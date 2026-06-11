from typing import Any

import boto3
from botocore.config import Config as BotoConfig

from app.config import Config


class RekognitionService:
    def __init__(self) -> None:
        self.mock = Config.MOCK_REKOGNITION
        self.bucket_evidencias = Config.S3_BUCKET_EVIDENCIAS
        self.bucket_licencias = Config.S3_BUCKET_LICENCIAS
        self.umbral_identidad = Config.UMBRAL_IDENTIDAD_FACIAL
        self.umbral_somnolencia = Config.UMBRAL_SOMNOLENCIA

        if not self.mock:
            self.client = boto3.client(
                "rekognition",
                region_name=Config.AWS_REGION,
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                config=BotoConfig(connect_timeout=10, read_timeout=10),
            )

    def comparar_caras(
        self,
        s3_key_fuente: str,
        s3_key_objetivo: str,
        bucket_fuente: str | None = None,
        bucket_objetivo: str | None = None,
    ) -> dict[str, Any]:
        if self.mock:
            return {"coincide": True, "confianza": 98.5}

        bucket_f = bucket_fuente or self.bucket_licencias
        bucket_o = bucket_objetivo or self.bucket_evidencias

        response = self.client.compare_faces(
            SourceImage={"S3Object": {"Bucket": bucket_f, "Name": s3_key_fuente}},
            TargetImage={"S3Object": {"Bucket": bucket_o, "Name": s3_key_objetivo}},
            SimilarityThreshold=self.umbral_identidad,
        )

        matches = response.get("FaceMatches", [])
        if matches:
            similarity = matches[0].get("Similarity", 0.0)
            return {
                "coincide": similarity >= self.umbral_identidad,
                "confianza": similarity,
            }

        return {"coincide": False, "confianza": 0.0}

    def analizar_estado(self, s3_key: str, bucket: str | None = None) -> dict[str, Any]:
        if self.mock:
            return {
                "ojos_abiertos": True,
                "confianza_ojos": 99.5,
                "somnolencia_detectada": False,
                "estado_emocional": "CALM",
            }

        bucket = bucket or self.bucket_evidencias

        response = self.client.detect_faces(
            Image={"S3Object": {"Bucket": bucket, "Name": s3_key}},
            Attributes=["ALL"],
        )

        details = response.get("FaceDetails", [])
        if not details:
            return {
                "ojos_abiertos": False,
                "confianza_ojos": 0.0,
                "somnolencia_detectada": True,
                "estado_emocional": "UNKNOWN",
            }

        face = details[0]
        eyes_open = face.get("EyesOpen", {})
        eyes_value = eyes_open.get("Value", False)
        eyes_conf = eyes_open.get("Confidence", 0.0)

        emotions = face.get("Emotions", [])
        estado_emocional = emotions[0].get("Type", "UNKNOWN") if emotions else "UNKNOWN"

        somnolencia = not eyes_value or eyes_conf < self.umbral_somnolencia

        return {
            "ojos_abiertos": eyes_value,
            "confianza_ojos": eyes_conf,
            "somnolencia_detectada": somnolencia,
            "estado_emocional": estado_emocional,
        }


rekognition_service = RekognitionService()
