"""
Trains the 6-class star CNN classifier.

Data source: the real Hipparcos catalog (fetched via backend/data/star_catalog.py),
using B-V color index as a bootstrap label (standard spectral-type boundaries).
This gives a real, if approximate, labeled dataset without needing a spectrograph.

Usage:
    python scripts/train_cnn.py
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from data.star_catalog import fetch_star_catalog
from ml.cnn_classifier import featurize, _build_model, CLASSES
from config import Config


def main():
    print("Loading star catalog (run scripts/fetch_simbad_labels.py first for real SIMBAD labels)...")
    stars = fetch_star_catalog(n_stars=5000, use_cache=True)
    print(f"Got {len(stars)} stars.")

    real_labels = sum(1 for s in stars if s.get("label_source") == "simbad")
    if real_labels:
        print(f"Label sources: {real_labels} real SIMBAD spectral types, "
              f"{len(stars) - real_labels} color-index proxy.")
    else:
        print("No SIMBAD labels found in cache — training entirely on the color-index "
              "proxy. Run scripts/fetch_simbad_labels.py first for real labels.")

    X, y = [], []
    for s in stars:
        if s["color_index"] is None or s["spectral_class"] not in CLASSES:
            continue
        X.append(featurize(s["color_index"], s["magnitude"]))
        y.append(CLASSES.index(s["spectral_class"]))

    X = np.array(X).reshape(-1, 32, 1)
    y = np.array(y)
    print(f"Training set: {X.shape[0]} samples across {len(CLASSES)} classes.")

    model = _build_model(input_len=32)
    model.fit(X, y, epochs=20, batch_size=32, validation_split=0.15, verbose=2)

    os.makedirs(Config.MODEL_DIR, exist_ok=True)
    model.save(Config.CNN_MODEL_PATH)
    print(f"Saved model to {Config.CNN_MODEL_PATH}")


if __name__ == "__main__":
    main()
