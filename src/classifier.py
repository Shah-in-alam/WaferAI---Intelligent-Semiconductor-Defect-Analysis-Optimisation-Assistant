from __future__ import annotations

import os
from pathlib import Path

import cv2
import numpy as np

from .preprocessor import CLASS_NAMES
from .utils import get_logger

logger = get_logger(__name__)


class WaferClassifier:
    """Wafer defect classifier.

    Loads a trained Keras model if `model_path` points to a real .h5/.keras file
    AND TensorFlow is importable. Otherwise falls back to a heuristic that
    inspects pixel statistics — useful for the runnable demo before a model is
    available.
    """

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path
        self.model = self._try_load_model(model_path)
        self.using_stub = self.model is None

    def _try_load_model(self, model_path: str | None):
        if not model_path or not Path(model_path).exists():
            logger.info("No model file at %s — using heuristic stub.", model_path)
            return None
        try:
            import tensorflow as tf  # noqa: WPS433 — optional dep

            model = tf.keras.models.load_model(model_path)
            logger.info("Loaded TF model from %s", model_path)
            return model
        except Exception as exc:
            logger.warning("Could not load TF model (%s) — falling back to stub.", exc)
            return None

    def predict(self, image_tensor: np.ndarray) -> tuple[str, float]:
        probs = self._predict_proba(image_tensor)
        idx = int(np.argmax(probs))
        return CLASS_NAMES[idx], float(probs[idx]) * 100.0

    def predict_proba(self, image_tensor: np.ndarray) -> dict[str, float]:
        probs = self._predict_proba(image_tensor)
        return {name: float(p) * 100.0 for name, p in zip(CLASS_NAMES, probs)}

    def _predict_proba(self, image_tensor: np.ndarray) -> np.ndarray:
        if self.model is not None:
            return self.model.predict(image_tensor, verbose=0)[0]
        return self._heuristic(image_tensor[0])

    def generate_gradcam(self, image_tensor: np.ndarray) -> np.ndarray:
        """Heatmap of attended regions. For the stub: a smoothed intensity map."""
        img = image_tensor[0]
        gray = img.mean(axis=2).astype(np.float32)
        heat = cv2.GaussianBlur(gray, (0, 0), sigmaX=2.5)
        heat = (heat - heat.min()) / max(heat.max() - heat.min(), 1e-6)
        return heat

    def _heuristic(self, img: np.ndarray) -> np.ndarray:
        """Improved geometric heuristic across all 9 WM-811K classes.

        Pipeline:
          1. Detect defect pixels (red-dominant if image is a wafer render,
             else brightness percentile).
          2. Compute density, centroid offset, radial structure, linearity,
             and central-hole indicators.
          3. Decision tree with per-class confidence based on how strongly
             the geometric pattern matches.
        """
        h, w = img.shape[:2]
        total = h * w

        mask = self._defect_mask(img)
        n = int(mask.sum())
        density = n / total
        probs = np.zeros(len(CLASS_NAMES), dtype=np.float32)

        if n < 8 or density < 0.005:
            probs[CLASS_NAMES.index("None")] = 0.92
            return _spread(probs, "None")

        if density > 0.50:
            probs[CLASS_NAMES.index("Near-full")] = 0.90
            return _spread(probs, "Near-full")

        if density < 0.06:
            probs[CLASS_NAMES.index("None")] = 0.85
            return _spread(probs, "None")

        if density > 0.30:
            probs[CLASS_NAMES.index("Random")] = 0.75
            return _spread(probs, "Random")

        # ----- Geometric features over the defect mask -----
        ys, xs = np.where(mask)
        max_r = max(min(h, w) / 2, 1)
        radii = np.sqrt((xs - w / 2) ** 2 + (ys - h / 2) ** 2) / max_r

        # Radial band fractions: where on the wafer the defects sit.
        f_in = float((radii < 0.30).sum() / n)
        f_md = float(((radii >= 0.30) & (radii < 0.65)).sum() / n)
        f_ot = float((radii >= 0.65).sum() / n)

        # Very-central density: ~empty for Edge-Ring / Donut, full for Center.
        cb = max(h // 20, 1)
        cbox = mask[h // 2 - cb : h // 2 + cb, w // 2 - cb : w // 2 + cb]
        cbx = float(cbox.mean()) if cbox.size else 0.0

        # Peak angular-bin fraction: high (>0.35) when a tight cluster sits
        # in one direction (Loc), low when defects spread around (Edge-Ring).
        angles = np.arctan2(ys - h / 2, xs - w / 2)
        bins, _ = np.histogram(angles, bins=8, range=(-np.pi, np.pi))
        mxbn = float(bins.max() / max(bins.sum(), 1))

        if f_in > 0.20:
            primary = "Center"
            conf = 0.80 + 0.15 * min((f_in - 0.20) / 0.30, 1.0)
        elif f_md > 0.40:
            primary = "Donut"
            conf = 0.78 + 0.10 * min((f_md - 0.40) / 0.30, 1.0)
        elif f_ot > 0.70:
            if cbx < 0.05:
                primary = "Edge-Ring"
                conf = 0.84
            else:
                primary = "Edge-Loc"
                conf = 0.76
        elif density < 0.12:
            if mxbn > 0.35:
                primary = "Loc"
                conf = 0.72 + 0.15 * min((mxbn - 0.35) / 0.30, 1.0)
            else:
                primary = "Scratch"
                conf = 0.70 + 0.10 * self._linearity(xs, ys)
        else:
            primary = "Random"
            conf = 0.65

        probs[CLASS_NAMES.index(primary)] = min(conf, 0.96)
        return _spread(probs, primary)

    @staticmethod
    def _defect_mask(img: np.ndarray) -> np.ndarray:
        """Detect defect pixels.

        Tries red-channel dominance first (matches `scripts/extract_samples.py`
        rendering). Falls back to a robust brightness threshold so arbitrary
        uploaded images still produce a usable mask.
        """
        r, g, b = img[..., 0], img[..., 1], img[..., 2]
        red_dom = (r > 0.55) & (r > g + 0.15) & (r > b + 0.15)
        if red_dom.sum() > 8:
            return red_dom

        gray = img.mean(axis=2)
        if gray.std() < 0.02:
            return np.zeros_like(gray, dtype=bool)

        thresh = float(np.percentile(gray, 80))
        eps = 0.02
        mask = gray > (thresh + eps)
        if mask.sum() < 8:
            relaxed = gray > (thresh - eps)
            if relaxed.sum() < 0.5 * relaxed.size:
                mask = relaxed
        return mask

    @staticmethod
    def _linearity(xs: np.ndarray, ys: np.ndarray) -> float:
        """0-1 score: 0 = isotropic blob, 1 = perfectly straight line."""
        if len(xs) < 5:
            return 0.0
        coords = np.column_stack([xs, ys]).astype(np.float64)
        coords -= coords.mean(axis=0)
        cov = coords.T @ coords / len(coords)
        eigvals = np.linalg.eigvalsh(cov)
        total = float(eigvals.sum())
        if total < 1e-6:
            return 0.0
        # Larger eigenvalue's share of total variance — 0.5 isotropic, 1.0 line.
        ratio = float(eigvals[1]) / total
        return float(max(0.0, min(1.0, (ratio - 0.5) * 2.0)))


def _spread(probs: np.ndarray, primary: str) -> np.ndarray:
    remaining = 1.0 - probs.sum()
    others = [i for i, n in enumerate(CLASS_NAMES) if n != primary]
    for i in others:
        probs[i] = remaining / len(others)
    return probs / probs.sum()
