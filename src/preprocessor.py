import numpy as np
from PIL import Image

CLASS_NAMES = [
    "Center",
    "Donut",
    "Edge-Loc",
    "Edge-Ring",
    "Loc",
    "Random",
    "Scratch",
    "Near-full",
    "None",
]
IMG_SIZE = 96


class WaferPreprocessor:
    def validate_image(self, image: Image.Image) -> bool:
        return image.size[0] > 0 and image.size[1] > 0

    def preprocess_for_model(self, image: Image.Image) -> np.ndarray:
        image = image.convert("RGB")
        image = image.resize((IMG_SIZE, IMG_SIZE), Image.Resampling.LANCZOS)
        arr = np.array(image, dtype=np.float32) / 255.0
        return np.expand_dims(arr, axis=0)

    def extract_metadata(self, image: Image.Image) -> dict:
        gray = np.array(image.convert("L"))
        h, w = gray.shape

        threshold = np.percentile(gray, 70)
        defect_mask = gray > threshold
        defect_density = 100.0 * defect_mask.sum() / (h * w)

        ys, xs = np.where(defect_mask)
        if len(xs) == 0:
            location = "None"
        else:
            cx, cy = xs.mean(), ys.mean()
            dx = abs(cx - w / 2) / (w / 2)
            dy = abs(cy - h / 2) / (h / 2)
            location = "Edge" if max(dx, dy) > 0.55 else "Centre"

        return {
            "width": int(w),
            "height": int(h),
            "defect_density": round(float(defect_density), 2),
            "location": location,
        }
