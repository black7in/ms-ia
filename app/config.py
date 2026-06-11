import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    PORT: int = int(os.getenv("PORT", "8002"))
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-in-production")

    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "test")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
    S3_BUCKET_EVIDENCIAS: str = os.getenv("S3_BUCKET_EVIDENCIAS", "bustrack-evidencias")
    S3_BUCKET_LICENCIAS: str = os.getenv("S3_BUCKET_LICENCIAS", "bustrack-licencias")

    DYNAMODB_ENDPOINT: str | None = os.getenv("DYNAMODB_ENDPOINT") or None
    DYNAMODB_TABLE_INFERENCIAS: str = os.getenv(
        "DYNAMODB_TABLE_INFERENCIAS", "inferencias_ia"
    )
    DYNAMODB_TABLE_PREDICCIONES: str = os.getenv(
        "DYNAMODB_TABLE_PREDICCIONES", "predicciones_ml"
    )

    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", "/app/credentials/google-vision.json"
    )

    MS_CORE_URL: str = os.getenv("MS_CORE_URL", "http://localhost:3000")
    MS_OPERACIONES_URL: str = os.getenv("MS_OPERACIONES_URL", "http://localhost:8001")

    MOCK_REKOGNITION: bool = os.getenv("MOCK_REKOGNITION", "true").lower() == "true"
    MOCK_S3: bool = os.getenv("MOCK_S3", "true").lower() == "true"
    MOCK_PUSH_NOTIFICATIONS: bool = (
        os.getenv("MOCK_PUSH_NOTIFICATIONS", "true").lower() == "true"
    )

    MODELS_PATH: str = os.getenv("MODELS_PATH", "app/models/")
    REENTRENAR_AUTO: bool = os.getenv("REENTRENAR_AUTO", "true").lower() == "true"

    UMBRAL_IDENTIDAD_FACIAL: float = float(os.getenv("UMBRAL_IDENTIDAD_FACIAL", "90.0"))
    UMBRAL_SOMNOLENCIA: float = float(os.getenv("UMBRAL_SOMNOLENCIA", "70.0"))

    EXPO_ACCESS_TOKEN: str = os.getenv("EXPO_ACCESS_TOKEN", "")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:4200")
