from flask import Blueprint, jsonify, request

from data.mast_client import fetch_light_curve, search_targets, generate_synthetic_light_curve

lightcurve_bp = Blueprint("lightcurve", __name__)


@lightcurve_bp.route("/api/search", methods=["GET"])
def search():
    query = request.args.get("q", "")
    mission = request.args.get("mission", "TESS")
    if not query:
        return jsonify({"error": "missing query param 'q'"}), 400
    results = search_targets(query, mission=mission)
    return jsonify({"query": query, "mission": mission, "results": results})


@lightcurve_bp.route("/api/lightcurve/<target_name>", methods=["GET"])
def lightcurve(target_name):
    mission = request.args.get("mission", "TESS")
    synthetic = request.args.get("synthetic", "false").lower() == "true"

    if synthetic:
        data = generate_synthetic_light_curve(has_transit=True)
    else:
        data = fetch_light_curve(target_name, mission=mission)
        if "error" in data:
            # graceful fallback so the frontend always has something to plot
            fallback = generate_synthetic_light_curve(has_transit=True)
            fallback["fallback_reason"] = data["error"]
            data = fallback

    return jsonify(data)
