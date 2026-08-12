"""
Computes which real stars and constellations are above the horizon for any
given latitude/longitude (and optional time), using real astronomical
coordinate transforms (RA/Dec -> Alt/Az) via astropy.

The star catalog below uses real J2000 RA/Dec coordinates and V magnitudes
for ~55 well-known named stars across ~18 recognizable constellations.
"""

STAR_CATALOG = [
    {"name": "Polaris", "ra": 37.95, "dec": 89.26, "mag": 1.98, "constellation": "Ursa Minor"},
    {"name": "Kochab", "ra": 222.68, "dec": 74.16, "mag": 2.07, "constellation": "Ursa Minor"},
    {"name": "Pherkad", "ra": 230.18, "dec": 71.83, "mag": 3.05, "constellation": "Ursa Minor"},
    {"name": "Dubhe", "ra": 165.93, "dec": 61.75, "mag": 1.79, "constellation": "Ursa Major"},
    {"name": "Merak", "ra": 165.46, "dec": 56.38, "mag": 2.37, "constellation": "Ursa Major"},
    {"name": "Phecda", "ra": 178.46, "dec": 53.69, "mag": 2.44, "constellation": "Ursa Major"},
    {"name": "Megrez", "ra": 183.86, "dec": 57.03, "mag": 3.31, "constellation": "Ursa Major"},
    {"name": "Alioth", "ra": 193.51, "dec": 55.96, "mag": 1.77, "constellation": "Ursa Major"},
    {"name": "Mizar", "ra": 200.98, "dec": 54.93, "mag": 2.23, "constellation": "Ursa Major"},
    {"name": "Alkaid", "ra": 206.89, "dec": 49.31, "mag": 1.86, "constellation": "Ursa Major"},
    {"name": "Schedar", "ra": 10.13, "dec": 56.54, "mag": 2.24, "constellation": "Cassiopeia"},
    {"name": "Caph", "ra": 2.29, "dec": 59.15, "mag": 2.28, "constellation": "Cassiopeia"},
    {"name": "Gamma Cas", "ra": 14.18, "dec": 60.72, "mag": 2.47, "constellation": "Cassiopeia"},
    {"name": "Ruchbah", "ra": 21.45, "dec": 60.24, "mag": 2.68, "constellation": "Cassiopeia"},
    {"name": "Segin", "ra": 28.60, "dec": 63.67, "mag": 3.35, "constellation": "Cassiopeia"},
    {"name": "Betelgeuse", "ra": 88.79, "dec": 7.41, "mag": 0.42, "constellation": "Orion"},
    {"name": "Rigel", "ra": 78.63, "dec": -8.20, "mag": 0.18, "constellation": "Orion"},
    {"name": "Bellatrix", "ra": 81.28, "dec": 6.35, "mag": 1.64, "constellation": "Orion"},
    {"name": "Mintaka", "ra": 83.00, "dec": -0.30, "mag": 2.23, "constellation": "Orion"},
    {"name": "Alnilam", "ra": 84.05, "dec": -1.20, "mag": 1.69, "constellation": "Orion"},
    {"name": "Alnitak", "ra": 85.19, "dec": -1.94, "mag": 1.88, "constellation": "Orion"},
    {"name": "Saiph", "ra": 86.94, "dec": -9.67, "mag": 2.07, "constellation": "Orion"},
    {"name": "Antares", "ra": 247.35, "dec": -26.43, "mag": 1.06, "constellation": "Scorpius"},
    {"name": "Shaula", "ra": 263.40, "dec": -37.10, "mag": 1.62, "constellation": "Scorpius"},
    {"name": "Sargas", "ra": 264.33, "dec": -42.99, "mag": 1.87, "constellation": "Scorpius"},
    {"name": "Dschubba", "ra": 240.08, "dec": -22.62, "mag": 2.29, "constellation": "Scorpius"},
    {"name": "Regulus", "ra": 152.09, "dec": 11.97, "mag": 1.35, "constellation": "Leo"},
    {"name": "Denebola", "ra": 177.26, "dec": 14.57, "mag": 2.14, "constellation": "Leo"},
    {"name": "Algieba", "ra": 154.99, "dec": 19.84, "mag": 2.28, "constellation": "Leo"},
    {"name": "Deneb", "ra": 310.36, "dec": 45.28, "mag": 1.25, "constellation": "Cygnus"},
    {"name": "Sadr", "ra": 305.56, "dec": 40.26, "mag": 2.23, "constellation": "Cygnus"},
    {"name": "Gienah", "ra": 304.51, "dec": 33.97, "mag": 2.48, "constellation": "Cygnus"},
    {"name": "Albireo", "ra": 292.68, "dec": 27.96, "mag": 3.18, "constellation": "Cygnus"},
    {"name": "Aldebaran", "ra": 68.98, "dec": 16.51, "mag": 0.85, "constellation": "Taurus"},
    {"name": "Elnath", "ra": 81.57, "dec": 28.61, "mag": 1.65, "constellation": "Taurus"},
    {"name": "Pollux", "ra": 116.33, "dec": 28.03, "mag": 1.14, "constellation": "Gemini"},
    {"name": "Castor", "ra": 113.65, "dec": 31.89, "mag": 1.58, "constellation": "Gemini"},
    {"name": "Acrux", "ra": 186.65, "dec": -63.10, "mag": 0.77, "constellation": "Crux"},
    {"name": "Mimosa", "ra": 191.93, "dec": -59.69, "mag": 1.25, "constellation": "Crux"},
    {"name": "Gacrux", "ra": 187.79, "dec": -57.11, "mag": 1.63, "constellation": "Crux"},
    {"name": "Imai", "ra": 183.79, "dec": -58.75, "mag": 2.78, "constellation": "Crux"},
    {"name": "Markab", "ra": 346.19, "dec": 15.21, "mag": 2.49, "constellation": "Pegasus"},
    {"name": "Scheat", "ra": 345.94, "dec": 28.08, "mag": 2.42, "constellation": "Pegasus"},
    {"name": "Algenib", "ra": 3.31, "dec": 15.18, "mag": 2.83, "constellation": "Pegasus"},
    {"name": "Alpheratz", "ra": 2.10, "dec": 29.09, "mag": 2.06, "constellation": "Pegasus"},
    {"name": "Sirius", "ra": 101.29, "dec": -16.72, "mag": -1.46, "constellation": "Canis Major"},
    {"name": "Mirzam", "ra": 95.67, "dec": -17.96, "mag": 1.98, "constellation": "Canis Major"},
    {"name": "Adhara", "ra": 104.66, "dec": -28.97, "mag": 1.50, "constellation": "Canis Major"},
    {"name": "Arcturus", "ra": 213.92, "dec": 19.18, "mag": -0.05, "constellation": "Bootes"},
    {"name": "Vega", "ra": 279.23, "dec": 38.78, "mag": 0.03, "constellation": "Lyra"},
    {"name": "Altair", "ra": 297.70, "dec": 8.87, "mag": 0.76, "constellation": "Aquila"},
    {"name": "Spica", "ra": 201.30, "dec": -11.16, "mag": 1.04, "constellation": "Virgo"},
    {"name": "Capella", "ra": 79.17, "dec": 45.998, "mag": 0.08, "constellation": "Auriga"},
    {"name": "Procyon", "ra": 114.83, "dec": 5.22, "mag": 0.34, "constellation": "Canis Minor"},
    {"name": "Fomalhaut", "ra": 344.41, "dec": -29.62, "mag": 1.16, "constellation": "Piscis Austrinus"},
    {"name": "Alpha Centauri", "ra": 219.90, "dec": -60.83, "mag": -0.27, "constellation": "Centaurus"},
    {"name": "Beta Centauri", "ra": 210.96, "dec": -60.37, "mag": 0.61, "constellation": "Centaurus"},
]

