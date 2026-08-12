"""
CNN star classifier: classifies a star into one of 6 spectral types
(O, B, A, F, G, K) from a small feature vector derived from photometry
(color index, magnitude, folded light-curve shape).

Represented as a 1D-CNN over a fixed-length "spectral-photometric fingerprint"
vector, since we don't have raw spectra — this is a common, honest approach
when working from photometric survey data (Hipparcos/Gaia/TESS) rather than
spectrographs.
"""
import os
import numpy as np

from config import Config

CLASSES = Config.STAR_CLASSES  # ["O","B","A","F","G","K"]

_model = None


def _build_model(input_len=32):
    import tensorflow as tf
    from tensorflow.keras import layers, models

    model = models.Sequential([
        layers.Input(shape=(input_len, 1)),
        layers.Conv1D(16, 3, activation="relu", padding="same"),
        layers.MaxPooling1D(2),
        layers.Conv1D(32, 3, activation="relu", padding="same"),
        layers.MaxPooling1D(2),
        layers.Flatten(),
        layers.Dense(64, activation="relu"),
        layers.Dropout(0.3),
        layers.Dense(len(CLASSES), activation="softmax"),
    ])
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return model


def featurize(color_index, magnitude, light_curve_flux=None, length=32):
    """Build a fixed-length feature vector from available photometry.
    If a light curve is provided, use its folded/binned shape; otherwise
    pad with color/magnitude-derived stats."""
    vec = np.zeros(length, dtype=np.float32)
    vec[0] = color_index if color_index is not None else 0.6
    vec[1] = magnitude if magnitude is not None else 5.0
    if light_curve_flux is not None and len(light_curve_flux) > 0:
        flux = np.array(light_curve_flux, dtype=np.float32)
        bins = np.array_split(flux, length - 2)
        binned = [b.mean() for b in bins]
        vec[2:2 + len(binned)] = binned[:length - 2]
    return vec


def load_model():
    global _model
    if _model is not None:
        return _model
    path = Config.CNN_MODEL_PATH
    if os.path.exists(path):
        import tensorflow as tf
        _model = tf.keras.models.load_model(path)
    else:
        _model = _build_model()  # untrained fallback; see scripts/train_cnn.py
    return _model


def classify_star(color_index, magnitude, light_curve_flux=None):
    model = load_model()
    features = featurize(color_index, magnitude, light_curve_flux).reshape(1, -1, 1)
    probs = model.predict(features, verbose=0)[0]
    idx = int(np.argmax(probs))
    return {
        "predicted_class": CLASSES[idx],
        "confidence": float(probs[idx]),
        "probabilities": {c: float(p) for c, p in zip(CLASSES, probs)},
    }
