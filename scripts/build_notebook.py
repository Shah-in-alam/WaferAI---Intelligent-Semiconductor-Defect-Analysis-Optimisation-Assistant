"""Generate notebooks/train_model.ipynb and notebooks/inference.ipynb.

Run once:  python scripts/build_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TRAIN_CELLS: list[tuple[str, str]] = [
    ("md", """# WaferAI — Train EfficientNetB0 on WM-811K

End-to-end training notebook. Produces `wafer_classifier.h5` that you drop into `models/` of your local WaferAI repo for real inference.

**Prerequisites**
1. Upload `LSWMD.pkl` (~2 GB) to the root of your Google Drive.
2. **Runtime → Change runtime type → T4 GPU** (free tier).
3. Run all cells. Total time: ~45–90 min on T4.

The preprocessing here mirrors `scripts/extract_samples.py` so the saved model expects the same input format the local Gradio app sends at inference time.
"""),

    ("code", """import tensorflow as tf
print("TF version:", tf.__version__)
gpus = tf.config.list_physical_devices("GPU")
print("GPU:", gpus)
assert gpus, "No GPU detected. Runtime → Change runtime type → T4 GPU."
"""),

    ("md", "## 1. Mount Google Drive"),

    ("code", """from google.colab import drive
drive.mount("/content/drive")

DATASET_PATH = "/content/drive/MyDrive/LSWMD.pkl"
"""),

    ("md", """## 2. Load LSWMD and filter to labelled rows

WM-811K has 811,457 wafer maps; only ~172k carry a defect label. Unlabelled rows are dropped for supervised training.
"""),

    ("code", """import numpy as np
import pandas as pd

print(f"Loading {DATASET_PATH} ...")
df = pd.read_pickle(DATASET_PATH)
print(f"Total rows: {len(df):,}")

def _label(val):
    if isinstance(val, (list, np.ndarray)):
        return val[0] if len(val) else None
    return val

df["label"] = df["failureType"].apply(_label)
df = df[df["label"].notna()].copy()
df["label"] = df["label"].astype(str)

CLASS_NAMES = [
    "Center", "Donut", "Edge-Loc", "Edge-Ring", "Loc",
    "Random", "Scratch", "Near-full", "none",
]
df = df[df["label"].isin(CLASS_NAMES)].reset_index(drop=True)

print(f"Labelled rows: {len(df):,}")
print(df["label"].value_counts())
"""),

    ("md", """## 3. Preprocess wafer maps to 96×96×3

WM-811K wafer codes: `0` = outside wafer, `1` = good die, `2` = defect. We render each map to the same RGB palette `scripts/extract_samples.py` uses, so the model trained here expects the exact format the local Gradio app produces.
"""),

    ("code", """from PIL import Image

IMG_SIZE = 96

def wafer_to_rgb(wafer_map):
    h, w = wafer_map.shape
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[wafer_map == 1] = (90, 90, 110)
    img[wafer_map == 2] = (230, 60, 60)
    pil = Image.fromarray(img).resize((IMG_SIZE, IMG_SIZE), Image.NEAREST)
    return np.asarray(pil, dtype=np.uint8)

print("Rendering wafers (~5 min for 172k) ...")
X = np.empty((len(df), IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
y_labels = np.empty(len(df), dtype=np.int64)
label_to_idx = {name: i for i, name in enumerate(CLASS_NAMES)}

for i, row in enumerate(df.itertuples(index=False)):
    X[i] = wafer_to_rgb(row.waferMap)
    y_labels[i] = label_to_idx[row.label]
    if (i + 1) % 20000 == 0:
        print(f"  {i+1:,}/{len(df):,}")

print("X:", X.shape, X.dtype, "  y:", y_labels.shape)
"""),

    ("md", "## 4. Stratified 70/15/15 train/val/test split"),

    ("code", """from sklearn.model_selection import train_test_split

X_train, X_tmp, y_train, y_tmp = train_test_split(
    X, y_labels, test_size=0.30, stratify=y_labels, random_state=42
)
X_val, X_test, y_val, y_test = train_test_split(
    X_tmp, y_tmp, test_size=0.50, stratify=y_tmp, random_state=42
)
del X, X_tmp, y_labels, y_tmp

print(f"Train: {len(X_train):,}  Val: {len(X_val):,}  Test: {len(X_test):,}")
"""),

    ("md", """## 5. Build EfficientNetB0 (transfer learning)

ImageNet-pretrained backbone (frozen) → GlobalAveragePooling → Dense(256) → Dropout → Dense(9, softmax). The `Rescaling` layer normalises uint8 inputs inside the model.
"""),

    ("code", """from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras import layers, Model

def build_model(num_classes=9):
    inputs = layers.Input(shape=(IMG_SIZE, IMG_SIZE, 3), dtype="uint8")
    x = layers.Rescaling(1.0 / 255.0)(inputs)
    base = EfficientNetB0(
        include_top=False, weights="imagenet",
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
    )
    base.trainable = False
    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)
    return Model(inputs, outputs), base

model, base_model = build_model(len(CLASS_NAMES))
model.summary()
"""),

    ("md", """## 6. Train with class weights

WM-811K is extremely imbalanced (~78% are `none`). Class weights normalise the loss so minority classes aren't drowned out.
"""),

    ("code", """from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

class_weights_vals = compute_class_weight(
    "balanced",
    classes=np.arange(len(CLASS_NAMES)),
    y=y_train,
)
class_weight = {i: float(w) for i, w in enumerate(class_weights_vals)}
print("Class weights:", class_weight)

model.compile(
    optimizer=tf.keras.optimizers.Adam(1e-3),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

callbacks = [
    EarlyStopping(monitor="val_accuracy", patience=3, restore_best_weights=True),
    ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2, min_lr=1e-6),
]

history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    batch_size=128,
    epochs=10,
    class_weight=class_weight,
    callbacks=callbacks,
)
"""),

    ("md", """## 7. Fine-tune (recommended)

