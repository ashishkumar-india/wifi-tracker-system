"""
Structured logging utilities.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import json

from app.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        msg = f"{color}[{timestamp}] [{record.levelname}]{reset} {record.name}: {record.getMessage()}"
        if record.exc_info:
            msg += f"\n{self.formatException(record.exc_info)}"
        return msg


def setup_logging(log_level=None, log_file=None, use_json=False):
    """Setup logging configuration."""
    level = getattr(logging, (log_level or settings.LOG_LEVEL).upper())
    log_file = log_file or settings.LOG_FILE
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColoredFormatter())
    root_logger.addHandler(console_handler)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    if use_json:
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(file_handler)
    
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)


def get_logger(name):
    """Get a logger instance."""
    return logging.getLogger(name)
