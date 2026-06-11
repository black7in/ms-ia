from datetime import datetime, timezone, timedelta

BOLIVIA_OFFSET = timedelta(hours=-4)


def ahora_bolivia() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None) + BOLIVIA_OFFSET


def iso_bolivia(dt: datetime | None = None) -> str:
    if dt is None:
        dt = ahora_bolivia()
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def hoy_bolivia_str() -> str:
    return ahora_bolivia().strftime("%Y-%m-%d")
