from flask import Blueprint, jsonify
import datetime

health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "SkyTales API",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    })
