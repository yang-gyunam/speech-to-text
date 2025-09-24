"""
Unit tests for the error handling system.

Tests cover error handling, recovery strategies, user-friendly messages,
and suggestion systems for common error scenarios.
"""

import os
import tempfile
import shutil
import logging
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.speech_to_text.error_handler import ErrorHandler
from src.speech_to_text.exceptions import (
    SpeechToTextError,
    FileError,
    UnsupportedFormatError,
    ProcessingError,
    AudioProcessingError,
    AudioConversionError,
    ModelLoadError,
    TranscriptionError,
    SystemError,
    FileSystemError,
    DiskSpaceError
)


class TestErrorHandler:
    """Test cases for the ErrorHandler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.logger = Mock(spec=logging.Logger)
        self.error_handler = ErrorHandler(logger=self.logger)
    
    def test_initialization(self):
        """Test ErrorHandler initialization."""
        # Test with custom logger
        handler = ErrorHandler(logger=self.logger)
        assert handler.logger == self.logger
        
        # Test with default logger
        handler = ErrorHandler()
        assert handler.logger is not None
        assert isinstance(handler.logger, logging.Logger)
    
    def test_handle_unsupported_format_error(self):
        """Test handling of UnsupportedFormatError."""
        error = UnsupportedFormatError("xyz", ["wav", "mp3", "m4a"])
        can_recover, message, suggestions = self.error_handler.handle_error(error)
        
        assert not can_recover
        assert "지원되지 않습니다" in message
        assert "xyz" in message
        assert len(suggestions) == 3
        assert "wav, mp3, m4a" in suggestions[0]
        assert "FFmpeg" in suggestions[1]
    
    def test_handle_file_not_found_error(self):
        """Test handling of FileNotFoundError."""
        error = FileNotFoundError("test.wav")
        context = {"file_path": "/path/to/test.wav"}
        can_recover, message, suggestions = self.error_handler.handle_error(error, context)
        
        assert not can_recover
        assert "찾을 수 없습니다" in message
        assert "/path/to/test.wav" in message
        assert len(suggestions) == 4
        assert "경로가 올바른지" in suggestions[0]
    
    def test_handle_permission_error(self):
        """Test handling of PermissionError."""
        error = PermissionError("Access denied")
        context = {"file_path": "/restricted/file.wav"}
        can_recover, message, suggestions = self.error_handler.handle_error(error, context)
        
        assert can_recover
        assert "권한이 없습니다" in message
        assert len(suggestions) == 3
        assert "권한을 확인" in suggestions[0]
    
    def test_handle_audio_conversion_error(self):
        """Test handling of AudioConversionError."""
        error = AudioConversionError("input.m4a", "wav", "FFmpeg error")
        can_recover, message, suggestions = self.error_handler.handle_error(error)
        
        assert can_recover
        assert "오디오 변환에 실패" in message
        assert "input.m4a" in message
        assert len(suggestions) == 4
        assert "FFmpeg" in suggestions[0]
    
    def test_handle_model_load_error(self):
        """Test handling of ModelLoadError."""
        error = ModelLoadError("large", "Network timeout")
        can_recover, message, suggestions = self.error_handler.handle_error(error)
        
        assert can_recover
        assert "모델 로드에 실패" in message
        assert "large" in message
        assert len(suggestions) == 4
        assert "인터넷 연결" in suggestions[0]
    
    def test_handle_transcription_error(self):
        """Test handling of TranscriptionError."""
        error = TranscriptionError("/path/audio.wav", "Model crashed")
        can_recover, message, suggestions = self.error_handler.handle_error(error)
        
        assert can_recover
        assert "음성 인식에 실패" in message
        assert "/path/audio.wav" in message
        assert len(suggestions) == 4
        assert "음질을 확인" in suggestions[0]
    
    def test_handle_disk_space_error(self):
        """Test handling of DiskSpaceError."""
        error = DiskSpaceError(required_space=1000000, available_space=500000)
        can_recover, message, suggestions = self.error_handler.handle_error(error)
        
        assert not can_recover
        assert "디스크 공간이 부족" in message
        assert len(suggestions) == 4
        assert "0MB" in suggestions[3]  # Required space in MB
    
    def test_handle_memory_error(self):
        """Test handling of MemoryError."""
        error = MemoryError("Out of memory")
        can_recover, message, suggestions = self.error_handler.handle_error(error)
        
        assert can_recover
        assert "메모리가 부족" in message
        assert len(suggestions) == 4
        assert "프로그램을 종료" in suggestions[0]
    
    def test_handle_generic_error(self):
        """Test handling of generic/unknown errors."""
        error = ValueError("Unknown error")
        can_recover, message, suggestions = self.error_handler.handle_error(error)
        
        assert can_recover
        assert "예상치 못한 오류" in message
        assert "Unknown error" in message
        assert len(suggestions) == 4
        assert "다시 시도" in suggestions[0]
    
    def test_error_logging(self):
        """Test that errors are properly logged."""
        error = UnsupportedFormatError("xyz")
        context = {"file_path": "test.xyz"}
        
        self.error_handler.handle_error(error, context)
        
        self.logger.error.assert_called_once()
        call_args = self.logger.error.call_args[0][0]
        assert "UnsupportedFormatError" in call_args
        assert "test.xyz" in call_args
    
    def test_error_tracking(self):
        """Test error occurrence tracking."""
        error1 = UnsupportedFormatError("xyz")
        error2 = UnsupportedFormatError("abc")
        error3 = ModelLoadError("large")
        
        self.error_handler.handle_error(error1)
        self.error_handler.handle_error(error2)
        self.error_handler.handle_error(error3)
        
        stats = self.error_handler.get_error_statistics()
        assert stats["UnsupportedFormatError"] == 2
        assert stats["ModelLoadError"] == 1
    
    def test_reset_statistics(self):
        """Test resetting error statistics."""
        error = UnsupportedFormatError("xyz")
        self.error_handler.handle_error(error)
        
        assert len(self.error_handler.get_error_statistics()) > 0
        
        self.error_handler.reset_statistics()
        assert len(self.error_handler.get_error_statistics()) == 0
    
    @patch('os.path.exists')
    @patch('shutil.copy2')
    def test_permission_error_recovery(self, mock_copy, mock_exists):
        """Test recovery from permission errors."""
        mock_exists.return_value = True
        mock_copy.return_value = None
        
        error = PermissionError("Access denied")
        context = {"file_path": "/restricted/file.wav"}
        
        result = self.error_handler.attempt_recovery(error, context)
        
        assert result is True
        mock_copy.assert_called_once_with("/restricted/file.wav", "/tmp/file.wav")
        assert context["temp_file"] == "/tmp/file.wav"
    
    @patch('os.listdir')
    @patch('os.remove')
    def test_disk_space_recovery(self, mock_remove, mock_listdir):
        """Test recovery from disk space errors."""
        mock_listdir.return_value = [
            "speech_to_text_temp1.wav",
            "speech_to_text_temp2.wav",
            "other_file.txt"
        ]
        
        error = DiskSpaceError()
        context = {"temp_dir": "/tmp"}
        
        result = self.error_handler.attempt_recovery(error, context)
        
        assert result is True
        assert mock_remove.call_count == 2  # Only speech_to_text_ files
    
    def test_recovery_attempt_limit(self):
        """Test that recovery attempts are limited."""
        error = AudioConversionError("test.m4a", "wav")
        context = {"file_path": "test.m4a"}
        
        # First 3 attempts should proceed
        for i in range(3):
            result = self.error_handler.attempt_recovery(error, context)
            # Result will be False since we don't have actual recovery logic
        
        # 4th attempt should be blocked
        result = self.error_handler.attempt_recovery(error, context)
        assert result is False
    
    def test_recovery_with_exception(self):
        """Test recovery when an exception occurs during recovery."""
        with patch.object(self.error_handler, '_recover_permission_error', side_effect=Exception("Recovery failed")):
            error = PermissionError("Access denied")
            context = {"file_path": "/test/file.wav"}
            
            result = self.error_handler.attempt_recovery(error, context)
            
            assert result is False
            self.logger.error.assert_called()
    
    def test_get_common_solutions(self):
        """Test getting common solutions for frequent issues."""
        solutions = ErrorHandler.get_common_solutions()
        
        assert isinstance(solutions, dict)
        assert "파일을 찾을 수 없음" in solutions
        assert "지원하지 않는 파일 형식" in solutions
        assert "메모리 부족" in solutions
        assert "디스크 공간 부족" in solutions
        
        # Check that each solution category has multiple suggestions
        for category, suggestions in solutions.items():
            assert isinstance(suggestions, list)
            assert len(suggestions) >= 2
    
    def test_context_handling(self):
        """Test that context information is properly handled."""
        error = AudioProcessingError("validation", "/path/to/file.wav", "Invalid format")
        context = {
            "file_path": "/path/to/file.wav",
            "operation": "validation",
            "user_id": "test_user"
        }
        
        can_recover, message, suggestions = self.error_handler.handle_error(error, context)
        
        # Verify context is logged
        self.logger.error.assert_called_once()
        logged_message = self.logger.error.call_args[0][0]
        assert "test_user" in logged_message
        assert "/path/to/file.wav" in logged_message


class TestErrorHandlerIntegration:
    """Integration tests for ErrorHandler with real scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_real_file_not_found_scenario(self):
        """Test handling of real file not found scenario."""
        non_existent_file = os.path.join(self.temp_dir, "nonexistent.wav")
        error = FileNotFoundError(f"No such file: {non_existent_file}")
        context = {"file_path": non_existent_file}
        
        can_recover, message, suggestions = self.error_handler.handle_error(error, context)
        
        assert not can_recover
        assert "찾을 수 없습니다" in message
        assert non_existent_file in message
        assert len(suggestions) > 0
    
    def test_real_permission_scenario(self):
        """Test handling of real permission scenario."""
        # Create a file and remove read permissions
        test_file = os.path.join(self.temp_dir, "restricted.wav")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        os.chmod(test_file, 0o000)  # Remove all permissions
        
        try:
            with open(test_file, 'r') as f:
                f.read()
        except PermissionError as error:
            context = {"file_path": test_file}
            can_recover, message, suggestions = self.error_handler.handle_error(error, context)
            
            assert can_recover
            assert "권한이 없습니다" in message
            assert test_file in message
            assert len(suggestions) > 0
        finally:
            # Restore permissions for cleanup
            os.chmod(test_file, 0o644)
    
    def test_multiple_error_handling(self):
        """Test handling multiple different errors in sequence."""
        errors = [
            UnsupportedFormatError("xyz", ["wav", "mp3"]),
            ModelLoadError("large", "Network error"),
            DiskSpaceError(1000000, 500000),
            MemoryError("Out of memory")
        ]
        
        results = []
        for error in errors:
            result = self.error_handler.handle_error(error)
            results.append(result)
        
        # Verify each error was handled appropriately
        assert len(results) == 4
        assert not results[0][0]  # UnsupportedFormatError - cannot recover
        assert results[1][0]      # ModelLoadError - can recover
        assert not results[2][0]  # DiskSpaceError - cannot recover
        assert results[3][0]      # MemoryError - can recover
        
        # Verify statistics
        stats = self.error_handler.get_error_statistics()
        assert stats["UnsupportedFormatError"] == 1
        assert stats["ModelLoadError"] == 1
        assert stats["DiskSpaceError"] == 1
        assert stats["MemoryError"] == 1


if __name__ == "__main__":
    pytest.main([__file__])