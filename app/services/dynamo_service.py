import uuid
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

from app.config import Config
from app.utils.datetime_utils import iso_bolivia, hoy_bolivia_str


def _to_decimal(value: Any) -> Any:
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: _to_decimal(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_decimal(v) for v in value]
    return value


class DynamoService:
    def __init__(self) -> None:
        self.resource = boto3.resource(
            "dynamodb",
            region_name=Config.AWS_REGION,
            endpoint_url=Config.DYNAMODB_ENDPOINT,
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
        )
        self.tabla_inferencias = self.resource.Table(Config.DYNAMODB_TABLE_INFERENCIAS)
        self.tabla_predicciones = self.resource.Table(
            Config.DYNAMODB_TABLE_PREDICCIONES
        )

    def guardar_inferencia(
        self,
        tipo: str,
        viaje_id: str,
        chofer_id: str,
        bus_id: str,
        input_s3_key: str,
        resultado: dict[str, Any],
        confianza: float,
        modelo_usado: str,
        tiempo_ms: int,
    ) -> str:
        timestamp_id = f"{iso_bolivia()}#{uuid.uuid4()}"
        tipo_fecha = f"{tipo}#{hoy_bolivia_str()}"
        created_at = iso_bolivia()

        item: dict[str, Any] = {
            "tipo_fecha": tipo_fecha,
            "timestamp_id": timestamp_id,
            "tipo": tipo,
            "viaje_id": viaje_id,
            "chofer_id": chofer_id,
            "bus_id": bus_id,
            "input_s3_key": input_s3_key,
            "resultado": resultado,
            "confianza": confianza,
            "modelo_usado": modelo_usado,
            "tiempo_ms": tiempo_ms,
            "created_at": created_at,
        }

        self.tabla_inferencias.put_item(Item=_to_decimal(item))
        return timestamp_id

    def consultar_inferencias_por_chofer(
        self, chofer_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        response = self.tabla_inferencias.query(
            IndexName="chofer-fecha-index",
            KeyConditionExpression=Key("chofer_id").eq(chofer_id),
            ScanIndexForward=False,
            Limit=limit,
        )
        return response.get("Items", [])

    def consultar_inferencias_por_viaje_y_tipo(
        self, viaje_id: str, tipo: str
    ) -> list[dict[str, Any]]:
        response = self.tabla_inferencias.scan(
            FilterExpression="viaje_id = :vid AND tipo = :t",
            ExpressionAttributeValues={":vid": viaje_id, ":t": tipo},
        )
        return response.get("Items", [])

    def verificar_viaje_completado(self, viaje_id: str) -> dict[str, Any]:
        facial = self.consultar_inferencias_por_viaje_y_tipo(viaje_id, "FACIAL")
        placa = self.consultar_inferencias_por_viaje_y_tipo(viaje_id, "BUS_PLACA")

        chofer_ok = any(
            item.get("resultado", {}).get("puede_iniciar_viaje", False)
            or item.get("resultado", {}).get("verificado", False)
            for item in facial
        )
        bus_ok = any(
            item.get("resultado", {}).get("coincide", False)
            or item.get("resultado", {}).get("verificado", False)
            for item in placa
        )

        return {
            "chofer_verificado": chofer_ok,
            "bus_verificado": bus_ok,
            "puede_iniciar": chofer_ok and bus_ok,
        }

    def guardar_prediccion(
        self,
        tipo_entidad: str,
        fecha: str,
        valor_predicho: float,
        precio_sugerido: float,
        confianza: float,
        modelo_version: str,
        expira_en: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        item: dict[str, Any] = {
            "tipo_entidad": tipo_entidad,
            "fecha": fecha,
            "valor_predicho": valor_predicho,
            "precio_sugerido": precio_sugerido,
            "confianza": confianza,
            "modelo_version": modelo_version,
            "generado_en": iso_bolivia(),
            "expira_en": expira_en,
            "metadata": metadata or {},
        }

        self.tabla_predicciones.put_item(Item=_to_decimal(item))

    def obtener_prediccion(
        self, tipo_entidad: str, fecha: str
    ) -> dict[str, Any] | None:
        response = self.tabla_predicciones.get_item(
            Key={"tipo_entidad": tipo_entidad, "fecha": fecha}
        )
        return response.get("Item")

    def listar_predicciones_por_tipo(
        self, tipo_entidad_prefix: str, limit: int = 30
    ) -> list[dict[str, Any]]:
        response = self.tabla_predicciones.query(
            KeyConditionExpression=Key("tipo_entidad").eq(tipo_entidad_prefix),
            ScanIndexForward=False,
            Limit=limit,
        )
        return response.get("Items", [])


dynamo_service = DynamoService()
