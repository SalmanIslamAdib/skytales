from flask import Blueprint, jsonify, request

from ml.cnn_classifier import classify_star

classify_bp = Blueprint("classify", __name__)


@classify_bp.route("/api/classify", methods=["POST"])
def classify():
    body = request.get_json(force=True) or {}
    color_index = body.get("color_index")
    magnitude = body.get("magnitude")
    flux = body.get("flux")  # optional light curve

    if color_index is None and magnitude is None and flux is None:
        return jsonify({"error": "provide at least color_index, magnitude, or flux"}), 400

    result = classify_star(color_index, magnitude, flux)
    return jsonify(result)
