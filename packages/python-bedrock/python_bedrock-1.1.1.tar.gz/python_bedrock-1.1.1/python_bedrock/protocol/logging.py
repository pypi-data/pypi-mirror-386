"""Protocol logging and debugging support."""
import logging
import sys
import time
from typing import Optional, Dict, Any
from contextlib import contextmanager
from dataclasses import dataclass
from threading import local

@dataclass
class LogContext:
    """Thread-local logging context information."""
    connection_id: Optional[str] = None
    protocol_version: Optional[int] = None
    peer_info: Optional[str] = None
    is_client: bool = True

class ProtocolLogFormatter(logging.Formatter):
    """Custom formatter for protocol logs with context."""
    
    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None
    ) -> None:
        if not fmt:
            fmt = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] '
            fmt += '[%(context_info)s] %(message)s'
        super().__init__(fmt, datefmt)
        
        # Thread-local storage for context
        self.context = local()
        self.context.data = LogContext()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with context information."""
        # Add context info
        context = getattr(self.context, 'data', LogContext())
        context_parts = []
        
        if context.connection_id:
            context_parts.append(f"conn={context.connection_id}")
        if context.protocol_version:
            context_parts.append(f"ver={context.protocol_version}")
        if context.peer_info:
            context_parts.append(f"peer={context.peer_info}")
        if context.is_client is not None:
            context_parts.append("client" if context.is_client else "server")
        
        record.context_info = ' '.join(context_parts) if context_parts else '-'
        
        # Add timing info for performance logging
        if hasattr(record, 'duration'):
            record.message = f"{record.message} (took {record.duration:.3f}s)"
        
        return super().format(record)
    
    @contextmanager
    def connection_context(
        self,
        connection_id: Optional[str] = None,
        protocol_version: Optional[int] = None,
        peer_info: Optional[str] = None,
        is_client: Optional[bool] = None
    ):
        """Context manager for connection-specific logging."""
        old_context = getattr(self.context, 'data', LogContext())
        try:
            new_context = LogContext(
                connection_id=connection_id or old_context.connection_id,
                protocol_version=protocol_version or old_context.protocol_version,
                peer_info=peer_info or old_context.peer_info,
                is_client=is_client if is_client is not None else old_context.is_client
            )
            self.context.data = new_context
            yield
        finally:
            self.context.data = old_context

class ProtocolLogger:
    """Protocol-specific logger with performance tracking."""
    
    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
        handler: Optional[logging.Handler] = None,
        formatter: Optional[ProtocolLogFormatter] = None
    ) -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        if handler is None:
            handler = logging.StreamHandler(sys.stdout)
        if formatter is None:
            formatter = ProtocolLogFormatter()
            
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        self.formatter = formatter
        self._timers: Dict[str, float] = {}
    
    def set_context(
        self,
        connection_id: Optional[str] = None,
        protocol_version: Optional[int] = None,
        peer_info: Optional[str] = None,
        is_client: Optional[bool] = None
    ) -> None:
        """Set the current logging context."""
        self.formatter.context.data = LogContext(
            connection_id=connection_id,
            protocol_version=protocol_version,
            peer_info=peer_info,
            is_client=is_client
        )
    
    @contextmanager
    def connection_context(self, **kwargs: Any):
        """Context manager for connection-specific logging."""
        with self.formatter.connection_context(**kwargs):
            yield
    
    def start_timer(self, name: str) -> None:
        """Start a named performance timer."""
        self._timers[name] = time.time()
    
    def stop_timer(self, name: str) -> Optional[float]:
        """Stop a named timer and return duration."""
        start_time = self._timers.pop(name, None)
        if start_time is None:
            return None
        return time.time() - start_time
    
    @contextmanager
    def timer(self, operation: str):
        """Context manager for timing operations."""
        timer_name = f"op_{operation}_{time.time()}"
        self.start_timer(timer_name)
        try:
            yield
        finally:
            duration = self.stop_timer(timer_name)
            if duration is not None:
                self.performance(operation, duration)
    
    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        self.logger.critical(msg, *args, **kwargs)
    
    def performance(self, operation: str, duration: float) -> None:
        """Log a performance metric."""
        record = logging.LogRecord(
            name=self.logger.name,
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg=f"Operation {operation} completed",
            args=(),
            exc_info=None
        )
        record.duration = duration
        self.logger.handle(record)

# Global logger instance
protocol_logger = ProtocolLogger('bedrock.protocol')