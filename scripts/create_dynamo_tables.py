import os
import sys

import boto3
from dotenv import load_dotenv

load_dotenv()


def get_dynamo_client() -> boto3.client:
    return boto3.client(
        "dynamodb",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        endpoint_url=os.getenv("DYNAMODB_ENDPOINT", "http://localhost:4566"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
    )


def crear_tabla_inferencias(client: boto3.client) -> None:
    tabla = os.getenv("DYNAMODB_TABLE_INFERENCIAS", "inferencias_ia")

    try:
        client.describe_table(TableName=tabla)
        print(f"[OK] Tabla '{tabla}' ya existe.")
        return
    except client.exceptions.ResourceNotFoundException:
        pass

    client.create_table(
        TableName=tabla,
        KeySchema=[
            {"AttributeName": "tipo_fecha", "KeyType": "HASH"},
            {"AttributeName": "timestamp_id", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "tipo_fecha", "AttributeType": "S"},
            {"AttributeName": "timestamp_id", "AttributeType": "S"},
            {"AttributeName": "chofer_id", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "chofer-fecha-index",
                "KeySchema": [
                    {"AttributeName": "chofer_id", "KeyType": "HASH"},
                    {"AttributeName": "created_at", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    print(f"[OK] Tabla '{tabla}' creada con GSI 'chofer-fecha-index'.")


def crear_tabla_predicciones(client: boto3.client) -> None:
    tabla = os.getenv("DYNAMODB_TABLE_PREDICCIONES", "predicciones_ml")

    try:
        client.describe_table(TableName=tabla)
        print(f"[OK] Tabla '{tabla}' ya existe.")
        return
    except client.exceptions.ResourceNotFoundException:
        pass

    client.create_table(
        TableName=tabla,
        KeySchema=[
            {"AttributeName": "tipo_entidad", "KeyType": "HASH"},
            {"AttributeName": "fecha", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "tipo_entidad", "AttributeType": "S"},
            {"AttributeName": "fecha", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    client.update_time_to_live(
        TableName=tabla,
        TimeToLiveSpecification={"AttributeName": "expira_en", "Enabled": True},
    )
    print(f"[OK] Tabla '{tabla}' creada con TTL en 'expira_en'.")


def main() -> None:
    print("Conectando a DynamoDB...")
    client = get_dynamo_client()

    tablas_existentes = client.list_tables().get("TableNames", [])
    print(f"Tablas existentes: {tablas_existentes}")

    crear_tabla_inferencias(client)
    crear_tabla_predicciones(client)

    print("Listo.")


if __name__ == "__main__":
    sys.exit(main())
