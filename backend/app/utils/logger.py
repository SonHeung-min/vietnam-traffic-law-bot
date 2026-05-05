import logging
import sys


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Force UTF-8 để hiển thị tiếng Việt trên Windows
        stream = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
        handler = logging.StreamHandler(stream)
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
