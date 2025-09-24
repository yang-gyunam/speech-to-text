"""
Structured logging and monitoring system for the speech-to-text application.

This module provides comprehensive logging capabilities, performance monitoring,
timing measurements, and debug mode for troubleshooting.
"""

import os
import sys
import time
import logging
import logging.handlers
from typing import Dict, Any, Optional, Callable
from functools import wraps
from pathlib import Path
import json
from datetime import datetime
from contextlib import contextmanager


class PerformanceMonitor:
    """Monitor and track performance metrics."""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    def start_timer(self, operation: str) -> None:
        """Start timing an operation."""
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str) -> float:
        """End timing an operation and return duration."""
        if operation not in self.start_times:
            return 0.0
        
        duration = time.time() - self.start_times[operation]
        del self.start_times[operation]
        
        # Store metrics
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration)
        
        return duration
    
    def get_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics summary."""
        summary = {}
        for operation, durations in self.metrics.items():
            summary[operation] = {
                'count': len(durations),
                'total_time': sum(durations),
                'average_time': sum(durations) / len(durations),
                'min_time': min(durations),
                'max_time': max(durations)
            }
        return summary
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics.clear()
        self.start_times.clear()


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class SpeechToTextLogger:
    """
    Comprehensive logging system for the speech-to-text application.
    """
    
    def __init__(self, 
                 name: str = "speech_to_text",
                 log_level: str = "INFO",
                 log_dir: Optional[str] = None,
                 enable_console: bool = True,
                 enable_file: bool = True,
                 enable_structured: bool = False,
                 debug_mode: bool = False):
        """
        Initialize the logging system.
        
        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files (default: ./logs)
            enable_console: Enable console logging
            enable_file: Enable file logging
            enable_structured: Enable structured JSON logging
            debug_mode: Enable debug mode with verbose logging
        """
        self.name = name
        self.log_level = getattr(logging, log_level.upper())
        self.log_dir = Path(log_dir) if log_dir else Path("./logs")
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_structured = enable_structured
        self.debug_mode = debug_mode
        
        # Create performance monitor
        self.performance_monitor = PerformanceMonitor()
        
        # Setup logger
        self.logger = self._setup_logger()
        
        # Track session info
        self.session_start = time.time()
        self.session_id = f"session_{int(self.session_start)}"
        
        self.info("Logger initialized", extra_data={
            'session_id': self.session_id,
            'log_level': log_level,
            'debug_mode': debug_mode
        })
    
    def _setup_logger(self) -> logging.Logger:
        """Setup and configure the logger."""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create log directory if needed
        if self.enable_file:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            
            if self.enable_structured:
                console_handler.setFormatter(StructuredFormatter())
            else:
                console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                if self.debug_mode:
                    console_format = '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
                console_handler.setFormatter(logging.Formatter(console_format))
            
            logger.addHandler(console_handler)
        
        # File handler
        if self.enable_file:
            log_file = self.log_dir / f"{self.name}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
            )
            file_handler.setLevel(self.log_level)
            
            if self.enable_structured:
                file_handler.setFormatter(StructuredFormatter())
            else:
                file_format = '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
                file_handler.setFormatter(logging.Formatter(file_format))
            
            logger.addHandler(file_handler)
        
        # Error file handler (always enabled if file logging is enabled)
        if self.enable_file:
            error_file = self.log_dir / f"{self.name}_errors.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            
            error_format = '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
            error_handler.setFormatter(logging.Formatter(error_format))
            
            logger.addHandler(error_handler)
        
        return logger
    
    def debug(self, message: str, extra_data: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, extra_data)
    
    def info(self, message: str, extra_data: Optional[Dict[str, Any]] = None) -> None:
        """Log info message."""
        self._log(logging.INFO, message, extra_data)
    
    def warning(self, message: str, extra_data: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, extra_data)
    
    def error(self, message: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = False) -> None:
        """Log error message."""
        self._log(logging.ERROR, message, extra_data, exc_info)
    
    def critical(self, message: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = False) -> None:
        """Log critical message."""
        self._log(logging.CRITICAL, message, extra_data, exc_info)
    
    def _log(self, level: int, message: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = False) -> None:
        """Internal logging method."""
        if extra_data:
            # Create a LogRecord with extra data
            import sys
            exc_info_tuple = sys.exc_info() if exc_info else None
            record = self.logger.makeRecord(
                self.logger.name, level, "", 0, message, (), exc_info_tuple
            )
            record.extra_data = extra_data
            self.logger.handle(record)
        else:
            self.logger.log(level, message, exc_info=exc_info)
    
    @contextmanager
    def timer(self, operation: str, log_result: bool = True):
        """Context manager for timing operations."""
        self.performance_monitor.start_timer(operation)
        start_time = time.time()
        
        try:
            if self.debug_mode:
                self.debug(f"Starting operation: {operation}")
            yield
        finally:
            duration = self.performance_monitor.end_timer(operation)
            if log_result:
                self.info(f"Operation completed: {operation}", extra_data={
                    'operation': operation,
                    'duration_seconds': duration,
                    'session_id': self.session_id
                })
    
    def time_function(self, operation_name: Optional[str] = None):
        """Decorator for timing function execution."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                op_name = operation_name or f"{func.__module__}.{func.__name__}"
                with self.timer(op_name):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def log_function_call(self, include_args: bool = False, include_result: bool = False):
        """Decorator for logging function calls."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                func_name = f"{func.__module__}.{func.__name__}"
                
                log_data = {
                    'function': func_name,
                    'session_id': self.session_id
                }
                
                if include_args and self.debug_mode:
                    log_data['args'] = str(args)
                    log_data['kwargs'] = str(kwargs)
                
                self.debug(f"Calling function: {func_name}", extra_data=log_data)
                
                try:
                    result = func(*args, **kwargs)
                    
                    if include_result and self.debug_mode:
                        log_data['result'] = str(result)[:200]  # Limit result length
                    
                    self.debug(f"Function completed: {func_name}", extra_data=log_data)
                    return result
                    
                except Exception as e:
                    log_data['error'] = str(e)
                    self.error(f"Function failed: {func_name}", extra_data=log_data, exc_info=True)
                    raise
                    
            return wrapper
        return decorator
    
    def log_file_operation(self, operation: str, file_path: str, **kwargs) -> None:
        """Log file operations with standardized format."""
        self.info(f"File operation: {operation}", extra_data={
            'operation': operation,
            'file_path': file_path,
            'session_id': self.session_id,
            **kwargs
        })
    
    def log_audio_processing(self, operation: str, file_path: str, **kwargs) -> None:
        """Log audio processing operations."""
        self.info(f"Audio processing: {operation}", extra_data={
            'operation': operation,
            'file_path': file_path,
            'session_id': self.session_id,
            **kwargs
        })
    
    def log_transcription(self, file_path: str, language: str, model: str, **kwargs) -> None:
        """Log transcription operations."""
        self.info("Transcription started", extra_data={
            'operation': 'transcription',
            'file_path': file_path,
            'language': language,
            'model': model,
            'session_id': self.session_id,
            **kwargs
        })
    
    def log_error_with_context(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log error with detailed context information."""
        self.error(f"Error occurred: {type(error).__name__}", extra_data={
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'session_id': self.session_id
        }, exc_info=True)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        metrics = self.performance_monitor.get_metrics()
        session_duration = time.time() - self.session_start
        
        return {
            'session_id': self.session_id,
            'session_duration': session_duration,
            'operations': metrics,
            'timestamp': datetime.now().isoformat()
        }
    
    def log_performance_summary(self) -> None:
        """Log performance summary."""
        metrics = self.get_performance_metrics()
        self.info("Performance summary", extra_data=metrics)
    
    def set_debug_mode(self, enabled: bool) -> None:
        """Enable or disable debug mode."""
        self.debug_mode = enabled
        if enabled:
            self.logger.setLevel(logging.DEBUG)
            self.info("Debug mode enabled")
        else:
            self.logger.setLevel(self.log_level)
            self.info("Debug mode disabled")
    
    def create_child_logger(self, name: str) -> 'SpeechToTextLogger':
        """Create a child logger with the same configuration."""
        child_name = f"{self.name}.{name}"
        return SpeechToTextLogger(
            name=child_name,
            log_level=logging.getLevelName(self.log_level),
            log_dir=str(self.log_dir),
            enable_console=self.enable_console,
            enable_file=self.enable_file,
            enable_structured=self.enable_structured,
            debug_mode=self.debug_mode
        )
    
    def close(self) -> None:
        """Close logger and cleanup resources."""
        self.log_performance_summary()
        self.info("Logger shutting down", extra_data={
            'session_id': self.session_id,
            'session_duration': time.time() - self.session_start
        })
        
        # Close all handlers
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)


# Global logger instance
_global_logger: Optional[SpeechToTextLogger] = None


def get_logger(name: str = "speech_to_text") -> SpeechToTextLogger:
    """Get or create global logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = SpeechToTextLogger(name=name)
    return _global_logger


def setup_logging(log_level: str = "INFO", 
                 log_dir: Optional[str] = None,
                 debug_mode: bool = False,
                 enable_structured: bool = False) -> SpeechToTextLogger:
    """Setup global logging configuration."""
    global _global_logger
    _global_logger = SpeechToTextLogger(
        log_level=log_level,
        log_dir=log_dir,
        debug_mode=debug_mode,
        enable_structured=enable_structured
    )
    return _global_logger


def cleanup_logging() -> None:
    """Cleanup global logging resources."""
    global _global_logger
    if _global_logger:
        _global_logger.close()
        _global_logger = None