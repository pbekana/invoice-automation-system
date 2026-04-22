import logging
import sys
import json

class CustomJsonFormatter(logging.Formatter):
    """Simple JSON formatter for logging."""
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage()
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_logger(name="invoice_automation"):
    """Set up structured logging using standard library."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        # Fallback to simple format if jsonlogger is missing
        formatter = CustomJsonFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

logger = setup_logger()
