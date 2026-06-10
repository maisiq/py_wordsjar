import datetime as dt
import logging
import sys

_logger: logging.Logger | None = None


class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[1;31m"  # Bold Red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord):
        color = self.COLORS.get(record.levelname, self.RESET)
        ts = dt.datetime.now(dt.UTC).strftime("%d-%m-%Y %H:%M:%S")
        message = super().format(record)
        return f"[{ts}] {color}{message}{self.RESET}"


def init(debug: bool):
    global _logger

    logger = logging.getLogger("main")

    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColorFormatter())
    console_handler.setLevel(level)

    logger.addHandler(console_handler)

    _logger = logger


def get_logger() -> logging.Logger:
    if _logger is None:
        raise RuntimeError("logger not initialized")
    return _logger