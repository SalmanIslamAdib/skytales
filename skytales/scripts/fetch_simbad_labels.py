"""
Enriches the cached Hipparcos star catalog with REAL SIMBAD spectral types,
replacing the B-V color-index proxy label wherever a SIMBAD match exists.

Run this before scripts/train_cnn.py to train on real labels instead of the
color-index approximation.

This queries SIMBAD in batches (network calls) — for 3000 stars, expect a
few minutes depending on SIMBAD's response time.

Usage:
    python scripts/fetch_simbad_labels.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from data.star_catalog import fetch_star_catalog, CACHE_PATH
from data.simbad_labels import fetch_simbad_spectral_types


def main():
    stars = fetch_star_catalog(n_stars=3000, use_cache=True)
    hip_ids = [int(s["id"].replace("HIP", "")) for s in stars if s["id"].startswith("HIP")]

    if not hip_ids:
        print("No Hipparcos-sourced stars in the cache (catalog may be the synthetic "
              "fallback). Run this on a machine with network access to Vizier first.")
        return

    print(f"Querying SIMBAD for {len(hip_ids)} stars — this can take a few minutes...")
    sptype_map = fetch_simbad_spectral_types(hip_ids)

    matched = 0
    for s in stars:
        if not s["id"].startswith("HIP"):
            continue
        hip = int(s["id"].replace("HIP", ""))
        real_class = sptype_map.get(hip)
        s["real_spectral_class"] = real_class
        if real_class:
            matched += 1
            s["spectral_class"] = real_class  # prefer real label over color-index proxy
            s["label_source"] = "simbad"
        else:
            s["label_source"] = "color_index_proxy"

    print(f"Matched {matched}/{len(hip_ids)} stars to a real SIMBAD spectral type "
          f"({len(hip_ids) - matched} fall back to the color-index proxy).")

    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(stars, f)
    print(f"Updated catalog cache written to {CACHE_PATH}")


if __name__ == "__main__":
    main()
