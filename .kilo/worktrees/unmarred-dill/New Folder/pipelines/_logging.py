# pipelines/_logging.py
import logging, sys


def setup_logger(name: str = "mahoun", level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:  # idempotent
        return logger
    logger.setLevel(level)
    h = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    h.setFormatter(fmt)
    logger.addHandler(h)
    return logger
