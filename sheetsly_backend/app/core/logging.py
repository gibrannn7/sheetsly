"""Logging configuration with sensitive data masking."""

import logging
import re
import sys
from typing import Any
from .config import settings

# Sensitive key regex patterns to mask in logs
SENSITIVE_PATTERNS = [
    re.compile(r"(sk-[a-zA-Z0-9_\-\.]{10,})"),
    re.compile(r"(api[_\-]?key\s*[:=]\s*['\"]?)([^'\"\s]+)", re.IGNORECASE),
    re.compile(r"(password\s*[:=]\s*['\"]?)([^'\"\s]+)", re.IGNORECASE),
    re.compile(r"(token\s*[:=]\s*['\"]?)([^'\"\s]+)", re.IGNORECASE),
]


class SensitiveDataFilter(logging.Filter):
    """Filters log records to mask API keys and secrets."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.mask_sensitive(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.mask_sensitive(v) if isinstance(v, str) else v for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.mask_sensitive(arg) if isinstance(arg, str) else arg for arg in record.args)
        return True

    @staticmethod
    def mask_sensitive(text: str) -> str:
        masked = text
        for pattern in SENSITIVE_PATTERNS:
            masked = pattern.sub(r"***REDACTED***", masked)
        return masked


def setup_logger() -> logging.Logger:
    """Configures and returns the application logger."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    app_logger = logging.getLogger(settings.APP_NAME)
    app_logger.setLevel(log_level)

    # Avoid duplicate handlers
    if not app_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())
        app_logger.addHandler(handler)

    return app_logger


logger = setup_logger()
