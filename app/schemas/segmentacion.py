from typing import Optional

from pydantic import BaseModel


class CaracteristicasSegmento(BaseModel):
    frecuencia_promedio_mensual: Optional[float] = None
    gasto_promedio: Optional[float] = None
    ruta_preferida: Optional[str] = None


class SegmentoCliente(BaseModel):
    id: int
    nombre: str
    descripcion: str
    total_clientes: int
    porcentaje: float
    caracteristicas: Optional[CaracteristicasSegmento] = None


class SegmentacionResponse(BaseModel):
    total_clientes: int
    segmentos: list[SegmentoCliente]
    modelo_version: str
    generado_en: str


class ClienteSegmentoResponse(BaseModel):
    cliente_id: str
    segmento_id: int
    segmento_nombre: str
    confianza: float
