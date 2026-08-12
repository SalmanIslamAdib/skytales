from flask import Blueprint, jsonify, request

from ml.transit_lstm import detect_transit
from ml.transient_filter import filter_candidate

transit_bp = Blueprint("transit", __name__)


@transit_bp.route("/api/transit", methods=["POST"])
def transit():
    body = request.get_json(force=True) or {}
    flux = body.get("flux")
    if not flux:
        return jsonify({"error": "provide 'flux' as a list of floats"}), 400

    detection = detect_transit(flux)
    return jsonify(detection)


@transit_bp.route("/api/transient", methods=["POST"])
def transient():
    body = request.get_json(force=True) or {}
    flux = body.get("flux")
    target_name = body.get("target_name", "unknown")
    if not flux:
        return jsonify({"error": "provide 'flux' as a list of floats"}), 400

    detection = detect_transit(flux)
    result = filter_candidate(detection, flux, target_name)
    result["detection"] = detection
    return jsonify(result)
