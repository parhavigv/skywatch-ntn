import logging
import sys

def setup_logging() -> logging.Logger:
    logger = logging.getLogger("skywatch")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    ))
    if not logger.handlers:
        logger.addHandler(handler)
    return logger

logger = setup_logging()
