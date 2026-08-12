from flask import Blueprint, jsonify, request

from data.star_catalog import fetch_star_catalog
from config import Config

stars_bp = Blueprint("stars", __name__)


@stars_bp.route("/api/stars", methods=["GET"])
def get_stars():
    n = int(request.args.get("n", Config.N_STARS))
    n = min(n, 10000)
    stars = fetch_star_catalog(n_stars=n)
    return jsonify({"count": len(stars), "stars": stars})
