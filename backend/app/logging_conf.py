import logging
import sys

class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Ensure request_id always exists
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True

def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | req=%(request_id)s | %(message)s"
    )
    handler.setFormatter(formatter)

    # 🔑 Attach filter HERE (global)
    handler.addFilter(RequestIdFilter())

    root.handlers.clear()
    root.addHandler(handler)
