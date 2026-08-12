"""
Transit detection using two complementary models:

1. An LSTM sequence classifier: predicts P(transit present) over a windowed
   light curve.
2. An LSTM Autoencoder: trained to reconstruct *normal* (transit-free) flux
   sequences; a high reconstruction error flags anomalous dips (candidate
   transits or transients) even for transit shapes never seen in training.

Both operate on fixed-length, normalized flux windows.
"""
import os
import numpy as np

from config import Config

WINDOW = 200
_lstm_clf = None
_autoencoder = None


def _windowize(flux, window=WINDOW):
    flux = np.array(flux, dtype=np.float32)
    if len(flux) < window:
        flux = np.pad(flux, (0, window - len(flux)), mode="edge")
    else:
        # take evenly spaced samples to fit the window
        idx = np.linspace(0, len(flux) - 1, window).astype(int)
        flux = flux[idx]
    flux = (flux - flux.mean()) / (flux.std() + 1e-8)
    return flux


def _build_lstm_classifier():
    import tensorflow as tf
    from tensorflow.keras import layers, models
    model = models.Sequential([
        layers.Input(shape=(WINDOW, 1)),
        layers.LSTM(32, return_sequences=True),
        layers.LSTM(16),
        layers.Dense(16, activation="relu"),
        layers.Dense(1, activation="sigmoid"),
    ])
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    return model


def _build_autoencoder():
    import tensorflow as tf
    from tensorflow.keras import layers, models
    model = models.Sequential([
        layers.Input(shape=(WINDOW, 1)),
        layers.LSTM(32, return_sequences=False),
        layers.RepeatVector(WINDOW),
        layers.LSTM(32, return_sequences=True),
        layers.TimeDistributed(layers.Dense(1)),
    ])
    model.compile(optimizer="adam", loss="mse")
    return model


def load_models():
    global _lstm_clf, _autoencoder
    import tensorflow as tf
    if _lstm_clf is None:
        _lstm_clf = (tf.keras.models.load_model(Config.LSTM_AE_MODEL_PATH.replace("_ae", "_clf"))
                     if os.path.exists(Config.LSTM_AE_MODEL_PATH.replace("_ae", "_clf"))
                     else _build_lstm_classifier())
    if _autoencoder is None:
        _autoencoder = (tf.keras.models.load_model(Config.LSTM_AE_MODEL_PATH)
                         if os.path.exists(Config.LSTM_AE_MODEL_PATH)
                         else _build_autoencoder())
    return _lstm_clf, _autoencoder


def detect_transit(flux, anomaly_threshold=1.5):
    clf, ae = load_models()
    window = _windowize(flux).reshape(1, WINDOW, 1)

    transit_prob = float(clf.predict(window, verbose=0)[0][0])

    reconstruction = ae.predict(window, verbose=0)
    recon_error = float(np.mean((reconstruction - window) ** 2))

    return {
        "transit_probability": transit_prob,
        "is_transit_lstm": transit_prob > 0.5,
        "reconstruction_error": recon_error,
        "is_anomaly_autoencoder": recon_error > anomaly_threshold,
        "combined_detection": (transit_prob > 0.5) or (recon_error > anomaly_threshold),
    }
