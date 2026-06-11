from flask import Blueprint, jsonify
from datetime import datetime, timezone
from typing import Any

from app.config import Config

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check() -> tuple[Any, int]:
    return (
        jsonify(
            {
                "status": "ok",
                "service": "ms-ia",
                "environment": Config.ENVIRONMENT,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
        200,
    )