CONSTELLATION_LINES = [
    ("Dubhe", "Merak"), ("Merak", "Phecda"), ("Phecda", "Megrez"), ("Megrez", "Dubhe"),
    ("Megrez", "Alioth"), ("Alioth", "Mizar"), ("Mizar", "Alkaid"),
    ("Caph", "Schedar"), ("Schedar", "Gamma Cas"), ("Gamma Cas", "Ruchbah"), ("Ruchbah", "Segin"),
    ("Betelgeuse", "Bellatrix"), ("Bellatrix", "Mintaka"), ("Mintaka", "Alnilam"),
    ("Alnilam", "Alnitak"), ("Alnitak", "Betelgeuse"), ("Mintaka", "Rigel"),
    ("Alnitak", "Saiph"), ("Rigel", "Saiph"),
    ("Dschubba", "Antares"), ("Antares", "Sargas"), ("Sargas", "Shaula"),
    ("Regulus", "Algieba"), ("Algieba", "Denebola"),
    ("Deneb", "Sadr"), ("Sadr", "Gienah"), ("Sadr", "Albireo"),
    ("Castor", "Pollux"),
    ("Acrux", "Gacrux"), ("Mimosa", "Imai"),
    ("Polaris", "Kochab"), ("Kochab", "Pherkad"),
    ("Markab", "Scheat"), ("Scheat", "Alpheratz"), ("Alpheratz", "Algenib"), ("Algenib", "Markab"),
    ("Sirius", "Mirzam"), ("Sirius", "Adhara"),
    ("Aldebaran", "Elnath"),
    ("Alpha Centauri", "Beta Centauri"),
]

