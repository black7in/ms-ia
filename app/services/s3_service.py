import base64
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from app.config import Config


class S3Service:
    def __init__(self) -> None:
        self.mock = Config.MOCK_S3
        self.bucket_evidencias = Config.S3_BUCKET_EVIDENCIAS
        self.bucket_licencias = Config.S3_BUCKET_LICENCIAS

        if not self.mock:
            self.client = boto3.client(
                "s3",
                region_name=Config.AWS_REGION,
                endpoint_url=None,
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            )
        else:
            self.mock_dir = Path("tmp/ia-uploads")
            self.mock_dir.mkdir(parents=True, exist_ok=True)

    def subir_imagen(
        self, imagen_base64: str, key: str, bucket: str | None = None
    ) -> str:
        if "," in imagen_base64:
            imagen_base64 = imagen_base64.split(",", 1)[1]
        image_bytes = base64.b64decode(imagen_base64)

        bucket = bucket or self.bucket_evidencias

        if self.mock:
            file_path = self.mock_dir / bucket / key
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(image_bytes)
            return key

        self._ensure_bucket(bucket)
        self.client.put_object(
            Bucket=bucket,
            Key=key,
            Body=image_bytes,
            ContentType="image/jpeg",
        )
        return key

    def leer_imagen(self, key: str, bucket: str | None = None) -> bytes:
        bucket = bucket or self.bucket_evidencias

        if self.mock:
            file_path = self.mock_dir / bucket / key
            if not file_path.exists():
                raise FileNotFoundError(f"Imagen no encontrada: {key}")
            return file_path.read_bytes()

        response = self.client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    def existe_imagen(self, key: str, bucket: str | None = None) -> bool:
        bucket = bucket or self.bucket_evidencias

        if self.mock:
            return (self.mock_dir / bucket / key).exists()

        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False

    def _ensure_bucket(self, bucket: str) -> None:
        try:
            self.client.head_bucket(Bucket=bucket)
        except ClientError:
            self.client.create_bucket(Bucket=bucket)


s3_service = S3Service()
