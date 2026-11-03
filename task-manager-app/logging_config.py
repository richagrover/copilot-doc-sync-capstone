from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

LOGGER_NAME = "task_manager"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(
                timespec="milliseconds"
            ),
            "level": record.levelname,
            "event": getattr(record, "event", record.getMessage()),
            "user_id": getattr(record, "user_id", None),
            "detail": getattr(record, "detail", None),
        }
        return json.dumps(payload, ensure_ascii=False)


def configure() -> None:
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False


def log_event(event: str, *, user_id: int | None = None, detail: str | None = None) -> None:
    """Emit a structured event. Never pass passwords, hashes, or tokens."""
    logging.getLogger(LOGGER_NAME).info(
        event, extra={"event": event, "user_id": user_id, "detail": detail}
    )
