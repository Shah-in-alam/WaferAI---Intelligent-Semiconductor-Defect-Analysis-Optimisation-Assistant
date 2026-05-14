"""Extract a handful of real wafer maps from LSWMD.pkl as PNG samples.

LSWMD.pkl is a pandas DataFrame with columns:
    waferMap       — 2D numpy int array (0=outside, 1=good, 2=defect)
    failureType    — defect label (Center, Donut, Edge-Loc, Edge-Ring, Loc,
                     Random, Scratch, Near-full, none)  (some rows: [])
    trianTestLabel — train/test split  (some rows: [])

This script picks up to N examples per labelled defect class and writes them
to data/sample_wafers/<class>.png.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PKL = ROOT / "data" / "raw" / "LSWMD.pkl"
OUTPUT_DIR = ROOT / "data" / "sample_wafers"

# WM-811K's nine defect labels (we deliberately skip the "none" majority class
# for the sample gallery, except for one representative).
CLASS_NAMES = [
    "Center",
    "Donut",
    "Edge-Loc",
    "Edge-Ring",
    "Loc",
    "Random",
    "Scratch",
    "Near-full",
    "none",
]


def wafer_to_png(wafer_map: np.ndarray) -> Image.Image:
    """Render WM-811K wafer codes 0/1/2 into a 3-channel image.

    0 (outside wafer) -> black
    1 (good die)      -> mid-grey
    2 (defect die)    -> bright red
    """
    h, w = wafer_map.shape
    img = np.zeros((h, w, 3), dtype=np.uint8)
    good = wafer_map == 1
    bad = wafer_map == 2
    img[good] = (90, 90, 110)
    img[bad] = (230, 60, 60)
    return Image.fromarray(img).resize((256, 256), Image.Resampling.NEAREST)


def main(pkl_path: Path = DEFAULT_PKL, samples_per_class: int = 1) -> int:
    if not pkl_path.exists():
        print(f"Dataset not found at {pkl_path}", file=sys.stderr)
        return 1

    print(f"Loading {pkl_path} ... (this can take ~30s for a ~2GB file)")
    df = pd.read_pickle(pkl_path)
    print(f"Loaded {len(df):,} rows.")

    # Normalise failureType — some rows contain a list/array of strings,
    # some are scalar strings, some are empty lists for unlabelled rows.
    def _label(val):
        if isinstance(val, (list, np.ndarray)):
            return val[0] if len(val) else None
        return val

    df["_label"] = df["failureType"].apply(_label)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    written = 0

    for cls in CLASS_NAMES:
        matches = df[df["_label"] == cls]
        if matches.empty:
            print(f"  - {cls}: no samples found")
            continue

        for i in range(min(samples_per_class, len(matches))):
            wafer = matches.iloc[i]["waferMap"]
            if not isinstance(wafer, np.ndarray) or wafer.size == 0:
                continue
            img = wafer_to_png(wafer)
            safe = cls.lower().replace("-", "_")
            suffix = f"_{i + 1}" if samples_per_class > 1 else ""
            out_path = OUTPUT_DIR / f"{safe}{suffix}.png"
            img.save(out_path)
            print(f"  - wrote {out_path.relative_to(ROOT)}")
            written += 1

    print(f"\nDone. Wrote {written} sample images to {OUTPUT_DIR.relative_to(ROOT)}.")
    return 0


if __name__ == "__main__":
    pkl = Path(os.getenv("DATASET_PATH", DEFAULT_PKL))
    n = int(os.getenv("SAMPLES_PER_CLASS", "1"))
    raise SystemExit(main(pkl, n))
