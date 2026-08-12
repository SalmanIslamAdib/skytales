import os

class Config:
    # MAST / astroquery
    MAST_TIMEOUT = 60

    # 3D Sky Map
    N_STARS = 3000
    # Vizier catalog used for the sky map (Hipparcos - New Reduction)
    STAR_CATALOG = "I/311/hip2"

    # Star classification (6 spectral classes)
    STAR_CLASSES = ["O", "B", "A", "F", "G", "K"]  # extend with "M" if needed

    # Model paths
    MODEL_DIR = os.path.join(os.path.dirname(__file__), "ml", "saved_models")
    CNN_MODEL_PATH = os.path.join(MODEL_DIR, "star_cnn.h5")
    LSTM_AE_MODEL_PATH = os.path.join(MODEL_DIR, "transit_lstm_ae.h5")

    # Transient filter
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    USE_LLM_FILTER = bool(ANTHROPIC_API_KEY)

    # Flask
    DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"
    PORT = int(os.environ.get("PORT", 5000))
