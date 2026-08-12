"""
Queries the NASA Exoplanet Archive for confirmed transiting planets with
known ephemerides (period, transit duration, transit epoch), used to build
a REAL-light-curve training set for transit detection — labeling actual
MAST flux data using the planet's confirmed transit timing, instead of
injecting synthetic box-transits into noise.
"""


def fetch_confirmed_transiting_planets(limit=50, facility="TESS"):
    """Returns list of dicts: planet_name, hostname, period_days,
    duration_hours, epoch_bjd, tic_id."""
    from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive

    try:
        table = NasaExoplanetArchive.query_criteria(
            table="pscomppars",
            select="pl_name,hostname,pl_orbper,pl_trandur,pl_tranmid,tic_id,disc_facility",
            where=(
                "pl_orbper is not null and pl_trandur is not null "
                f"and pl_tranmid is not null and disc_facility like '%{facility}%'"
            ),
        )
    except Exception as e:
        print(f"[exoplanet_archive] query failed: {e}")
        return []

    planets = []
    for row in table:
        try:
            planets.append({
                "planet_name": str(row["pl_name"]),
                "hostname": str(row["hostname"]),
                "period_days": float(row["pl_orbper"]),
                "duration_hours": float(row["pl_trandur"]),
                "epoch_bjd": float(row["pl_tranmid"]),
                "tic_id": str(row["tic_id"]) if row["tic_id"] else None,
            })
        except Exception:
            continue
        if len(planets) >= limit:
            break

    return planets
