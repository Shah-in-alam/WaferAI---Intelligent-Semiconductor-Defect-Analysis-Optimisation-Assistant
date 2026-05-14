from __future__ import annotations

from io import BytesIO

import cv2
import matplotlib
import numpy as np
from PIL import Image

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def overlay_gradcam(
    original: Image.Image,
    heatmap: np.ndarray,
    alpha: float = 0.45,
) -> Image.Image:
    """Overlay a heatmap on the original image, returning a PIL Image."""
    img = np.array(original.convert("RGB"))

    heat_resized = cv2.resize(heatmap, (img.shape[1], img.shape[0]))
    heat_8u = np.uint8(255 * np.clip(heat_resized, 0, 1))
    colour = cv2.applyColorMap(heat_8u, cv2.COLORMAP_JET)
    colour = cv2.cvtColor(colour, cv2.COLOR_BGR2RGB)

    blended = cv2.addWeighted(img, 1 - alpha, colour, alpha, 0)
    return Image.fromarray(blended)


def confidence_chart(probs: dict[str, float]) -> Image.Image:
    """Horizontal bar chart of class probabilities."""
    items = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
    labels, values = zip(*items)

    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=120)
    bars = ax.barh(labels, values, color="#3F8EFC")
    bars[0].set_color("#E8553F")

    ax.set_xlabel("Confidence (%)")
    ax.set_xlim(0, 100)
    ax.invert_yaxis()
    ax.grid(axis="x", linestyle=":", alpha=0.4)

    for bar, value in zip(bars, values):
        ax.text(
            min(value + 1.5, 95),
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}%",
            va="center",
            fontsize=9,
        )

    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).copy()
