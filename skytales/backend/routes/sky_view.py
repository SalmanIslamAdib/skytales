from flask import Blueprint, jsonify, request

from data.sky_view import compute_sky_view

sky_view_bp = Blueprint("sky_view", __name__)


@sky_view_bp.route("/api/sky_view", methods=["GET"])
def sky_view():
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
        time_str = request.args.get("time")

        if not (-90 <= lat <= 90):
            return jsonify({"error": "latitude must be between -90 and 90"}), 400
        if not (-180 <= lon <= 180):
            return jsonify({"error": "longitude must be between -180 and 180"}), 400

        stars, lines, obstime = compute_sky_view(lat, lon, time_str)
        return jsonify({
            "latitude": lat,
            "longitude": lon,
            "time": obstime,
            "stars": stars,
            "constellation_lines": lines,
            "count": len(stars),
        })
    except (TypeError, ValueError):
        return jsonify({"error": "provide numeric 'lat' and 'lon' query params"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
