import logging
import sys
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler


def get_config_value(*keys, default=None):
    """Lazy import to avoid circular dependency"""
    from app.config.config_loader import get_config_value as _get_config_value

    return _get_config_value(*keys, default=default)


class OWASPFormatter(logging.Formatter):

    def __init__(self, fmt=None, datefmt=None):
        """Initialize the OWASP formatter."""
        if fmt is None:
            fmt = (
                "%(asctime)s - %(name)s - %(levelname)s - "
                "[WHO: %(user)s] [WHAT: %(action)s] "
                "[WHEN: %(timestamp)s] [WHERE: %(location)s] - "
                "%(message)s"
            )
        if datefmt is None:
            datefmt = "%Y-%m-%d %H:%M:%S"

        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:

        if not hasattr(record, "user"):
            record.user = "system"
        if not hasattr(record, "action"):
            record.action = record.funcName or "unknown"
        if not hasattr(record, "timestamp"):
            record.timestamp = datetime.now(timezone.utc).isoformat()
        if not hasattr(record, "location"):
            record.location = (
                f"{record.module}.{record.funcName}"
                if record.funcName
                else record.module
            )

        return super().format(record)


class LoggerConfig:

    DEFAULT_LOG_LEVEL = logging.INFO
    DEFAULT_LOG_FORMAT = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "[WHO: %(user)s] [WHAT: %(action)s] "
        "[WHEN: %(timestamp)s] [WHERE: %(location)s] - "
        "%(message)s"
    )
    DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    # File logging configuration - use None and lazy load to avoid circular import at module level
    LOG_DIR = None
    LOG_FILE = None
    MAX_BYTES = None
    BACKUP_COUNT = None

    _loggers: Dict[str, logging.Logger] = {}
    _configured = False

    @classmethod
    def _init_config_values(cls):
        """Initialize config values from config.json if not already set"""
        if cls.LOG_DIR is None:
            cls.LOG_DIR = get_config_value("logging", "dir", default="logs")
        if cls.LOG_FILE is None:
            cls.LOG_FILE = get_config_value(
                "logging", "file", default="whatsapp-automation.log"
            )
        if cls.MAX_BYTES is None:
            cls.MAX_BYTES = get_config_value(
                "logging", "max_bytes", default=10 * 1024 * 1024
            )
        if cls.BACKUP_COUNT is None:
            cls.BACKUP_COUNT = get_config_value("logging", "backup_count", default=5)

    @classmethod
    def setup(
        cls,
        log_level: Optional[int] = None,
        enable_file_logging: bool = True,
        enable_console_logging: bool = True,
        log_dir: Optional[str] = None,
        log_file: Optional[str] = None,
    ) -> None:

        if cls._configured:
            return

        # Initialize config values from config.json
        cls._init_config_values()

        # Determine log level from config or parameter
        if log_level is None:
            log_level_str = get_config_value("logging", "level", default="INFO").upper()
            log_level = getattr(logging, log_level_str, cls.DEFAULT_LOG_LEVEL)

        # Update class variables if provided
        if log_dir:
            cls.LOG_DIR = log_dir
        if log_file:
            cls.LOG_FILE = log_file

        # Create log directory if it doesn't exist
        if enable_file_logging and not os.path.exists(cls.LOG_DIR):
            os.makedirs(cls.LOG_DIR, exist_ok=True)

        cls._configured = True

    @classmethod
    def get_logger(
        cls,
        name: str,
        log_level: Optional[int] = None,
        enable_file_logging: bool = True,
        enable_console_logging: bool = True,
    ) -> logging.Logger:

        if not cls._configured:
            cls.setup()

        if name in cls._loggers:
            return cls._loggers[name]

        logger = logging.getLogger(name)

        if log_level is None:
            log_level_str = get_config_value("logging", "level", default="INFO").upper()
            log_level = getattr(logging, log_level_str, cls.DEFAULT_LOG_LEVEL)

        logger.setLevel(log_level)

        logger.handlers.clear()

        formatter = OWASPFormatter(
            fmt=cls.DEFAULT_LOG_FORMAT, datefmt=cls.DEFAULT_DATE_FORMAT
        )

        if enable_console_logging:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        if enable_file_logging:
            try:
                log_path = os.path.join(cls.LOG_DIR, cls.LOG_FILE)
                file_handler = RotatingFileHandler(
                    log_path, maxBytes=cls.MAX_BYTES, backupCount=cls.BACKUP_COUNT
                )
                file_handler.setLevel(log_level)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"Failed to setup file logging: {e}")

        logger.propagate = False

        cls._loggers[name] = logger

        return logger

    @classmethod
    def reset(cls) -> None:
        cls._loggers.clear()
        cls._configured = False


def get_logger(
    name: str,
    log_level: Optional[int] = None,
    enable_file_logging: bool = True,
    enable_console_logging: bool = True,
) -> logging.Logger:

    return LoggerConfig.get_logger(
        name=name,
        log_level=log_level,
        enable_file_logging=enable_file_logging,
        enable_console_logging=enable_console_logging,
    )


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    user: str = "system",
    action: str = "unknown",
    location: Optional[str] = None,
    **kwargs,
) -> None:

    timestamp = datetime.now(timezone.utc).isoformat()

    extra = {
        "user": user,
        "action": action,
        "timestamp": timestamp,
        "location": location or "unknown",
        **kwargs,
    }

    logger.log(level, message, extra=extra)


def create_owasp_log_context(
    user: str = "system", action: str = "unknown", location: Optional[str] = None
) -> Dict[str, Any]:

    return {
        "user": user,
        "action": action,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "location": location or "unknown",
    }


LoggerConfig.setup()
