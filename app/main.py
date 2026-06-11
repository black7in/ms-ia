import json

import humps
from flask import Flask, request
from flask_cors import CORS

from app.config import Config
from app.routes.health import health_bp
from app.routes.verificacion import verificacion_bp
from app.routes.prediccion import prediccion_bp
from app.routes.segmentacion import segmentacion_bp
from app.routes.agente import agente_bp


def create_app() -> Flask:
    app = Flask(__name__)

    origins = [
        origin.strip() for origin in Config.CORS_ORIGINS.split(",") if origin.strip()
    ]
    CORS(app, origins=origins)

    app.register_blueprint(health_bp)
    app.register_blueprint(verificacion_bp)
    app.register_blueprint(prediccion_bp)
    app.register_blueprint(segmentacion_bp)
    app.register_blueprint(agente_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.FLASK_DEBUG)