Unfreeze the last ~30 layers of the backbone, drop the LR to 1e-5, train 5 more epochs. Typically adds 1–3% absolute accuracy.
"""),

    ("code", """base_model.trainable = True
for layer in base_model.layers[:-30]:
    layer.trainable = False

model.compile(
    optimizer=tf.keras.optimizers.Adam(1e-5),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

history_ft = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    batch_size=64,
    epochs=5,
    class_weight=class_weight,
    callbacks=callbacks,
)
"""),

    ("md", "## 8. Evaluate on the held-out test set"),

    ("code", """from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
print(f"\\nTest accuracy: {test_acc*100:.2f}%   Test loss: {test_loss:.4f}\\n")

y_pred = model.predict(X_test, batch_size=128, verbose=0).argmax(axis=1)
print(classification_report(y_test, y_pred, target_names=CLASS_NAMES, digits=3))

cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(9, 7))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES)
plt.xlabel("Predicted"); plt.ylabel("True"); plt.title("Confusion Matrix")
plt.tight_layout()
plt.savefig("confusion_matrix.png", dpi=120)
plt.show()
"""),

    ("md", """## 9. Save and download

The saved file goes into `models/wafer_classifier.h5` of your local WaferAI repo. Set `MODEL_PATH=models/wafer_classifier.h5` in `.env` (already the default) and the app will load it on next launch.
"""),

    ("code", """model.save("wafer_classifier.h5")
print("Saved.")

from google.colab import files
files.download("wafer_classifier.h5")
files.download("confusion_matrix.png")
"""),
]


INFER_CELLS: list[tuple[str, str]] = [
    ("md", """# WaferAI — Inference on Colab

Loads your trained `wafer_classifier.h5` and runs the full inference pipeline (preprocess → predict → Grad-CAM → confidence chart) on Colab. Use this if your local Python is 3.13 (no TensorFlow wheel) and you want to test the trained model without setting up a 3.11 venv.

**Prerequisites**
1. Run `train_model.ipynb` first and save `wafer_classifier.h5` to your Google Drive root.
2. Optional: T4 GPU (not required — inference works on CPU in <1 s).
3. Run all cells. Upload an image when prompted.
"""),

    ("md", "## 1. Mount Drive and load the model"),

    ("code", """from google.colab import drive
drive.mount("/content/drive")

MODEL_PATH = "/content/drive/MyDrive/wafer_classifier.h5"
"""),

    ("code", """import tensorflow as tf
print("TF version:", tf.__version__)

model = tf.keras.models.load_model(MODEL_PATH)
print("Loaded.")
model.summary()
"""),

    ("md", """## 2. Upload a wafer-map image

Click **Choose Files** and pick a PNG/JPG. You can also use one of the sample images from `data/sample_wafers/` in the repo.
"""),

    ("code", """from google.colab import files
import io
from PIL import Image
import numpy as np

uploaded = files.upload()
filename = next(iter(uploaded))
original = Image.open(io.BytesIO(uploaded[filename])).convert("RGB")
print(f"Loaded {filename}, size {original.size}")
original
"""),

    ("md", "## 3. Preprocess and predict"),

    ("code", """IMG_SIZE = 96
CLASS_NAMES = [
    "Center", "Donut", "Edge-Loc", "Edge-Ring", "Loc",
    "Random", "Scratch", "Near-full", "none",
]

resized = original.resize((IMG_SIZE, IMG_SIZE), Image.LANCZOS)
arr = np.asarray(resized, dtype=np.uint8)
batch = np.expand_dims(arr, 0)

