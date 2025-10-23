"""Logging configuration and utilities for the protocol library."""
import logging
import sys
from typing import Optional, Dict, Any
from pathlib import Path

# Create the base logger
logger = logging.getLogger("python_protocol_test")

class ProtocolLogFormatter(logging.Formatter):
    """Custom formatter with connection context."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Add connection info if available
        if hasattr(record, 'conn_id'):
            record.msg = f"[Conn {record.conn_id}] {record.msg}"
        return super().format(record)

def configure_logging(
    level: int = logging.INFO,
    logFile: Optional[Path] = None,
    formatStr: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
) -> None:
    """Configure protocol logging.
    
    Args:
        level: Logging level (default: INFO)
        logFile: Optional path to log file
        formatStr: Log message format string
    """
    # Create formatter
    formatter = ProtocolLogFormatter(formatStr)
    
    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # File handler if requested
    if logFile:
        file_handler = logging.FileHandler(logFile)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    logger.setLevel(level)

class LogContext:
    """Context manager for adding connection info to logs."""
    
    def __init__(self, **context: Any):
        self.context = context
        self.old_context: Dict[str, Any] = {}
    
    def __enter__(self) -> 'LogContext':
        # Save old context and set new
        for k, v in self.context.items():
            if hasattr(logger, k):
                self.old_context[k] = getattr(logger, k)
            setattr(logger, k, v)
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        # Restore old context
        for k, v in self.old_context.items():
            setattr(logger, k, v)
        # Remove any new attributes
        for k in self.context:
            if k not in self.old_context:
                delattr(logger, k)

def log_connection(conn_id: str) -> LogContext:
    """Create a log context for a connection."""
    return LogContext(conn_id=conn_id)