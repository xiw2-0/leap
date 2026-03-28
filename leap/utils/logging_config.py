import logging
import logging.handlers
import time
from pathlib import Path
from leap.config import settings
from typing import Optional


class MillisecondFormatter(logging.Formatter):
    """Custom formatter to include milliseconds in log timestamps."""

    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None):
        """Override formatTime to include milliseconds."""
        ct = self.converter(record.created)
        if datefmt:
            s = time.strftime(datefmt, ct)
        else:
            s = time.strftime("%Y-%m-%d %H:%M:%S", ct)
        # Add milliseconds (3 digits, zero-padded) from record.msecs
        return f"{s}.{int(record.msecs):03d}"


def setup_logging():
    """Configure logging for the entire application."""

    log_format = MillisecondFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(thread)d | %(name)s:%(lineno)d | %(message)s"
    )

    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(exist_ok=True)

    rotating_file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_dir / "leap.log",
        when="D",
        interval=1,
        backupCount=7,
        encoding="utf-8",
        utc=False,
        atTime=None
    )
    rotating_file_handler.setFormatter(log_format)
    rotating_file_handler.setLevel(
        getattr(logging, settings.LOG_LEVEL.upper()))

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root_logger.addHandler(rotating_file_handler)

    # Configure FastAPI and related component logging
    # FastAPI uses uvicorn for serving, so we need to configure both
    fastapi_log_level = getattr(logging, settings.LOG_LEVEL.upper())

    # Get the specific loggers and configure them
    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.setLevel(fastapi_log_level)
    fastapi_logger.addHandler(rotating_file_handler)
    fastapi_logger.propagate = False  # Prevent duplicate logs from root logger

    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(fastapi_log_level)
    uvicorn_logger.addHandler(rotating_file_handler)
    uvicorn_logger.propagate = False

    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(fastapi_log_level)
    uvicorn_access_logger.addHandler(rotating_file_handler)
    uvicorn_access_logger.propagate = False

    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.setLevel(fastapi_log_level)
    uvicorn_error_logger.addHandler(rotating_file_handler)
    uvicorn_error_logger.propagate = False

    # Reduce noise from other third-party libraries
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