probs = model.predict(batch, verbose=0)[0]
top_idx = int(np.argmax(probs))
print(f"Prediction: {CLASS_NAMES[top_idx]}  ({probs[top_idx]*100:.1f}%)")
print()
for i in np.argsort(probs)[::-1]:
    print(f"  {CLASS_NAMES[i]:<10}  {probs[i]*100:5.1f}%")
"""),

    ("md", """## 4. Grad-CAM

Compute the gradient of the predicted class with respect to the last convolutional layer of EfficientNetB0, then weight the feature maps to get a class-discriminative heatmap.
"""),

    ("code", """import cv2

# The model wraps EfficientNetB0 as a single Layer. Pull the inner base and
# pick its last conv layer ('top_conv').
base = next(l for l in model.layers if isinstance(l, tf.keras.Model))
LAST_CONV = "top_conv"
print("Grad-CAM target layer:", LAST_CONV, "→", base.get_layer(LAST_CONV).output.shape)

# Strategy: get conv activations and prediction in two forward passes, then
# attribute via gradients of the predicted class wrt the conv tensor. Falls
# back to channel-mean activation if the gradient is disconnected (which can
# happen with deeply nested Keras models).
batch_f = tf.constant(batch, dtype=tf.float32)
conv_extractor = tf.keras.Model(base.input, base.get_layer(LAST_CONV).output)

with tf.GradientTape() as tape:
    rescaled = batch_f / 255.0
    tape.watch(rescaled)
    conv_out = conv_extractor(rescaled, training=False)
    tape.watch(conv_out)
    preds = model(batch_f, training=False)
    target = preds[:, top_idx]

grads = tape.gradient(target, conv_out)
conv_arr = conv_out[0].numpy()
if grads is None:
    print("(Gradient disconnected — using channel-mean activations as the heatmap.)")
    heat = conv_arr.mean(axis=-1)
else:
    weights = tf.reduce_mean(grads, axis=(0, 1, 2)).numpy()
    heat = (conv_arr * weights).sum(axis=-1)

heat = np.maximum(heat, 0)
heat = heat / max(heat.max(), 1e-6)

orig_arr = np.array(original)
heat_resized = cv2.resize(heat, (orig_arr.shape[1], orig_arr.shape[0]))
heat_8u = np.uint8(255 * heat_resized)
colour = cv2.applyColorMap(heat_8u, cv2.COLORMAP_JET)
colour = cv2.cvtColor(colour, cv2.COLOR_BGR2RGB)
overlay = cv2.addWeighted(orig_arr, 0.55, colour, 0.45, 0)
Image.fromarray(overlay)
"""),

    ("md", "## 5. Confidence chart"),

    ("code", """import matplotlib.pyplot as plt

order = np.argsort(probs)[::-1]
labels = [CLASS_NAMES[i] for i in order]
values = [probs[i] * 100 for i in order]

plt.figure(figsize=(8, 4.5))
bars = plt.barh(labels, values, color="#3F8EFC")
bars[0].set_color("#E8553F")
plt.gca().invert_yaxis()
plt.xlabel("Confidence (%)")
plt.xlim(0, 100)
plt.grid(axis="x", linestyle=":", alpha=0.4)
for bar, v in zip(bars, values):
    plt.text(min(v + 1.5, 95), bar.get_y() + bar.get_height() / 2, f"{v:.1f}%", va="center")
plt.tight_layout()
plt.show()
"""),
]


def _to_lines(text: str) -> list[str]:
    lines = text.split("\n")
    return [ln + "\n" for ln in lines[:-1]] + ([lines[-1]] if lines[-1] else [])


def _build(cells_def: list[tuple[str, str]], out_path: Path, gpu: bool) -> None:
    cells = []
    for kind, source in cells_def:
        if kind == "md":
            cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": _to_lines(source),
            })
        else:
            cells.append({
                "cell_type": "code",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": _to_lines(source),
            })

    metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
        "colab": {"provenance": []},
    }
    if gpu:
        metadata["colab"]["gpuType"] = "T4"
        metadata["accelerator"] = "GPU"

    nb = {"cells": cells, "metadata": metadata, "nbformat": 4, "nbformat_minor": 5}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(nb, indent=1), encoding="utf-8")
    print(f"Wrote {out_path.relative_to(ROOT)}  ({out_path.stat().st_size:,} bytes, {len(cells)} cells)")


def main() -> None:
    _build(TRAIN_CELLS, ROOT / "notebooks" / "train_model.ipynb", gpu=True)
    _build(INFER_CELLS, ROOT / "notebooks" / "inference.ipynb", gpu=False)


if __name__ == "__main__":
    main()
