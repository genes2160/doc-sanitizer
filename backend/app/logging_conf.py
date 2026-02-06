import logging
import sys

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | req=%(request_id)s | %(message)s"
    )
    handler.setFormatter(fmt)

    logger.handlers.clear()
    logger.addHandler(handler)
