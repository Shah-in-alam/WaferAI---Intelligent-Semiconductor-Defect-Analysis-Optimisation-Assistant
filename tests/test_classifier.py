import numpy as np
from PIL import Image

from src.classifier import WaferClassifier
from src.preprocessor import CLASS_NAMES, IMG_SIZE, WaferPreprocessor

pp = WaferPreprocessor()


def _tensor(img: np.ndarray) -> np.ndarray:
    return pp.preprocess_for_model(Image.fromarray(img))


def test_predict_returns_known_class_and_probability():
    img = np.zeros((100, 100), dtype=np.uint8)
    img[40:60, 40:60] = 255
    clf = WaferClassifier()
    name, conf = clf.predict(_tensor(img))
    assert name in CLASS_NAMES
    assert 0.0 <= conf <= 100.0


def test_predict_proba_sums_to_100():
    clf = WaferClassifier()
    blank = np.zeros((50, 50), dtype=np.uint8)
    probs = clf.predict_proba(_tensor(blank))
    assert set(probs) == set(CLASS_NAMES)
    assert abs(sum(probs.values()) - 100.0) < 0.5


def test_blank_wafer_classified_as_none():
    clf = WaferClassifier()
    blank = np.zeros((50, 50), dtype=np.uint8)
    name, _ = clf.predict(_tensor(blank))
    assert name == "None"


def test_gradcam_returns_normalised_2d_array():
    clf = WaferClassifier()
    arr = np.zeros((50, 50), dtype=np.uint8)
    arr[20:30, 20:30] = 200
    heat = clf.generate_gradcam(_tensor(arr))
    assert heat.shape == (IMG_SIZE, IMG_SIZE)
    assert 0.0 <= heat.min() and heat.max() <= 1.0
