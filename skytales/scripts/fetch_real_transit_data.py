"""
Builds a REAL training dataset for transit detection:

  1. Pulls confirmed transiting planets + ephemerides (period, duration,
     epoch) from the NASA Exoplanet Archive.
  2. Downloads each host star's real TESS light curve via `lightkurve`.
  3. Uses the confirmed ephemeris to label in-transit vs. out-of-transit
     time windows — real stellar noise and real transit shapes, not
     synthetic box injections.
  4. Slides a fixed-length window across each light curve and saves the
     resulting (window, label) pairs to data/real_transit_dataset.npz.

This does real network downloads per target, so it's slow (minutes) — run
it once, then reuse the cached .npz for training. Targets that fail to
download (no data, bad ID, timeout) are skipped, not fatal.

Usage:
    python scripts/fetch_real_transit_data.py --n_targets 40
"""
import os
import sys
import argparse
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from data.exoplanet_archive import fetch_confirmed_transiting_planets
from ml.transit_lstm import WINDOW, _windowize

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "real_transit_dataset.npz")


def label_in_transit(time, period, epoch, duration_hours):
    duration_days = duration_hours / 24.0
    phase = ((np.array(time) - epoch + period / 2) % period) - period / 2
    return np.abs(phase) < (duration_days / 2)


def build_windows(flux, in_transit_mask, window=WINDOW, stride=100, positive_frac_threshold=0.05):
    X, y = [], []
    flux = np.array(flux)
    for start in range(0, len(flux) - window, stride):
        end = start + window
        seg_flux = flux[start:end]
        seg_mask = in_transit_mask[start:end]
        if np.isnan(seg_flux).any():
            continue
        label = 1 if seg_mask.mean() > positive_frac_threshold else 0
        X.append(_windowize(seg_flux))
        y.append(label)
    return X, y


def main(n_targets=40):
    print("Fetching confirmed transiting planets from NASA Exoplanet Archive...")
    planets = fetch_confirmed_transiting_planets(limit=n_targets)
    print(f"Got {len(planets)} candidate targets.")
    if not planets:
        print("No targets returned — check network access to the Exoplanet Archive TAP service.")
        return

    import lightkurve as lk

    all_X, all_y, used_targets = [], [], []

    for p in planets:
        target = p["tic_id"] or p["hostname"]
        try:
            print(f"Downloading light curve for {target} ({p['planet_name']})...")
            search = lk.search_lightcurve(target, mission="TESS")
            if len(search) == 0:
                print("  no light curve found, skipping")
                continue

            lc = search[0].download().remove_nans().flatten()
            time = lc.time.value
            flux = lc.flux.value

            mask = label_in_transit(time, p["period_days"], p["epoch_bjd"], p["duration_hours"])
            X, y = build_windows(flux, mask)
            if not X:
                print("  no usable windows, skipping")
                continue

            all_X.extend(X)
            all_y.extend(y)
            used_targets.append(target)
            print(f"  added {len(X)} windows ({sum(y)} transit-positive)")
        except Exception as e:
            print(f"  failed: {e}")
            continue

    if not all_X:
        print("No real data collected. Check network access / target availability and retry.")
        return

    X = np.array(all_X).reshape(-1, WINDOW, 1)
    y = np.array(all_y)

    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    np.savez(DATA_PATH, X=X, y=y, targets=np.array(used_targets, dtype=object))
    print(f"\nSaved {X.shape[0]} real windows ({int(y.sum())} transit-positive) "
          f"from {len(used_targets)} targets to {DATA_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_targets", type=int, default=40,
                         help="How many confirmed-planet host stars to pull light curves for.")
    args = parser.parse_args()
    main(args.n_targets)
