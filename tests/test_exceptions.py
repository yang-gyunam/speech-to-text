"""
Unit tests for custom exception classes in the speech-to-text application.

Tests the behavior and message formatting of all custom exception types.
"""

import pytest
from src.speech_to_text.exceptions import (
    SpeechToTextError,
    FileError,
    UnsupportedFormatError,
    ProcessingError,
    AudioConversionError,
    ModelLoadError,
    TranscriptionError,
    SystemError,
    DiskSpaceError
)


class TestSpeechToTextError:
    """Test cases for base SpeechToTextError exception."""
    
    def test_base_exception_creation(self):
        """Test creating base exception with message."""
        error = SpeechToTextError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)


class TestFileError:
    """Test cases for FileError exception."""
    
    def test_file_error_creation(self):
        """Test creating FileError with message."""
        error = FileError("File operation failed")
        assert str(error) == "File operation failed"
        assert isinstance(error, SpeechToTextError)


class TestUnsupportedFormatError:
    """Test cases for UnsupportedFormatError exception."""
    
    def test_unsupported_format_error_without_supported_formats(self):
        """Test UnsupportedFormatError without supported formats list."""
        error = UnsupportedFormatError("xyz")
        assert error.format_name == "xyz"
        assert error.supported_formats == []
        assert str(error) == "Unsupported format 'xyz'"
    
    def test_unsupported_format_error_with_supported_formats(self):
        """Test UnsupportedFormatError with supported formats list."""
        supported = ["wav", "mp3", "m4a"]
        error = UnsupportedFormatError("xyz", supported)
        assert error.format_name == "xyz"
        assert error.supported_formats == supported
        assert str(error) == "Unsupported format 'xyz'. Supported formats: wav, mp3, m4a"
    
    def test_unsupported_format_error_inheritance(self):
        """Test that UnsupportedFormatError inherits from FileError."""
        error = UnsupportedFormatError("xyz")
        assert isinstance(error, FileError)
        assert isinstance(error, SpeechToTextError)


class TestProcessingError:
    """Test cases for ProcessingError exception."""
    
    def test_processing_error_creation(self):
        """Test creating ProcessingError with message."""
        error = ProcessingError("Processing failed")
        assert str(error) == "Processing failed"
        assert isinstance(error, SpeechToTextError)


class TestAudioConversionError:
    """Test cases for AudioConversionError exception."""
    
    def test_audio_conversion_error_without_original_error(self):
        """Test AudioConversionError without original error message."""
        error = AudioConversionError("/path/to/file.m4a", "wav")
        assert error.source_file == "/path/to/file.m4a"
        assert error.target_format == "wav"
        assert error.original_error is None
        assert str(error) == "Failed to convert '/path/to/file.m4a' to wav"
    
    def test_audio_conversion_error_with_original_error(self):
        """Test AudioConversionError with original error message."""
        error = AudioConversionError("/path/to/file.m4a", "wav", "FFmpeg not found")
        assert error.source_file == "/path/to/file.m4a"
        assert error.target_format == "wav"
        assert error.original_error == "FFmpeg not found"
        assert str(error) == "Failed to convert '/path/to/file.m4a' to wav: FFmpeg not found"
    
    def test_audio_conversion_error_inheritance(self):
        """Test that AudioConversionError inherits from ProcessingError."""
        error = AudioConversionError("/path/to/file.m4a", "wav")
        assert isinstance(error, ProcessingError)
        assert isinstance(error, SpeechToTextError)


class TestModelLoadError:
    """Test cases for ModelLoadError exception."""
    
    def test_model_load_error_without_original_error(self):
        """Test ModelLoadError without original error message."""
        error = ModelLoadError("base")
        assert error.model_name == "base"
        assert error.original_error is None
        assert str(error) == "Failed to load Whisper model 'base'"
    
    def test_model_load_error_with_original_error(self):
        """Test ModelLoadError with original error message."""
        error = ModelLoadError("large", "Network timeout")
        assert error.model_name == "large"
        assert error.original_error == "Network timeout"
        assert str(error) == "Failed to load Whisper model 'large': Network timeout"
    
    def test_model_load_error_inheritance(self):
        """Test that ModelLoadError inherits from ProcessingError."""
        error = ModelLoadError("base")
        assert isinstance(error, ProcessingError)
        assert isinstance(error, SpeechToTextError)


class TestTranscriptionError:
    """Test cases for TranscriptionError exception."""
    
    def test_transcription_error_without_original_error(self):
        """Test TranscriptionError without original error message."""
        error = TranscriptionError("/path/to/audio.m4a")
        assert error.file_path == "/path/to/audio.m4a"
        assert error.original_error is None
        assert str(error) == "Failed to transcribe '/path/to/audio.m4a'"
    
    def test_transcription_error_with_original_error(self):
        """Test TranscriptionError with original error message."""
        error = TranscriptionError("/path/to/audio.m4a", "Audio too short")
        assert error.file_path == "/path/to/audio.m4a"
        assert error.original_error == "Audio too short"
        assert str(error) == "Failed to transcribe '/path/to/audio.m4a': Audio too short"
    
    def test_transcription_error_inheritance(self):
        """Test that TranscriptionError inherits from ProcessingError."""
        error = TranscriptionError("/path/to/audio.m4a")
        assert isinstance(error, ProcessingError)
        assert isinstance(error, SpeechToTextError)


class TestSystemError:
    """Test cases for SystemError exception."""
    
    def test_system_error_creation(self):
        """Test creating SystemError with message."""
        error = SystemError("System resource unavailable")
        assert str(error) == "System resource unavailable"
        assert isinstance(error, SpeechToTextError)


class TestDiskSpaceError:
    """Test cases for DiskSpaceError exception."""
    
    def test_disk_space_error_without_space_info(self):
        """Test DiskSpaceError without space information."""
        error = DiskSpaceError()
        assert error.required_space is None
        assert error.available_space is None
        assert str(error) == "Insufficient disk space"
    
    def test_disk_space_error_with_space_info(self):
        """Test DiskSpaceError with space information."""
        error = DiskSpaceError(required_space=1000000, available_space=500000)
        assert error.required_space == 1000000
        assert error.available_space == 500000
        assert str(error) == "Insufficient disk space (required: 1000000 bytes, available: 500000 bytes)"
    
    def test_disk_space_error_inheritance(self):
        """Test that DiskSpaceError inherits from SystemError."""
        error = DiskSpaceError()
        assert isinstance(error, SystemError)
        assert isinstance(error, SpeechToTextError)