# Approximate distances in light-years (rounded, from published measurements)
STAR_DISTANCE_LY = {
    "Polaris": 433, "Kochab": 130, "Pherkad": 487, "Dubhe": 123, "Merak": 79,
    "Phecda": 83, "Megrez": 58, "Alioth": 81, "Mizar": 78, "Alkaid": 101,
    "Schedar": 228, "Caph": 54, "Gamma Cas": 610, "Ruchbah": 99, "Segin": 442,
    "Betelgeuse": 548, "Rigel": 860, "Bellatrix": 250, "Mintaka": 1200,
    "Alnilam": 2000, "Alnitak": 1260, "Saiph": 650, "Antares": 550, "Shaula": 570,
    "Sargas": 270, "Dschubba": 400, "Regulus": 79, "Denebola": 36, "Algieba": 130,
    "Deneb": 2600, "Sadr": 1800, "Gienah": 72, "Albireo": 430, "Aldebaran": 65,
    "Elnath": 131, "Pollux": 34, "Castor": 51, "Acrux": 320, "Mimosa": 280,
    "Gacrux": 88, "Imai": 345, "Markab": 133, "Scheat": 196, "Algenib": 390,
    "Alpheratz": 97, "Sirius": 8.6, "Mirzam": 500, "Adhara": 430, "Arcturus": 37,
    "Vega": 25, "Altair": 17, "Spica": 250, "Capella": 43, "Procyon": 11.5,
    "Fomalhaut": 25, "Alpha Centauri": 4.37, "Beta Centauri": 390,
}

CONSTELLATION_FACTS = {
    "Ursa Major": "The Great Bear — home to the well-known 'Big Dipper' asterism.",
    "Ursa Minor": "The Little Bear — contains Polaris, the North Star.",
    "Cassiopeia": "Named after a vain queen in Greek mythology; recognizable by its W shape.",
    "Orion": "The Hunter — one of the most recognizable constellations, marked by its three-star belt.",
    "Scorpius": "The Scorpion — home to the bright red supergiant Antares.",
    "Leo": "The Lion — one of the twelve zodiac constellations.",
    "Cygnus": "The Swan, flying along the Milky Way — also called the Northern Cross.",
    "Taurus": "The Bull — home to the bright red giant Aldebaran.",
    "Gemini": "The Twins — marked by the bright stars Castor and Pollux.",
    "Crux": "The Southern Cross — the smallest constellation, used for navigation in the Southern Hemisphere.",
    "Pegasus": "The Winged Horse — marked by the Great Square asterism.",
    "Canis Major": "The Great Dog — home to Sirius, the brightest star in the night sky.",
    "Bootes": "The Herdsman — home to the bright orange giant Arcturus.",
    "Lyra": "The Lyre — home to the bright star Vega.",
    "Aquila": "The Eagle — home to the bright star Altair.",
    "Virgo": "The Maiden — the largest of the zodiac constellations.",
    "Auriga": "The Charioteer — home to the bright star Capella.",
    "Canis Minor": "The Little Dog — home to the bright star Procyon.",
    "Piscis Austrinus": "The Southern Fish — home to the bright star Fomalhaut.",
    "Centaurus": "The Centaur — home to Alpha Centauri, the closest star system to our Sun.",
}

