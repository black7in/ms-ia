import csv
import os
from typing import Any

from flask import Blueprint, jsonify

from app.services.segmentacion_service import segmentacion_service
from app.utils.jwt_utils import require_auth

segmentacion_bp = Blueprint("segmentacion", __name__)


def _cargar_clientes() -> list[dict[str, Any]]:
    path = os.path.join("tmp", "training_data", "clientes_data.csv")
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


@segmentacion_bp.route("/segmentacion/clientes", methods=["GET"])
@require_auth
def segmentos() -> Any:
    clientes = _cargar_clientes()
    if not clientes:
        return jsonify({"error": "No hay datos de clientes disponibles"}), 503

    result = segmentacion_service.obtener_segmentos(clientes)
    return jsonify(result), 200


@segmentacion_bp.route("/segmentacion/cliente/<cliente_id>", methods=["GET"])
@require_auth
def cliente_segmento(cliente_id: str) -> Any:
    clientes = _cargar_clientes()
    cliente = next((c for c in clientes if c.get("cliente_id") == cliente_id), None)

    if not cliente:
        return jsonify({"error": "Cliente no encontrado"}), 404

    result = segmentacion_service.clasificar_cliente(cliente)
    return jsonify(result), 200
