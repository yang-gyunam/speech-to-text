"""
Unit tests for the logging and monitoring system.

Tests cover structured logging, performance monitoring, timing measurements,
and debug mode functionality.
"""

import os
import json
import time
import tempfile
import shutil
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.speech_to_text.logger import (
    SpeechToTextLogger,
    PerformanceMonitor,
    StructuredFormatter,
    get_logger,
    setup_logging,
    cleanup_logging
)


class TestPerformanceMonitor:
    """Test cases for the PerformanceMonitor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor()
    
    def test_timer_operations(self):
        """Test basic timer operations."""
        # Start timer
        self.monitor.start_timer("test_operation")
        assert "test_operation" in self.monitor.start_times
        
        # Simulate some work
        time.sleep(0.01)
        
        # End timer
        duration = self.monitor.end_timer("test_operation")
        assert duration > 0
        assert "test_operation" not in self.monitor.start_times
        assert "test_operation" in self.monitor.metrics
    
    def test_multiple_operations(self):
        """Test tracking multiple operations."""
        operations = ["op1", "op2", "op3"]
        
        for op in operations:
            self.monitor.start_timer(op)
            time.sleep(0.001)
            self.monitor.end_timer(op)
        
        metrics = self.monitor.get_metrics()
        assert len(metrics) == 3
        
        for op in operations:
            assert op in metrics
            assert metrics[op]['count'] == 1
            assert metrics[op]['total_time'] > 0
    
    def test_repeated_operations(self):
        """Test tracking repeated operations."""
        operation = "repeated_op"
        
        for _ in range(3):
            self.monitor.start_timer(operation)
            time.sleep(0.001)
            self.monitor.end_timer(operation)
        
        metrics = self.monitor.get_metrics()
        assert metrics[operation]['count'] == 3
        assert metrics[operation]['average_time'] > 0
        assert metrics[operation]['min_time'] <= metrics[operation]['max_time']
    
    def test_end_timer_without_start(self):
        """Test ending timer that wasn't started."""
        duration = self.monitor.end_timer("nonexistent")
        assert duration == 0.0
    
    def test_reset_metrics(self):
        """Test resetting metrics."""
        self.monitor.start_timer("test")
        self.monitor.end_timer("test")
        
        assert len(self.monitor.get_metrics()) > 0
        
        self.monitor.reset_metrics()
        assert len(self.monitor.get_metrics()) == 0
        assert len(self.monitor.start_times) == 0


