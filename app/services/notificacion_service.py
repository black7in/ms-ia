import logging
from typing import Any

from app.config import Config

logger = logging.getLogger(__name__)


class NotificacionService:
    def __init__(self) -> None:
        self.mock = Config.MOCK_PUSH_NOTIFICATIONS

    def alertar_supervisor(
        self, viaje_id: str, resultado: dict[str, Any], mensaje: str
    ) -> None:
        if self.mock:
            logger.info(
                "[MOCK] Notificando supervisor: viaje=%s, mensaje=%s",
                viaje_id,
                mensaje,
            )
            return

        logger.info(
            "Notificacion real a supervisor: viaje=%s, mensaje=%s",
            viaje_id,
            mensaje,
        )


notificacion_service = NotificacionService()
