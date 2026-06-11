from typing import Any

from flask import Blueprint, jsonify, request

from app.schemas.agente import AgenteReporteRequest
from app.services.agente_service import agente_service
from app.services.mscore_service import mscore_service
from app.utils.jwt_utils import require_auth

agente_bp = Blueprint("agente", __name__)


@agente_bp.route("/agente/reporte", methods=["POST"])
@require_auth
def reporte() -> Any:
    data = AgenteReporteRequest(**request.get_json())

    sql = agente_service.generar_sql(data.pregunta)

    if not sql:
        return (
            jsonify(
                {
                    "pregunta": data.pregunta,
                    "explicacion": None,
                    "sql_generado": None,
                    "columnas": [],
                    "filas": [],
                    "total_filas": 0,
                    "error": (
                        "No pude generar una consulta valida para esa pregunta. "
                        "Intenta con algo relacionado a ventas, viajes o clientes."
                    ),
                }
            ),
            200,
        )

    columnas: list[str] = []
    filas: list[list] = []
    error_msg: str | None = None

    try:
        response = mscore_service.ejecutar_query(sql)
        columnas = response.get("columnas", response.get("columns", []))
        filas = response.get("filas", response.get("rows", []))
    except Exception as exc:
        error_msg = str(exc)

    explicacion = agente_service.generar_explicacion(
        data.pregunta, sql, columnas, filas
    )

    return (
        jsonify(
            {
                "pregunta": data.pregunta,
                "explicacion": explicacion,
                "sql_generado": sql,
                "columnas": columnas,
                "filas": filas,
                "total_filas": len(filas),
                "error": error_msg,
            }
        ),
        200,
    )
