import csv
import io
import tempfile
from typing import Any

from flask import Blueprint, jsonify, request

from app.schemas.prediccion import AprobarPrediccionRequest, ReentrenarRequest
from app.services.mscore_service import mscore_service
from app.services.prediccion_service import prediccion_service
from app.utils.jwt_utils import require_auth

prediccion_bp = Blueprint("prediccion", __name__)


@prediccion_bp.route("/prediccion/demanda", methods=["GET"])
@require_auth
def demanda() -> Any:
    ruta_id = request.args.get("rutaId", "")
    fecha = request.args.get("fecha", "")
    precio_base = float(request.args.get("precioBase", 85.0))

    if not ruta_id or not fecha:
        return jsonify({"error": "rutaId y fecha son requeridos"}), 400

    result = prediccion_service.predecir_demanda(ruta_id, fecha, precio_base)
    return jsonify(result), 200


@prediccion_bp.route("/prediccion/aprobar", methods=["POST"])
@require_auth
def aprobar() -> Any:
    data = AprobarPrediccionRequest(**request.get_json())

    try:
        response = mscore_service.aprobar_precio_sugerido(
            data.ruta_id, data.fecha, data.precio_aprobado
        )
        return jsonify({"mensaje": "Precio aprobado", "detalle": response}), 200
    except Exception:
        return (
            jsonify({"mensaje": "Precio aprobado (MS-Core no disponible)"}),
            200,
        )


@prediccion_bp.route("/modelos/reentrenar", methods=["POST"])
@require_auth
def reentrenar() -> Any:
    data = ReentrenarRequest(**request.get_json())
    modelo = data.modelo

    errores: list[str] = []
    entrenados: list[str] = []

    if modelo in ("demand", "all"):
        try:
            response = mscore_service.get_datos_entrenamiento("demanda")
            _entrenar_demand(response)
            entrenados.append("demand")
        except Exception as e:
            errores.append(f"demand: {e}")

    if modelo in ("kmeans", "all"):
        try:
            response = mscore_service.get_datos_entrenamiento("clientes")
            _entrenar_kmeans(response)
            entrenados.append("kmeans")
        except Exception as e:
            errores.append(f"kmeans: {e}")

    return (
        jsonify(
            {
                "mensaje": f"Reentrenamiento: {entrenados}",
                "entrenados": entrenados,
                "errores": errores,
            }
        ),
        200 if entrenados else 500,
    )


def _entrenar_demand(response: dict[str, Any]) -> None:
    from app.models.train.train_demand import train_demand_model

    filas = response.get("filas", response.get("datos", []))
    if not filas:
        raise ValueError("MS-Core no retorno datos de demanda")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False
    ) as f:
        writer = csv.DictWriter(f, fieldnames=filas[0].keys())
        writer.writeheader()
        writer.writerows(filas)
        path = f.name

    train_demand_model(path, "app/models/demand_model.pkl")


def _entrenar_kmeans(response: dict[str, Any]) -> None:
    from app.models.train.train_segmentacion import train_segmentacion_model

    filas = response.get("filas", response.get("datos", []))
    if not filas:
        raise ValueError("MS-Core no retorno datos de clientes")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False
    ) as f:
        writer = csv.DictWriter(f, fieldnames=filas[0].keys())
        writer.writeheader()
        writer.writerows(filas)
        path = f.name

    train_segmentacion_model(path, "app/models/kmeans_model.pkl")
