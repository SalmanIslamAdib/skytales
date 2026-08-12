"""
Fetches a real, bright-star catalog (Hipparcos New Reduction) via astroquery/Vizier
for the 3D sky map. Falls back to a bundled synthetic catalog if the network /
astroquery is unavailable, so the app still runs offline.

Coordinates are converted from RA/Dec/parallax into 3D Cartesian (x, y, z) in
parsecs, centered on the Sun, so the frontend can plot a real 3D star field.
"""
import os
import json
import numpy as np
import pandas as pd

CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "star_catalog_cache.json")


def _radec_to_xyz(ra_deg, dec_deg, dist_pc):
    ra = np.radians(ra_deg)
    dec = np.radians(dec_deg)
    x = dist_pc * np.cos(dec) * np.cos(ra)
    y = dist_pc * np.cos(dec) * np.sin(ra)
    z = dist_pc * np.sin(dec)
    return x, y, z


def _spectral_bucket(bt_vt_color):
    """Approximate spectral classification from B-V color index, using
    standard OBAFGK temperature-boundary cutoffs. This is a PROXY label,
    used only as a fallback when no real SIMBAD spectral type is available
    (see scripts/fetch_simbad_labels.py for real labels). Stars cooler than
    K (i.e. true M dwarfs) are folded into the K bucket to keep the 6-class
    scheme (O,B,A,F,G,K) — M dwarfs are rare in this bright-star sample
    anyway since Hipparcos is magnitude-limited."""
    if bt_vt_color is None or np.isnan(bt_vt_color):
        return "G"
    if bt_vt_color < -0.30:
        return "O"
    elif bt_vt_color < -0.02:
        return "B"
    elif bt_vt_color < 0.30:
        return "A"
    elif bt_vt_color < 0.58:
        return "F"
    elif bt_vt_color < 0.81:
        return "G"
    else:
        return "K"  # includes true K and any cooler (M-type) stars


def _find_column(colnames, candidates):
    """VizieR sometimes names the same column differently across catalog
    versions/astroquery versions (e.g. RAICRS vs RA_ICRS vs RArad). Try each
    known candidate name, case-insensitively, instead of assuming one."""
    lower_map = {c.lower(): c for c in colnames}
    for candidate in candidates:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]
    return None


def fetch_star_catalog(n_stars=3000, use_cache=True):
    """Returns a list of dicts: id, name, ra, dec, distance_pc, x, y, z,
    magnitude, color_index, spectral_class."""
    if use_cache and os.path.exists(CACHE_PATH):
        with open(CACHE_PATH) as f:
            cached = json.load(f)
        if len(cached) >= min(n_stars, len(cached)):
            return cached[:n_stars]

    try:
        from astroquery.vizier import Vizier
        Vizier.ROW_LIMIT = n_stars
        Vizier.columns = ["**"]  # request all available columns; we'll find the ones we need below
        catalogs = Vizier.get_catalogs("I/311/hip2")
        table = catalogs[0]
        df = table.to_pandas()

        ra_col = _find_column(df.columns, ["RAICRS", "RA_ICRS", "RArad", "RAJ2000", "_RAJ2000"])
        de_col = _find_column(df.columns, ["DEICRS", "DE_ICRS", "DErad", "DEJ2000", "_DEJ2000"])
        plx_col = _find_column(df.columns, ["Plx", "plx"])
        hip_col = _find_column(df.columns, ["HIP", "hip"])
        mag_col = _find_column(df.columns, ["Hpmag", "HPmag", "Vmag"])
        bv_col = _find_column(df.columns, ["B-V", "BV", "B_V"])

        missing = [name for name, col in [("RA", ra_col), ("Dec", de_col), ("parallax", plx_col),
                                           ("HIP id", hip_col), ("magnitude", mag_col)] if col is None]
        if missing:
            raise ValueError(f"Vizier returned unexpected columns; couldn't find: {missing}. "
                              f"Available columns were: {list(df.columns)}")

        df = df[df[plx_col] > 0]  # need positive parallax for distance
        df["dist_pc"] = 1000.0 / df[plx_col]
        df = df.sort_values(mag_col).head(n_stars)  # brightest first

        stars = []
        for i, row in df.iterrows():
            x, y, z = _radec_to_xyz(row[ra_col], row[de_col], row["dist_pc"])
            bv_val = float(row[bv_col]) if bv_col and not pd.isna(row[bv_col]) else None
            stars.append({
                "id": f"HIP{int(row[hip_col])}",
                "name": f"HIP {int(row[hip_col])}",
                "ra": float(row[ra_col]),
                "dec": float(row[de_col]),
                "distance_pc": round(float(row["dist_pc"]), 2),
                "x": round(float(x), 3),
                "y": round(float(y), 3),
                "z": round(float(z), 3),
                "magnitude": round(float(row[mag_col]), 2),
                "color_index": round(bv_val, 3) if bv_val is not None else None,
                "spectral_class": _spectral_bucket(bv_val),
            })

        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w") as f:
            json.dump(stars, f)
        return stars

    except Exception as e:
        print(f"[star_catalog] Live fetch failed ({e}); generating synthetic fallback catalog.")
        return _synthetic_catalog(n_stars)


def _synthetic_catalog(n_stars):
    rng = np.random.default_rng(42)
    stars = []
    for i in range(n_stars):
        ra = rng.uniform(0, 360)
        dec = np.degrees(np.arcsin(rng.uniform(-1, 1)))
        dist = rng.uniform(1, 500)
        x, y, z = _radec_to_xyz(ra, dec, dist)
        bv = rng.normal(0.6, 0.5)
        stars.append({
            "id": f"SYN{i}",
            "name": f"Synthetic Star {i}",
            "ra": round(ra, 4),
            "dec": round(dec, 4),
            "distance_pc": round(dist, 2),
            "x": round(float(x), 3),
            "y": round(float(y), 3),
            "z": round(float(z), 3),
            "magnitude": round(rng.uniform(-1, 8), 2),
            "color_index": round(bv, 3),
            "spectral_class": _spectral_bucket(bv),
        })
    return stars