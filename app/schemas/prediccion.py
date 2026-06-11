from pydantic import BaseModel, Field


class FactoresDemanda(BaseModel):
    dia_semana: str
    es_feriado: bool
    temporada: str
    historico_promedio: float


class PrediccionDemandaResponse(BaseModel):
    ruta_id: str
    fecha: str
    ocupacion_predicha: float
    precio_base_actual: float
    precio_sugerido: float
    ajuste_porcentaje: float
    confianza: float
    factores: FactoresDemanda
    desde_cache: bool


class AprobarPrediccionRequest(BaseModel):
    ruta_id: str
    fecha: str
    precio_aprobado: float


class ReentrenarRequest(BaseModel):
    modelo: str = Field(description="demand | kmeans | isolation_forest | all")
