"""
Centralised logging configuration.
All modules should obtain loggers via get_logger(__name__).
"""

import logging

_LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger with the project-standard StreamHandler attached.
    Idempotent: calling twice for the same name does not duplicate handlers.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return logger
