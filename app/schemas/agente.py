from pydantic import BaseModel


class AgenteReporteRequest(BaseModel):
    pregunta: str


class AgenteReporteResponse(BaseModel):
    pregunta: str
    explicacion: str | None = None
    sql_generado: str | None = None
    columnas: list[str] = []
    filas: list[list] = []
    total_filas: int = 0
    error: str | None = None
