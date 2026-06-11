import functools
import logging
from typing import Any, Callable

from flask import request, jsonify

from app.config import Config

logger = logging.getLogger(__name__)


def require_auth(f: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if Config.ENVIRONMENT == "development" and not Config.JWT_SECRET:
            return f(*args, **kwargs)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token requerido"}), 401

        token = auth_header.split(" ", 1)[1]

        try:
            import jwt

            payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
            request.user = payload
        except Exception:
            return jsonify({"error": "Token invalido"}), 401

        return f(*args, **kwargs)

    return wrapper
