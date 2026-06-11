from typing import Any

import requests

from app.config import Config


class MSCoreService:
    def __init__(self) -> None:
        self.base_url = Config.MS_CORE_URL.rstrip("/")
        self.timeout = 10

    def _get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        response = requests.post(url, json=body, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_chofer(self, chofer_id: str) -> dict[str, Any]:
        return self._get(f"/choferes/{chofer_id}")

    def get_bus(self, bus_id: str) -> dict[str, Any]:
        return self._get(f"/buses/{bus_id}")

    def get_datos_entrenamiento(self, tipo: str) -> dict[str, Any]:
        return self._get(
            "/reportes/datos-entrenamiento",
            params={"tipo": tipo},
        )

    def aprobar_precio_sugerido(
        self, ruta_id: str, fecha: str, precio_aprobado: float
    ) -> dict[str, Any]:
        return self._post(
            "/tarifas/aprobar-sugerencia",
            body={
                "rutaId": ruta_id,
                "fecha": fecha,
                "precioAprobado": precio_aprobado,
            },
        )

    def ejecutar_query(self, sql: str) -> dict[str, Any]:
        return self._post(
            "/reportes/query",
            body={"sql": sql},
        )


mscore_service = MSCoreService()