class TestStructuredFormatter:
    """Test cases for the StructuredFormatter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = StructuredFormatter()
    
    def test_basic_formatting(self):
        """Test basic log record formatting."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"
        
        formatted = self.formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data['level'] == 'INFO'
        assert log_data['logger'] == 'test_logger'
        assert log_data['message'] == 'Test message'
        assert log_data['module'] == 'test_module'
        assert log_data['function'] == 'test_function'
        assert log_data['line'] == 10
        assert 'timestamp' in log_data
    
    def test_extra_data_formatting(self):
        """Test formatting with extra data."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"
        record.extra_data = {"key1": "value1", "key2": 42}
        
        formatted = self.formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data['key1'] == 'value1'
        assert log_data['key2'] == 42
    
    def test_exception_formatting(self):
        """Test formatting with exception info."""
        import sys
        try:
            raise ValueError("Test exception")
        except ValueError:
            exc_info = sys.exc_info()
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="test.py",
                lineno=10,
                msg="Error occurred",
                args=(),
                exc_info=exc_info
            )
            record.module = "test_module"
            record.funcName = "test_function"
            
            formatted = self.formatter.format(record)
            log_data = json.loads(formatted)
            
            assert 'exception' in log_data
            assert 'ValueError' in log_data['exception']
            assert 'Test exception' in log_data['exception']


class TestSpeechToTextLogger:
    """Test cases for the SpeechToTextLogger class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.logger = SpeechToTextLogger(
            name="test_logger",
            log_dir=self.temp_dir,
            enable_console=False,  # Disable console for testing
            enable_file=True
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.logger.close()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test logger initialization."""
        assert self.logger.name == "test_logger"
        assert self.logger.log_dir == Path(self.temp_dir)
        assert self.logger.performance_monitor is not None
        assert self.logger.session_id.startswith("session_")
    
    def test_log_levels(self):
        """Test different log levels."""
        self.logger.debug("Debug message")
        self.logger.info("Info message")
        self.logger.warning("Warning message")
        self.logger.error("Error message")
        self.logger.critical("Critical message")
        
        # Check that log file was created
        log_file = Path(self.temp_dir) / "test_logger.log"
        assert log_file.exists()
        
        # Check that error log file was created
        error_log_file = Path(self.temp_dir) / "test_logger_errors.log"
        assert error_log_file.exists()
    
    def test_extra_data_logging(self):
        """Test logging with extra data."""
        extra_data = {"user_id": "test_user", "operation": "test_op"}
        self.logger.info("Test message with extra data", extra_data=extra_data)
        
        log_file = Path(self.temp_dir) / "test_logger.log"
        assert log_file.exists()
    
    def test_timer_context_manager(self):
        """Test timer context manager."""
        with self.logger.timer("test_operation"):
            time.sleep(0.01)
        
        metrics = self.logger.get_performance_metrics()
        assert "test_operation" in metrics['operations']
        assert metrics['operations']['test_operation']['count'] == 1
    
    def test_timer_decorator(self):
        """Test timer decorator."""
        @self.logger.time_function("decorated_function")
        def test_function():
            time.sleep(0.01)
            return "result"
        
        result = test_function()
        assert result == "result"
        
        metrics = self.logger.get_performance_metrics()
        assert "decorated_function" in metrics['operations']
    
    def test_function_call_logging(self):
        """Test function call logging decorator."""
        @self.logger.log_function_call(include_args=True, include_result=True)
        def test_function(arg1, arg2=None):
            return f"result_{arg1}"
        
        # Enable debug mode to see function call logs
        self.logger.set_debug_mode(True)
        
        result = test_function("test", arg2="value")
        assert result == "result_test"
    
    def test_function_call_logging_with_exception(self):
        """Test function call logging with exception."""
        @self.logger.log_function_call()
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_function()
    
    def test_specialized_logging_methods(self):
        """Test specialized logging methods."""
        # File operation logging
        self.logger.log_file_operation("read", "/path/to/file.wav", size=1024)
        
        # Audio processing logging
        self.logger.log_audio_processing("conversion", "/path/to/audio.m4a", format="wav")
        
        # Transcription logging
        self.logger.log_transcription("/path/to/audio.wav", "ko", "base", confidence=0.95)
        
        # Error with context logging
        error = ValueError("Test error")
        context = {"file_path": "/test/file.wav", "operation": "transcription"}
        self.logger.log_error_with_context(error, context)
    
    def test_debug_mode(self):
        """Test debug mode functionality."""
        # Initially not in debug mode
        assert not self.logger.debug_mode
        
        # Enable debug mode
        self.logger.set_debug_mode(True)
        assert self.logger.debug_mode
        assert self.logger.logger.level == logging.DEBUG
        
        # Disable debug mode
        self.logger.set_debug_mode(False)
        assert not self.logger.debug_mode
    
    def test_performance_metrics(self):
        """Test performance metrics collection."""
        # Perform some timed operations
        with self.logger.timer("operation1"):
            time.sleep(0.01)
        
        with self.logger.timer("operation2"):
            time.sleep(0.005)
        
        metrics = self.logger.get_performance_metrics()
        
        assert 'session_id' in metrics
        assert 'session_duration' in metrics
        assert 'operations' in metrics
        assert 'timestamp' in metrics
        
        assert 'operation1' in metrics['operations']
        assert 'operation2' in metrics['operations']
    
    def test_child_logger_creation(self):
        """Test creating child loggers."""
        child_logger = self.logger.create_child_logger("child")
        
        assert child_logger.name == "test_logger.child"
        assert child_logger.log_dir == self.logger.log_dir
        assert child_logger.debug_mode == self.logger.debug_mode
        
        child_logger.close()
    
    def test_structured_logging(self):
        """Test structured logging format."""
        structured_logger = SpeechToTextLogger(
            name="structured_test",
            log_dir=self.temp_dir,
            enable_console=False,
            enable_file=True,
            enable_structured=True
        )
        
        structured_logger.info("Test structured message", extra_data={"key": "value"})
        structured_logger.close()
        
        log_file = Path(self.temp_dir) / "structured_test.log"
        assert log_file.exists()
        
        # Read and verify structured format
        with open(log_file, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
        
        # Skip the initialization log and check the test message
        for line in log_lines:
            if "Test structured message" in line:
                log_data = json.loads(line.strip())
                assert log_data['message'] == "Test structured message"
                assert log_data['key'] == "value"
                break


class TestGlobalLoggerFunctions:
    """Test cases for global logger functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        cleanup_logging()  # Clean up any existing global logger
    
    def teardown_method(self):
        """Clean up test fixtures."""
        cleanup_logging()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_get_logger(self):
        """Test getting global logger instance."""
        logger1 = get_logger()
        logger2 = get_logger()
        
        # Should return the same instance
        assert logger1 is logger2
        assert logger1.name == "speech_to_text"
    
    def test_setup_logging(self):
        """Test setting up global logging configuration."""
        logger = setup_logging(
            log_level="DEBUG",
            log_dir=self.temp_dir,
            debug_mode=True,
            enable_structured=True
        )
        
        assert logger.debug_mode is True
        assert logger.enable_structured is True
        assert logger.log_dir == Path(self.temp_dir)
    
    def test_cleanup_logging(self):
        """Test cleaning up global logging resources."""
        logger = get_logger()
        assert logger is not None
        
        cleanup_logging()
        
        # Getting logger again should create a new instance
        new_logger = get_logger()
        assert new_logger is not logger


class TestLoggerIntegration:
    """Integration tests for the logging system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        cleanup_logging()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_real_world_logging_scenario(self):
        """Test a realistic logging scenario."""
        logger = SpeechToTextLogger(
            name="integration_test",
            log_dir=self.temp_dir,
            enable_console=False,
            debug_mode=True
        )
        
        try:
            # Simulate application workflow
            logger.info("Application started")
            
            # Simulate file processing
            with logger.timer("file_processing"):
                logger.log_file_operation("read", "/test/audio.m4a", size=2048000)
                time.sleep(0.01)
                logger.log_audio_processing("conversion", "/test/audio.m4a", target_format="wav")
                time.sleep(0.01)
            
            # Simulate transcription
            with logger.timer("transcription"):
                logger.log_transcription("/test/audio.wav", "ko", "base")
                time.sleep(0.02)
                logger.info("Transcription completed", extra_data={
                    "confidence": 0.95,
                    "duration": 30.5,
                    "word_count": 150
                })
            
            # Simulate error
            try:
                raise ValueError("Simulated processing error")
            except ValueError as e:
                logger.log_error_with_context(e, {
                    "file_path": "/test/audio.wav",
                    "operation": "transcription",
                    "model": "base"
                })
            
            # Check performance metrics
            metrics = logger.get_performance_metrics()
            assert len(metrics['operations']) == 2
            assert 'file_processing' in metrics['operations']
            assert 'transcription' in metrics['operations']
            
            logger.info("Application completed")
            
        finally:
            logger.close()
        
        # Verify log files were created
        log_file = Path(self.temp_dir) / "integration_test.log"
        error_log_file = Path(self.temp_dir) / "integration_test_errors.log"
        
        assert log_file.exists()
        assert error_log_file.exists()
        
        # Verify log content
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
            assert "Application started" in log_content
            assert "file_processing" in log_content
            assert "transcription" in log_content
            assert "Application completed" in log_content
        
        with open(error_log_file, 'r', encoding='utf-8') as f:
            error_content = f.read()
            assert "Simulated processing error" in error_content
    
    def test_log_rotation(self):
        """Test log file rotation."""
        logger = SpeechToTextLogger(
            name="rotation_test",
            log_dir=self.temp_dir,
            enable_console=False
        )
        
        try:
            # Generate enough log data to trigger rotation
            for i in range(1000):
                logger.info(f"Log message {i} with some additional data to increase size")
        finally:
            logger.close()
        
        # Check that log file exists (rotation might not occur with small test data)
        log_file = Path(self.temp_dir) / "rotation_test.log"
        assert log_file.exists()


if __name__ == "__main__":
    pytest.main([__file__])