# SkyTales 🔭✨

A JWST-inspired sky simulation: a real 3D star map built from live MAST/Vizier
data, ML-based star classification and transit detection, and an LLM-assisted
transient filter — served by a Flask API and rendered in a Three.js + Plotly
frontend.

## Feature status

| Feature              | Status | Implementation                                      |
|-----------------------|--------|-----------------------------------------------------|
| 3D Sky Map            | ✅     | Three.js, 3,000 stars from Hipparcos (via Vizier)    |
| Star Classification   | ✅     | 1D-CNN, 6 spectral classes (O,B,A,F,G,K)             |
| Transit Detection     | ✅     | LSTM classifier + LSTM Autoencoder (anomaly score)   |
| Transient Filter      | ✅     | Rules engine + optional Claude LLM triage            |
| Light Curve Plot      | ✅     | Interactive Plotly, real MAST data via `lightkurve`  |
| API Health Check      | ✅     | `GET /api/health`                                    |
| Live Server Ready     | ✅     | Flask + `flask-cors`, CORS enabled                   |
| Sky View by Location  | ✅     | Enter/detect lat+lon → real visible stars & constellations |

## Project layout

```
skytales/
  backend/
    app.py                 # Flask entrypoint
    config.py
    data/
      star_catalog.py       # Hipparcos catalog fetch (Vizier) -> 3D coords
      mast_client.py         # MAST light curve search/fetch (lightkurve)
    ml/
      cnn_classifier.py      # 1D-CNN star classifier
      transit_lstm.py        # LSTM classifier + LSTM autoencoder
      transient_filter.py    # rules + optional Claude LLM triage
      saved_models/          # trained models land here (gitignored)
    routes/                  # Flask blueprints, one per feature
  frontend/
    index.html
    css/style.css
    js/api.js, starmap.js, lightcurve.js
  scripts/
    train_cnn.py
    train_lstm_autoencoder.py
  data/                      # cached catalogs
  requirements.txt
```

## Setup

```bash
cd skytales
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 1. Run the backend

```bash
cd backend
python app.py
```

Starts the Flask API at `http://localhost:5000`. Visit `/` for a list of
endpoints, or `/api/health` to check it's alive.

The **first** call to `/api/stars` will hit Vizier live to pull the
Hipparcos catalog and cache it locally to `data/star_catalog_cache.json` —
if you're offline or Vizier is unreachable, it transparently falls back to a
synthetic-but-realistic catalog so the app still runs.

### 2. Run the frontend

Any static server works — e.g. the VS Code "Live Server" extension on
`frontend/index.html`, or:

```bash
cd frontend
python -m http.server 8080
```

Then open `http://localhost:8080`.

### 3. (Optional) Train the ML models

Without training, the CNN/LSTM/Autoencoder routes still work — they run on
freshly-initialized (untrained) weights, so predictions are functional but
not meaningful. There are two ways to get real predictions:

**Quick path (synthetic-labeled, fast):**
```bash
python scripts/train_cnn.py                  # trains on B-V color-index proxy labels
python scripts/train_lstm_autoencoder.py      # trains on synthetic box-transit injections
```

**Real-data path (slower, more accurate — recommended):**
```bash
python scripts/fetch_simbad_labels.py         # cross-matches Hipparcos IDs -> real SIMBAD spectral types
python scripts/train_cnn.py                   # now trains on real labels wherever a match was found

python scripts/fetch_real_transit_data.py --n_targets 40   # real MAST light curves, labeled via confirmed-planet ephemerides
python scripts/train_lstm_autoencoder.py                    # auto-detects and prefers the real dataset if present
```

Both `fetch_*` scripts do real network calls (SIMBAD / NASA Exoplanet
Archive / MAST) and can take a few minutes — they cache their results to
`data/`, so you only need to run them once.

Models are saved to `backend/ml/saved_models/` and picked up automatically
by the API on next run.

### 4. (Optional) Enable the LLM transient triage

```bash
export ANTHROPIC_API_KEY=your_key_here   # Windows: set ANTHROPIC_API_KEY=...
```

Without a key, `/api/transient` still runs the rules engine and reports
`llm_used: false`.

## API reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Health check |
| `/api/stars?n=3000` | GET | 3D sky map star catalog |
| `/api/search?q=<name>&mission=TESS` | GET | Search MAST for a target |
| `/api/lightcurve/<target>?mission=TESS&synthetic=false` | GET | Fetch a light curve |
| `/api/classify` | POST | `{color_index, magnitude, flux?}` → spectral class |
| `/api/transit` | POST | `{flux: [...]}` → LSTM + autoencoder detection |
| `/api/transient` | POST | `{flux: [...], target_name}` → filtered/triaged result |
| `/api/sky_view?lat=<lat>&lon=<lon>` | GET | Real stars & constellations above the horizon for any location, right now |

## Notes on data honesty

- The 3D sky map uses **real** Hipparcos astrometry (RA/Dec/parallax → 3D
  Cartesian position), not simulated star placements.
- Star spectral classes are derived from **B-V color index** using standard
  boundaries — a reasonable proxy label since we don't have per-star
  spectrograph data in Hipparcos/Gaia photometry alone.
- Light curves come from real MAST observations via `lightkurve` when a
  valid target + mission is given; if the fetch fails (bad target name, no
  data, offline), the API transparently returns a clearly-labeled synthetic
  curve so the UI never breaks.
- ML models ship **untrained** by default (random weights). Two label
  qualities are available for training:
  - **CNN**: `scripts/fetch_simbad_labels.py` pulls real, catalog-assigned
    spectral types from SIMBAD; stars without a SIMBAD match fall back to
    the B-V color-index proxy (documented in `star_catalog.py`).
  - **LSTM/Autoencoder**: `scripts/fetch_real_transit_data.py` pulls real
    TESS light curves for confirmed transiting planets from the NASA
    Exoplanet Archive and labels in-transit windows using each planet's
    real ephemeris (period/epoch/duration) — real stellar noise and real
    transit shapes, not synthetic injections. If you skip this step,
    training falls back to synthetic box-transits automatically.
