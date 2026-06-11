from typing import Any

from flask import Blueprint, jsonify

from app.services.mscore_service import mscore_service
from app.services.segmentacion_service import segmentacion_service
from app.utils.jwt_utils import require_auth

segmentacion_bp = Blueprint("segmentacion", __name__)


@segmentacion_bp.route("/segmentacion/clientes", methods=["GET"])
@require_auth
def segmentos() -> Any:
    try:
        response = mscore_service.get_datos_entrenamiento("clientes")
        clientes = response.get("filas", [])
    except Exception:
        return (
            jsonify(
                {
                    "error": (
                        "No se pudieron obtener datos de MS-Core. "
                        "Verifica que el endpoint /reportes/datos-entrenamiento?tipo=clientes este disponible."
                    )
                }
            ),
            503,
        )

    if not clientes:
        return jsonify({"error": "No hay datos de clientes disponibles"}), 503

    result = segmentacion_service.obtener_segmentos(clientes)
    return jsonify(result), 200


@segmentacion_bp.route("/segmentacion/cliente/<cliente_id>", methods=["GET"])
@require_auth
def cliente_segmento(cliente_id: str) -> Any:
    try:
        response = mscore_service.get_datos_entrenamiento("clientes")
        clientes = response.get("filas", [])
    except Exception:
        return (
            jsonify({"error": "No se pudieron obtener datos de MS-Core"}),
            503,
        )

    cliente = next(
        (c for c in clientes if c.get("cliente_id") == cliente_id), None
    )

    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404

    result = segmentacion_service.clasificar_cliente(cliente)
    return jsonify(result), 200
