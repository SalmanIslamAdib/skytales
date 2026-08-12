import sys
import os

sys.path.insert(0, os.path.dirname(__file__))  # allow `from data...` / `from ml...` imports

from flask import Flask
from flask_cors import CORS

from config import Config
from routes.health import health_bp
from routes.stars import stars_bp
from routes.lightcurve import lightcurve_bp
from routes.classify import classify_bp
from routes.transit import transit_bp
from routes.sky_view import sky_view_bp


def create_app():
    app = Flask(__name__)
    CORS(app)  # CORS enabled for all origins — Live Server Ready

    app.register_blueprint(health_bp)
    app.register_blueprint(stars_bp)
    app.register_blueprint(lightcurve_bp)
    app.register_blueprint(classify_bp)
    app.register_blueprint(transit_bp)
    app.register_blueprint(sky_view_bp)

    @app.route("/")
    def index():
        return {
            "service": "SkyTales API",
            "endpoints": [
                "GET  /api/health",
                "GET  /api/stars?n=3000",
                "GET  /api/search?q=<target>&mission=TESS",
                "GET  /api/lightcurve/<target_name>?mission=TESS&synthetic=false",
                "POST /api/classify  {color_index, magnitude, flux?}",
                "POST /api/transit   {flux: [...]}",
                "POST /api/transient {flux: [...], target_name}",
                "GET  /api/sky_view?lat=<lat>&lon=<lon>&time=<optional ISO time>",
            ],
        }

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
