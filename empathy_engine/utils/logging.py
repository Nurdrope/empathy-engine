"""
Logging helpers with optional structlog/loguru support.
"""

from __future__ import annotations

from typing import Any


def get_logger(name: str) -> Any:
    """
    Return a logger compatible with .debug/.info/.warning/.error.

    Prefers structlog, falls back to loguru, then stdlib logging.
    """
    try:
        import structlog

        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(),
            processors=[structlog.processors.JSONRenderer()]
        )
        return structlog.get_logger(name)
    except Exception:
        try:
            from loguru import logger as loguru_logger

            return loguru_logger.bind(component=name)
        except Exception:
            import logging

            logger = logging.getLogger(name)
            if not logger.handlers:
                logging.basicConfig(level=logging.INFO)
            return logger
