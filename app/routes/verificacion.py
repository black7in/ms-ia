import logging
import time
from typing import Any

from flask import Blueprint, jsonify, request

from app.schemas.verificacion import VerificacionChoferRequest
from app.services.dynamo_service import dynamo_service
from app.services.mscore_service import mscore_service
from app.services.notificacion_service import notificacion_service
from app.services.rekognition_service import rekognition_service
from app.services.s3_service import s3_service
from app.utils.jwt_utils import require_auth

logger = logging.getLogger(__name__)

verificacion_bp = Blueprint("verificacion", __name__)


@verificacion_bp.route("/verificacion/chofer", methods=["POST"])
@require_auth
def verificar_chofer() -> Any:
    data = VerificacionChoferRequest(**request.get_json())
    inicio = time.perf_counter()

    s3_key = s3_service.subir_imagen(
        data.imagen_base64, f"facial/{data.viaje_id}/selfie.jpg"
    )

    try:
        chofer = mscore_service.get_chofer(data.chofer_id)
        foto_registrada_s3_key: str = chofer.get("fotoFacialS3Key", "")
    except Exception:
        foto_registrada_s3_key = ""

    if not foto_registrada_s3_key:
        return (
            jsonify(
                {
                    "verificado": False,
                    "identidad": {"coincide": False, "confianza": 0.0},
                    "estado": None,
                    "puede_iniciar_viaje": False,
                    "mensaje": "Chofer no tiene foto registrada en el sistema",
                }
            ),
            200,
        )

    resultado_identidad = rekognition_service.comparar_caras(
        s3_key_fuente=foto_registrada_s3_key,
        s3_key_objetivo=s3_key,
    )

    resultado_estado = rekognition_service.analizar_estado(s3_key)

    puede_iniciar = (
        resultado_identidad["coincide"]
        and not resultado_estado["somnolencia_detectada"]
    )

    tiempo_ms = int((time.perf_counter() - inicio) * 1000)

    if not puede_iniciar:
        notificacion_service.alertar_supervisor(
            data.viaje_id, resultado_estado, "Problema en verificacion de chofer"
        )

    dynamo_service.guardar_inferencia(
        tipo="FACIAL",
        viaje_id=data.viaje_id,
        chofer_id=data.chofer_id,
        bus_id="",
        input_s3_key=s3_key,
        resultado={
            "coincide": resultado_identidad.get("coincide", False),
            "confianza": resultado_identidad.get("confianza", 0.0),
            "ojos_abiertos": resultado_estado.get("ojos_abiertos", False),
            "confianza_ojos": resultado_estado.get("confianza_ojos", 0.0),
            "somnolencia_detectada": resultado_estado.get("somnolencia_detectada", False),
            "estado_emocional": resultado_estado.get("estado_emocional", ""),
            "puede_iniciar_viaje": puede_iniciar,
        },
        confianza=resultado_identidad.get("confianza", 0.0),
        modelo_usado="rekognition",
        tiempo_ms=tiempo_ms,
    )

    mensaje = (
        "Verificacion exitosa"
        if puede_iniciar
        else "Somnolencia detectada. Notificando al supervisor."
    )

    return (
        jsonify(
            {
                "verificado": puede_iniciar,
                "identidad": resultado_identidad,
                "estado": resultado_estado,
                "puede_iniciar_viaje": puede_iniciar,
                "mensaje": mensaje,
            }
        ),
        200,
    )


@verificacion_bp.route("/verificacion/viaje/<viaje_id>/estado", methods=["GET"])
@require_auth
def estado_verificacion(viaje_id: str) -> Any:
    facial = dynamo_service.consultar_inferencias_por_viaje_y_tipo(viaje_id, "FACIAL")

    chofer_ok = any(
        item.get("resultado", {}).get("puede_iniciar_viaje", False) for item in facial
    )
    identidad_ok = any(
        item.get("resultado", {}).get("coincide", False) for item in facial
    )
    estado_ok = any(
        not item.get("resultado", {}).get("somnolencia_detectada", True)
        for item in facial
    )

    return (
        jsonify(
            {
                "viaje_id": viaje_id,
                "chofer_verificado": chofer_ok,
                "puede_iniciar": chofer_ok,
                "detalle": {
                    "identidad_ok": identidad_ok,
                    "estado_ok": estado_ok,
                    "timestamp": facial[0].get("created_at") if facial else None,
                },
            }
        ),
        200,
    )


@verificacion_bp.route(
    "/verificacion/historial/chofer/<chofer_id>", methods=["GET"]
)
@require_auth
def historial_chofer(chofer_id: str) -> Any:
    items = dynamo_service.consultar_inferencias_por_chofer(chofer_id, limit=50)
    historial = []
    for item in items:
        resultado = item.get("resultado", {})
        historial.append(
            {
                "viaje_id": item.get("viaje_id", ""),
                "fecha": item.get("created_at", ""),
                "tipo": item.get("tipo", ""),
                "identidad_ok": resultado.get("coincide", False),
                "estado_ok": not resultado.get("somnolencia_detectada", True),
                "confianza": float(item.get("confianza", 0)),
            }
        )
    return jsonify({"chofer_id": chofer_id, "historial": historial}), 200
