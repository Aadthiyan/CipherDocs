"""
CyborgDB Logging Configuration
Structured logging with correlation ID tracking
"""

import logging
import sys
from typing import Optional
from contextvars import ContextVar
from datetime import datetime
from app.core.config import settings

# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class CorrelationIdFilter(logging.Filter):
    """
    Logging filter that adds correlation ID to log records
    """
    
    def filter(self, record):
        """Add correlation_id to log record"""
        record.correlation_id = correlation_id_var.get() or "N/A"
        return True


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for better readability in development
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        """Format log record with colors"""
        if settings.is_development():
            # Add color to level name
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logging():
    """
    Configure application logging
    
    Sets up:
    - Console handler with colored output (development)
    - File handler for persistent logs
    - Correlation ID filter for request tracking
    - Structured log format
    """
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Use colored formatter in development
    if settings.is_development():
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        console_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(CorrelationIdFilter())
    root_logger.addHandler(console_handler)
    
    # File handler (optional, for production)
    if not settings.is_development():
        try:
            import os
            os.makedirs("logs", exist_ok=True)
            
            file_handler = logging.FileHandler(
                f"logs/cyborgdb_{datetime.now().strftime('%Y%m%d')}.log"
            )
            file_handler.setLevel(logging.INFO)
            file_formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            file_handler.addFilter(CorrelationIdFilter())
            root_logger.addHandler(file_handler)
        except Exception as e:
            root_logger.warning(f"Failed to set up file logging: {e}")
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_correlation_id(correlation_id: str):
    """
    Set correlation ID for current context
    
    Args:
        correlation_id: Unique request identifier
    """
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """
    Get correlation ID from current context
    
    Returns:
        Correlation ID or None
    """
    return correlation_id_var.get()
