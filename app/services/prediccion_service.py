from datetime import date, timedelta
from typing import Any

import joblib

from app.config import Config
from app.services.dynamo_service import dynamo_service

FERIADOS_BOLIVIA_2026 = {
    date(2026, 1, 1),
    date(2026, 2, 9),
    date(2026, 2, 10),
    date(2026, 4, 2),
    date(2026, 4, 3),
    date(2026, 5, 1),
    date(2026, 6, 19),
    date(2026, 8, 6),
    date(2026, 11, 2),
    date(2026, 12, 25),
}


class PrediccionService:
    def __init__(self) -> None:
        self._model: Any = None
        self.model_path = Config.MODELS_PATH + "demand_model.pkl"

    def _load_model(self) -> Any:
        if self._model is None:
            self._model = joblib.load(self.model_path)
        return self._model

    def predecir_demanda(
        self,
        ruta_id: str,
        fecha_str: str,
        precio_base: float = 85.0,
    ) -> dict[str, Any]:
        cache_key = f"DEMANDA#{ruta_id}"
        cached = dynamo_service.obtener_prediccion(cache_key, fecha_str)
        if cached:
            return self._build_response(
                ruta_id,
                fecha_str,
                precio_base,
                float(cached.get("valor_predicho", 0.0)),
                float(cached.get("precio_sugerido", precio_base)),
                float(cached.get("confianza", 0.0)),
                cached.get("metadata", {}).get("factores", {}),
                desde_cache=True,
            )

        features = self._build_features(ruta_id, fecha_str)
        model = self._load_model()
        ocupacion_predicha = float(model.predict([features])[0])
        ocupacion_predicha = max(0.0, min(1.0, ocupacion_predicha))
        precio_sugerido = self._calcular_precio(precio_base, ocupacion_predicha)

        factores = {
            "dia_semana": date.fromisoformat(fecha_str).strftime("%A").lower(),
            "es_feriado": bool(features[1]),
            "temporada": "alta" if features[4] else "normal",
            "historico_promedio": round(features[5], 4),
        }

        expira_en = fecha_str + "T23:59:59"
        confianza = 0.85

        dynamo_service.guardar_prediccion(
            tipo_entidad=cache_key,
            fecha=fecha_str,
            valor_predicho=ocupacion_predicha,
            precio_sugerido=precio_sugerido,
            confianza=confianza,
            modelo_version="xgboost-v1",
            expira_en=expira_en,
            metadata={"factores": factores},
        )

        return self._build_response(
            ruta_id,
            fecha_str,
            precio_base,
            ocupacion_predicha,
            precio_sugerido,
            confianza,
            factores,
            desde_cache=False,
        )

    def _build_features(self, ruta_id: str, fecha_str: str) -> list[float]:
        fecha = date.fromisoformat(fecha_str)

        dia_semana = float(fecha.weekday())
        es_feriado = 1.0 if fecha in FERIADOS_BOLIVIA_2026 else 0.0
        mes = float(fecha.month)
        semana = float(fecha.isocalendar()[1])
        es_temporada_alta = 1.0 if fecha.month in (1, 7) else 0.0

        ocupacion_semana_anterior = self._get_historico_promedio(ruta_id, fecha)
        ocupacion_mismo_dia = ocupacion_semana_anterior

        return [
            dia_semana,
            es_feriado,
            mes,
            semana,
            es_temporada_alta,
            ocupacion_semana_anterior,
            ocupacion_mismo_dia,
        ]

    def _get_historico_promedio(self, ruta_id: str, fecha: date) -> float:
        cache_key = f"DEMANDA#{ruta_id}"
        semana_anterior = fecha - timedelta(days=7)
        cached = dynamo_service.obtener_prediccion(
            cache_key, semana_anterior.isoformat()
        )
        if cached:
            return float(cached.get("valor_predicho", 0.55))
        return 0.55

    def _calcular_precio(self, precio_base: float, ocupacion: float) -> float:
        ajuste = (ocupacion - 0.5) * 50
        return round(precio_base * (1 + ajuste / 100), 2)

    def _build_response(
        self,
        ruta_id: str,
        fecha_str: str,
        precio_base: float,
        ocupacion_predicha: float,
        precio_sugerido: float,
        confianza: float,
        factores: dict[str, Any],
        desde_cache: bool,
    ) -> dict[str, Any]:
        ajuste = (
            round((precio_sugerido - precio_base) / precio_base * 100, 1)
            if precio_base
            else 0.0
        )
        return {
            "ruta_id": ruta_id,
            "fecha": fecha_str,
            "ocupacion_predicha": ocupacion_predicha,
            "precio_base_actual": precio_base,
            "precio_sugerido": precio_sugerido,
            "ajuste_porcentaje": ajuste,
            "confianza": confianza,
            "factores": factores,
            "desde_cache": desde_cache,
        }


prediccion_service = PrediccionService()
