from typing import Any

import joblib
import numpy as np

from app.config import Config
from app.services.dynamo_service import dynamo_service
from app.utils.datetime_utils import iso_bolivia

SEGMENT_LABELS = {
    0: {"nombre": "Cliente frecuente", "descripcion": "Alta frecuencia, alto gasto"},
    1: {"nombre": "Cliente regular", "descripcion": "Frecuencia media"},
    2: {"nombre": "Cliente ocasional", "descripcion": "Baja frecuencia"},
}


class SegmentacionService:
    def __init__(self) -> None:
        self._model: Any = None
        self.model_path = Config.MODELS_PATH + "kmeans_model.pkl"

    def _load_model(self) -> Any:
        if self._model is None:
            self._model = joblib.load(self.model_path)
        return self._model

    def obtener_segmentos(self, clientes_data: list[dict[str, Any]]) -> dict[str, Any]:
        if not clientes_data:
            return {
                "total_clientes": 0,
                "segmentos": [],
                "modelo_version": "kmeans-v1",
                "generado_en": iso_bolivia(),
            }

        features = []
        for c in clientes_data:
            features.append(
                [
                    float(c.get("frecuencia_mensual", 0)),
                    float(c.get("gasto_promedio", 0)),
                    int(c.get("variedad_rutas", 0)),
                    int(c.get("dia_preferido", 0)),
                ]
            )

        model = self._load_model()
        X = np.array(features)
        labels = model.predict(X)

        counts = np.bincount(labels, minlength=3)
        total = len(clientes_data)

        segmentos = []
        for i in range(3):
            mask = labels == i
            clientes_segmento = [clientes_data[j] for j in range(total) if mask[j]]

            gasto_prom = 0.0
            frec_prom = 0.0
            if clientes_segmento:
                gasto_prom = round(
                    float(np.mean([float(c.get("gasto_promedio", 0)) for c in clientes_segmento])), 2
                )
                frec_prom = round(
                    float(np.mean([float(c.get("frecuencia_mensual", 0)) for c in clientes_segmento])), 2
                )

            segmentos.append(
                {
                    "id": i,
                    "total_clientes": int(counts[i]),
                    "porcentaje": round(counts[i] / total * 100, 1),
                    "caracteristicas": {
                        "frecuencia_promedio_mensual": frec_prom,
                        "gasto_promedio": gasto_prom,
                    },
                    "_gasto": gasto_prom,
                }
            )

        segmentos.sort(key=lambda s: s["_gasto"], reverse=True)

        etiquetas = [
            {"nombre": "Cliente frecuente", "descripcion": "Alta frecuencia, alto gasto"},
            {"nombre": "Cliente regular", "descripcion": "Frecuencia media"},
            {"nombre": "Cliente ocasional", "descripcion": "Baja frecuencia"},
        ]

        for idx, seg in enumerate(segmentos):
            seg["nombre"] = etiquetas[idx]["nombre"]
            seg["descripcion"] = etiquetas[idx]["descripcion"]
            seg["id"] = idx
            del seg["_gasto"]
            mask = labels == i
            clientes_segmento = [clientes_data[j] for j in range(total) if mask[j]]

            caracteristicas = {}
            if clientes_segmento:
                frecuencias = [
                    float(c.get("frecuencia_mensual", 0)) for c in clientes_segmento
                ]
                gastos = [float(c.get("gasto_promedio", 0)) for c in clientes_segmento]
                caracteristicas = {
                    "frecuencia_promedio_mensual": round(np.mean(frecuencias), 2),
                    "gasto_promedio": round(np.mean(gastos), 2),
                }

            segmentos.append(
                {
                    "id": i,
                    "nombre": label_info["nombre"],
                    "descripcion": label_info["descripcion"],
                    "total_clientes": int(counts[i]),
                    "porcentaje": round(counts[i] / total * 100, 1),
                    "caracteristicas": caracteristicas,
                }
            )

        result = {
            "total_clientes": total,
            "segmentos": segmentos,
            "modelo_version": "kmeans-v1",
            "generado_en": iso_bolivia(),
        }

        cache_key = "SEGMENTO#resumen"
        dynamo_service.guardar_prediccion(
            tipo_entidad=cache_key,
            fecha=iso_bolivia()[:10],
            valor_predicho=0.0,
            precio_sugerido=0.0,
            confianza=0.9,
            modelo_version="kmeans-v1",
            expira_en=iso_bolivia(),
            metadata={"segmentos": result},
        )

        return result

    def clasificar_cliente(self, cliente_data: dict[str, Any]) -> dict[str, Any]:
        features = np.array(
            [
                [
                    float(cliente_data.get("frecuencia_mensual", 0)),
                    float(cliente_data.get("gasto_promedio", 0)),
                    int(cliente_data.get("variedad_rutas", 0)),
                    int(cliente_data.get("dia_preferido", 0)),
                ]
            ]
        )

        model = self._load_model()
        cluster_id = int(model.predict(features)[0])
        label_info = SEGMENT_LABELS.get(
            cluster_id, {"nombre": f"Segmento {cluster_id}", "descripcion": ""}
        )

        return {
            "cliente_id": cliente_data.get("cliente_id", ""),
            "segmento_id": cluster_id,
            "segmento_nombre": label_info["nombre"],
            "confianza": 0.85,
        }


segmentacion_service = SegmentacionService()
