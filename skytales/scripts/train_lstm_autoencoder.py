"""
Trains:
  1. The LSTM transit classifier.
  2. The LSTM Autoencoder, trained on transit-free ("normal") sequences only,
     so it learns to reconstruct quiet stellar flux and flags anything else
     (transits, flares, transients, artifacts) as anomalous.

Data preference order:
  1. REAL MAST light curves labeled by confirmed-planet ephemerides — run
     `python scripts/fetch_real_transit_data.py` first to build this.
  2. Falls back to physically-realistic synthetic box-transit injections if
     no real dataset is cached, so the pipeline still runs end-to-end.

Usage:
    python scripts/train_lstm_autoencoder.py
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from data.mast_client import generate_synthetic_light_curve
from ml.transit_lstm import _windowize, _build_lstm_classifier, _build_autoencoder, WINDOW
from config import Config

REAL_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "real_transit_dataset.npz")


def build_synthetic_dataset(n=2000):
    X, y = [], []
    for i in range(n):
        has_transit = i % 2 == 0
        lc = generate_synthetic_light_curve(n_points=500, has_transit=has_transit, seed=i)
        X.append(_windowize(lc["flux"]))
        y.append(1 if has_transit else 0)
    return np.array(X).reshape(-1, WINDOW, 1), np.array(y)


def load_dataset():
    if os.path.exists(REAL_DATA_PATH):
        print(f"Loading REAL MAST-derived transit dataset from {REAL_DATA_PATH}")
        data = np.load(REAL_DATA_PATH, allow_pickle=True)
        return data["X"], data["y"], True
    print("No real dataset found at data/real_transit_dataset.npz.")
    print("Run `python scripts/fetch_real_transit_data.py` first for real MAST-derived data.")
    print("Falling back to synthetic box-transit injections for this run.")
    X, y = build_synthetic_dataset(2000)
    return X, y, False


def main():
    X, y, is_real = load_dataset()
    print(f"Dataset: {X.shape[0]} sequences ({int(y.sum())} transit-positive). "
          f"Source: {'real MAST data' if is_real else 'synthetic'}.")

    print("Training LSTM classifier...")
    clf = _build_lstm_classifier()
    clf.fit(X, y, epochs=10, batch_size=32, validation_split=0.15, verbose=2)

    print("Training LSTM autoencoder on transit-free sequences only...")
    X_normal = X[y == 0]
    ae = _build_autoencoder()
    ae.fit(X_normal, X_normal, epochs=15, batch_size=32, validation_split=0.15, verbose=2)

    os.makedirs(Config.MODEL_DIR, exist_ok=True)
    clf.save(Config.LSTM_AE_MODEL_PATH.replace("_ae", "_clf"))
    ae.save(Config.LSTM_AE_MODEL_PATH)
    print("Saved LSTM classifier and autoencoder.")
    if not is_real:
        print("\nNote: trained on synthetic data — the anomaly_threshold in "
              "ml/transit_lstm.py will likely need retuning once you train on real "
              "data, since real flux noise differs from synthetic Gaussian noise.")


if __name__ == "__main__":
    main()