# Real spectral types (temperature class) for each star, first letter only.
# Determines the star's true visual color: O/B = blue-white (hottest),
# A/F = white, G = yellow (like our Sun), K = orange, M = red (coolest).
STAR_SPECTRAL_TYPE = {
    "Polaris": "F", "Kochab": "K", "Pherkad": "A", "Dubhe": "K", "Merak": "A",
    "Phecda": "A", "Megrez": "A", "Alioth": "A", "Mizar": "A", "Alkaid": "B",
    "Schedar": "K", "Caph": "F", "Gamma Cas": "B", "Ruchbah": "A", "Segin": "B",
    "Betelgeuse": "M", "Rigel": "B", "Bellatrix": "B", "Mintaka": "B",
    "Alnilam": "B", "Alnitak": "O", "Saiph": "B", "Antares": "M", "Shaula": "B",
    "Sargas": "F", "Dschubba": "B", "Regulus": "B", "Denebola": "A", "Algieba": "K",
    "Deneb": "A", "Sadr": "F", "Gienah": "K", "Albireo": "K", "Aldebaran": "K",
    "Elnath": "B", "Pollux": "K", "Castor": "A", "Acrux": "B", "Mimosa": "B",
    "Gacrux": "M", "Imai": "B", "Markab": "B", "Scheat": "M", "Algenib": "B",
    "Alpheratz": "B", "Sirius": "A", "Mirzam": "B", "Adhara": "B", "Arcturus": "K",
    "Vega": "A", "Altair": "A", "Spica": "B", "Capella": "G", "Procyon": "F",
    "Fomalhaut": "A", "Alpha Centauri": "G", "Beta Centauri": "B",
}

STAR_COLOR_BY_TYPE = {
    "O": "#9bb0ff", "B": "#aabfff", "A": "#cad7ff",
    "F": "#f8f7ff", "G": "#fff4ea", "K": "#ffd2a1", "M": "#ffcc6f",
}


def compute_sky_view(lat, lon, time_str=None):
    """Returns (visible_stars, visible_constellation_lines, obstime_isot) for
    the given location and time (defaults to now)."""
    from astropy.coordinates import EarthLocation, AltAz, SkyCoord
    from astropy.time import Time
    import astropy.units as u

    location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg)
    obstime = Time(time_str) if time_str else Time.now()
    altaz_frame = AltAz(obstime=obstime, location=location)

    star_positions = {}
    visible_stars = []
    for star in STAR_CATALOG:
        coord = SkyCoord(ra=star["ra"] * u.deg, dec=star["dec"] * u.deg)
        altaz = coord.transform_to(altaz_frame)
        alt = float(altaz.alt.deg)
        az = float(altaz.az.deg)
        star_positions[star["name"]] = {"alt": alt, "az": az}
        if alt > 0:
            constellation = star["constellation"]
            spectral_type = STAR_SPECTRAL_TYPE.get(star["name"], "G")
            visible_stars.append({
                "name": star["name"],
                "constellation": constellation,
                "constellation_fact": CONSTELLATION_FACTS.get(constellation, ""),
                "magnitude": star["mag"],
                "distance_ly": STAR_DISTANCE_LY.get(star["name"]),
                "spectral_type": spectral_type,
                "color": STAR_COLOR_BY_TYPE.get(spectral_type, "#fff4ea"),
                "alt": alt,
                "az": az,
            })

    name_to_constellation = {s["name"]: s["constellation"] for s in STAR_CATALOG}

    visible_lines = []
    for name1, name2 in CONSTELLATION_LINES:
        p1 = star_positions.get(name1)
        p2 = star_positions.get(name2)
        if p1 and p2 and p1["alt"] > 0 and p2["alt"] > 0:
            constellation = name_to_constellation.get(name1, "")
            visible_lines.append({
                "constellation": constellation,
                "constellation_fact": CONSTELLATION_FACTS.get(constellation, ""),
                "star1": {"name": name1, "alt": p1["alt"], "az": p1["az"]},
                "star2": {"name": name2, "alt": p2["alt"], "az": p2["az"]},
            })

    return visible_stars, visible_lines, obstime.isot
