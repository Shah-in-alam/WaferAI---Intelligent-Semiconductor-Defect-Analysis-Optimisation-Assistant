import numpy as np
from PIL import Image

from src.preprocessor import IMG_SIZE, WaferPreprocessor


def _wafer(pattern: str = "center") -> Image.Image:
    arr = np.zeros((100, 100), dtype=np.uint8)
    if pattern == "center":
        arr[40:60, 40:60] = 255
    elif pattern == "edge":
        arr[:8, :] = 255
    return Image.fromarray(arr)


def test_preprocess_returns_correct_shape():
    pp = WaferPreprocessor()
    tensor = pp.preprocess_for_model(_wafer())
    assert tensor.shape == (1, IMG_SIZE, IMG_SIZE, 3)
    assert 0.0 <= tensor.min() and tensor.max() <= 1.0


def test_metadata_detects_centre_vs_edge():
    pp = WaferPreprocessor()
    assert pp.extract_metadata(_wafer("center"))["location"] == "Centre"
    assert pp.extract_metadata(_wafer("edge"))["location"] == "Edge"
