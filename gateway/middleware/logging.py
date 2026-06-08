import logging
import sys
import os
import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

_request_id_ctx: dict = {}

# Patch LogRecord factory so %(rid)s always has a fallback
_old_factory = logging.getLogRecordFactory()


def _record_factory(*args, **kwargs):
    record = _old_factory(*args, **kwargs)
    if not hasattr(record, "rid") or not record.rid:
        record.rid = _request_id_ctx.get("rid", "-")
    return record


logging.setLogRecordFactory(_record_factory)


def setup_logging(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, level, logging.INFO))

    fmt = os.getenv("LOG_FORMAT", "json")
    if fmt == "json":
        formatter = logging.Formatter(
            '{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s",'
            '"msg":"%(message)s","rid":"%(rid)s"}',
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s rid=%(rid)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-ID", uuid.uuid4().hex[:16])
        request.state.request_id = rid
        _request_id_ctx["rid"] = rid

        start = time.time()
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        response.headers["X-Response-Time"] = f"{(time.time() - start) * 1000:.0f}ms"
        return response
