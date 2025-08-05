from datetime import datetime, timezone



def now() -> datetime:
    """Reemplazo directo para datetime.utcnow() deprecado."""
    return datetime.now(timezone.utc)


