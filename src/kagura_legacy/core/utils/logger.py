import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class CustomFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: "\033[0;36m{}\033[0m",  # Cyan
        logging.INFO: "\033[0;32m{}\033[0m",  # Green
        logging.WARNING: "\033[0;33m{}\033[0m",  # Yellow
        logging.ERROR: "\033[0;31m{}\033[0m",  # Red
        logging.CRITICAL: "\033[0;35m{}\033[0m",  # Magenta
    }

    def format(self, record: logging.LogRecord) -> str:
        log_message = super().format(record)

        if os.getenv("ENVIRONMENT") == "production":
            return log_message

        color_format = self.FORMATS.get(record.levelno)
        if color_format is None:
            return log_message
        return color_format.format(log_message)


class Logger:
    _instance = None
    _initialized = False
    _loggers = {}

    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        if name is None:
            name = "app"

        if name not in cls._loggers:
            cls._loggers[name] = cls._initialize_logger(name)

        return cls._loggers[name]

    @staticmethod
    def _initialize_logger(name: Optional[str] = None) -> logging.Logger:
        if name is None:
            name = "app"

        logger = logging.Logger(name)

        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        logger.setLevel(getattr(logging, log_level))

        if logger.hasHandlers():
            logger.handlers.clear()

        log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
        formatter = CustomFormatter(log_format)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if os.getenv("ENVIRONMENT") == "production":
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

            current_date = datetime.now().strftime("%Y-%m-%d")
            log_file = log_dir / f"{current_date}.log"

            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=30,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    @staticmethod
    def set_log_level(level: str) -> None:
        logger = Logger.get_logger()
        logger.setLevel(getattr(logging, level.upper()))


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return Logger.get_logger(name)
