"""
Cross-matches Hipparcos star IDs against SIMBAD to fetch REAL, catalog-assigned
spectral types — replacing the B-V color-index proxy used as a fallback in
star_catalog.py._spectral_bucket.

SIMBAD's SP_TYPE field is a human/pipeline-curated spectral classification
(e.g. "G2V", "K0III", "M3.5V"), which is what real astronomical pipelines use.
"""
import numpy as np

# Folds M-type stars into K to match the 6-class scheme (O,B,A,F,G,K).
# Returns None for spectral types outside OBAFGKM (white dwarfs "D",
# carbon stars "C", Wolf-Rayet "W", etc.) — those are dropped from training
# rather than mislabeled.
_VALID_FIRST_LETTERS = {"O", "B", "A", "F", "G", "K"}


def parse_spectral_class(sp_type_str):
    if not sp_type_str:
        return None
    sp_type_str = str(sp_type_str).strip()
    if not sp_type_str:
        return None
    first = sp_type_str[0].upper()
    if first in _VALID_FIRST_LETTERS:
        return first
    if first == "M":
        return "K"  # fold cool dwarfs into K bucket, see note above
    return None


def fetch_simbad_spectral_types(hip_ids, batch_size=200):
    """hip_ids: list of ints (Hipparcos numbers).
    Returns dict: hip_id -> single-letter spectral class ('O'..'K') or None
    if no SIMBAD match / no usable spectral type.

    Uses SIMBAD's direct TAP/ADQL query interface (query_tap) rather than the
    older query_objects() convenience method. query_objects() always returns
    an internal 'object_number_id' column that some astropy/numpy builds on
    Windows fail to parse (OverflowError: Python int too large to convert to
    C long, since Windows' C 'long' is 32-bit even on 64-bit Python). query_tap
    lets us request only the columns we actually need, sidestepping that bug
    entirely.
    """
    from astroquery.simbad import Simbad

    results = {h: None for h in hip_ids}

    for i in range(0, len(hip_ids), batch_size):
        batch = hip_ids[i:i + batch_size]
        id_list = ", ".join(f"'HIP {h}'" for h in batch)
        query = f"""
            SELECT ident.id AS hip_id, basic.sp_type AS sp_type
            FROM ident
            JOIN basic ON ident.oidref = basic.oid
            WHERE ident.id IN ({id_list})
        """
        try:
            table = Simbad.query_tap(query)
        except Exception as e:
            print(f"[simbad] batch starting at {i} failed: {e}")
            continue
        if table is None or len(table) == 0:
            continue

        for row in table:
            try:
                hip_str = row["hip_id"]
                hip_str = hip_str.decode() if isinstance(hip_str, bytes) else str(hip_str)
                hip = int(hip_str.strip().split()[1])
                sp_raw = row["sp_type"]
                sp_str = sp_raw.decode() if isinstance(sp_raw, bytes) else str(sp_raw)
                results[hip] = parse_spectral_class(sp_str)
            except Exception:
                continue

    return results