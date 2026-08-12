"""
Real MAST data access for TESS / Kepler / JWST light curves, using the
`lightkurve` and `astroquery.mast` packages.

Public functions return plain dicts/lists (JSON-serializable) so routes can
return them directly.
"""
import numpy as np


def search_targets(query, mission="TESS", limit=10):
    """Search MAST for observations matching a target name (e.g. 'TOI-700',
    'Kepler-10', 'TRAPPIST-1')."""
    from astroquery.mast import Observations
    try:
        obs = Observations.query_criteria(target_name=query, obs_collection=mission)
        obs = obs[:limit]
        return [
            {
                "target_name": str(row["target_name"]),
                "obs_id": str(row["obs_id"]),
                "instrument": str(row["instrument_name"]),
                "mission": str(row["obs_collection"]),
                "start_time": float(row["t_min"]) if row["t_min"] else None,
            }
            for row in obs
        ]
    except Exception as e:
        return {"error": str(e), "hint": "MAST query failed. Check target name / network."}


def fetch_light_curve(target_name, mission="TESS"):
    """Fetch and return a real light curve time series for a target from MAST
    via lightkurve. Returns {time: [...], flux: [...], flux_err: [...]}."""
    import lightkurve as lk
    try:
        search_result = lk.search_lightcurve(target_name, mission=mission)
        if len(search_result) == 0:
            return {"error": f"No light curves found for '{target_name}' on {mission}."}

        lc = search_result[0].download()
        lc = lc.remove_nans()

        time = lc.time.value.tolist()
        flux = lc.flux.value.tolist()
        flux_err = lc.flux_err.value.tolist() if lc.flux_err is not None else [0.0] * len(flux)

        return {
            "target": target_name,
            "mission": mission,
            "time": time,
            "flux": flux,
            "flux_err": flux_err,
            "n_points": len(time),
        }
    except Exception as e:
        return {"error": str(e), "hint": "lightkurve/MAST fetch failed. Target may not exist or network issue."}


def generate_synthetic_light_curve(n_points=1000, has_transit=True, seed=None):
    """Fallback / demo light curve generator (e.g. for offline dev or ML
    training augmentation) — not real MAST data, clearly labeled as such."""
    rng = np.random.default_rng(seed)
    time = np.linspace(0, 27, n_points)  # ~1 TESS sector, days
    flux = 1.0 + rng.normal(0, 0.0008, n_points)

    if has_transit:
        period = rng.uniform(2, 10)
        depth = rng.uniform(0.002, 0.02)
        duration = rng.uniform(0.05, 0.2)
        t0 = rng.uniform(0, period)
        phase = ((time - t0) % period)
        in_transit = (phase < duration) | (phase > period - duration)
        flux[in_transit] -= depth

    return {
        "target": "SYNTHETIC",
        "mission": "SIMULATED",
        "time": time.tolist(),
        "flux": flux.tolist(),
        "flux_err": (np.full(n_points, 0.0008)).tolist(),
        "n_points": n_points,
        "synthetic": True,
    }
