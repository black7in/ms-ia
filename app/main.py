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

    @app.before_request
    def decamelize_request():
        if request.is_json:
            data = request.get_json(silent=True)
            if isinstance(data, (dict, list)):
                decamelized = humps.decamelize(data)
                request._cached_data = json.dumps(decamelized).encode()
                request.__dict__.pop("_cached_json", None)

    @app.after_request
    def camelize_response(response):
        if response.content_type == "application/json":
            data = response.get_json()
            if data is not None:
                response.data = json.dumps(humps.camelize(data))
                response.headers.pop("Content-Length", None)
        return response

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.FLASK_DEBUG)
