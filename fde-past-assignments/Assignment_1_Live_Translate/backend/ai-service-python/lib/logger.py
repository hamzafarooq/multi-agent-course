"""
lib/logger.py — structured JSON logging  (PROVIDED — you may extend)
====================================================================
Emits one JSON object per line to stdout AND to ai-service.log. Any keyword
you pass via `extra=` is merged into the line, so `log.info("translate",
extra={"cached": True, "latencyMs": 4})` becomes a greppable structured event.

    tail -f ai-service.log | grep translate
"""
import json
import logging
from datetime import datetime, timezone

LOG_FILE = "ai-service.log"
_RESERVED = set(logging.makeLogRecord({}).__dict__.keys()) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        for k, v in record.__dict__.items():
            if k not in _RESERVED and not k.startswith("_"):
                payload[k] = v
        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:  # already configured
        return logger
    logger.setLevel(logging.INFO)
    fmt = JsonFormatter()

    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
    logger.addHandler(stream)

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger
