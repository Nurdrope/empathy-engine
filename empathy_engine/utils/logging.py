"""
Logging helpers with optional structlog/loguru support.
"""

from __future__ import annotations

import logging as _stdlib_logging
from typing import Any


class _KwargsLoggerAdapter:
    """
    Wrap a stdlib logger so structlog-style calls work:
    logger.error("Something failed", error=str(e)) renders the kwargs
    as key=value pairs instead of raising TypeError.
    """

    def __init__(self, logger: _stdlib_logging.Logger):
        self._logger = logger

    @staticmethod
    def _format(msg: str, kwargs: dict) -> str:
        if not kwargs:
            return msg
        pairs = " ".join(f"{key}={value}" for key, value in kwargs.items())
        return f"{msg} {pairs}"

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.debug(self._format(msg, kwargs), *args)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.info(self._format(msg, kwargs), *args)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.warning(self._format(msg, kwargs), *args)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.error(self._format(msg, kwargs), *args)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._logger.exception(self._format(msg, kwargs), *args)


def get_logger(name: str) -> Any:
    """
    Return a logger compatible with .debug/.info/.warning/.error.

    Prefers structlog, falls back to loguru, then stdlib logging.
    All variants accept structlog-style keyword arguments.
    """
    try:
        import structlog

        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(
                _stdlib_logging.INFO
            ),
            processors=[structlog.processors.JSONRenderer()],
        )
        return structlog.get_logger(name)
    except Exception:
        try:
            from loguru import logger as loguru_logger

            return loguru_logger.bind(component=name)
        except Exception:
            logger = _stdlib_logging.getLogger(name)
            if not logger.handlers:
                _stdlib_logging.basicConfig(level=_stdlib_logging.INFO)
            return _KwargsLoggerAdapter(logger)
