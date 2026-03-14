import logging
import logging.handlers
from pathlib import Path
from leap.config import settings


def setup_logging():
    """Configure logging for the entire application."""
    
    log_format = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
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
    rotating_file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root_logger.addHandler(rotating_file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)