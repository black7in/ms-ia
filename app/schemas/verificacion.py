from typing import Optional

from pydantic import BaseModel


class VerificacionChoferRequest(BaseModel):
    viaje_id: str
    chofer_id: str
    imagen_base64: str


class IdentidadResult(BaseModel):
    coincide: bool
    confianza: float


class EstadoResult(BaseModel):
    ojos_abiertos: bool
    confianza_ojos: float
    somnolencia_detectada: bool
    estado_emocional: str


class VerificacionChoferResponse(BaseModel):
    verificado: bool
    identidad: IdentidadResult
    estado: EstadoResult
    puede_iniciar_viaje: bool
    mensaje: str
