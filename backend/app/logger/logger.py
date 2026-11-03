"""Application logging.

Two output modes:

* ``json`` — one JSON object per line, ready for a log collector (production);
* ``console`` — the coloured output that is pleasant to read locally.

The request id lives in a :mod:`contextvars` variable, so every log record
written while handling a request carries it without threading a logger through
the call chain.
"""

import contextvars
import datetime as dt
import json
import logging
import sys
import typing

_request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

LOGGER_NAME = "main"

#: Attributes that ``logging`` itself puts on every record; anything else that a
#: caller passed through ``extra=`` is copied into the JSON payload.
_RESERVED_FIELDS = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "request_id",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
    }
)


def set_request_id(value: str) -> contextvars.Token:
    return _request_id.set(value)


def get_request_id() -> str:
    return _request_id.get()


def reset_request_id(token: contextvars.Token) -> None:
    _request_id.reset(token)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, typing.Any] = {
            "ts": dt.datetime.fromtimestamp(record.created, dt.UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        for field, value in record.__dict__.items():
            if field not in _RESERVED_FIELDS and not field.startswith("_"):
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


class ConsoleFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[1;31m",  # Bold Red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        ts = dt.datetime.fromtimestamp(record.created, dt.UTC).strftime("%d-%m-%Y %H:%M:%S")
        message = super().format(record)
        extras = " ".join(
            f"{field}={value}"
            for field, value in record.__dict__.items()
            if field not in _RESERVED_FIELDS and not field.startswith("_") and value is not None
        )
        if extras:
            message = f"{message} {extras}"
        request_id = getattr(record, "request_id", "-")
        return f"[{ts}] [{request_id}] {color}{message}{self.RESET}"


_logger: logging.Logger | None = None


def init(debug: bool, json_logs: bool = True) -> None:
    global _logger

    logger = logging.getLogger(LOGGER_NAME)

    # A second call (tests, reload, several app factories in one process) must
    # not duplicate every record.
    logger.handlers.clear()
    logger.propagate = False

    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(JsonFormatter() if json_logs else ConsoleFormatter())

    logger.addHandler(handler)

    _logger = logger


def get_logger() -> logging.Logger:
    if _logger is None:
        raise RuntimeError("logger is not initialized")
    return _logger