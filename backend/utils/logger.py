"""
Structured logging module for SynkAI backend.
Configures stream handlers and formatters for consistent log formatting.
"""

import logging
import sys
from backend.config import settings


def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a named logger instance.

    Args:
        name (str): The name of the module invoking the logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        level = logging.DEBUG if settings.DEBUG else logging.INFO
        logger.setLevel(level)

        # Console Output Handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Standard log format
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
