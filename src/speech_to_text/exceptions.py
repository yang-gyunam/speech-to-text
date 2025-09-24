"""
Custom exception classes for the speech-to-text application.

This module defines specific exception types for different error scenarios
that can occur during audio processing and transcription operations.
"""


class SpeechToTextError(Exception):
    """Base exception class for all speech-to-text related errors."""
    pass


# File-related errors
class FileError(SpeechToTextError):
    """Base class for file-related errors."""
    pass


class UnsupportedFormatError(FileError):
    """Raised when an unsupported audio format is encountered."""
    
    def __init__(self, format_name: str, supported_formats: list = None):
        self.format_name = format_name
        self.supported_formats = supported_formats or []
        
        if self.supported_formats:
            message = f"Unsupported format '{format_name}'. Supported formats: {', '.join(self.supported_formats)}"
        else:
            message = f"Unsupported format '{format_name}'"
            
        super().__init__(message)


# Processing-related errors
class ProcessingError(SpeechToTextError):
    """Base class for processing-related errors."""
    pass


class AudioProcessingError(ProcessingError):
    """Raised when general audio processing operations fail."""
    
    def __init__(self, operation: str, file_path: str = None, original_error: str = None):
        self.operation = operation
        self.file_path = file_path
        self.original_error = original_error
        
        message = f"Audio processing failed during {operation}"
        if file_path:
            message += f" for file '{file_path}'"
        if original_error:
            message += f": {original_error}"
            
        super().__init__(message)


class AudioConversionError(ProcessingError):
    """Raised when audio format conversion fails."""
    
    def __init__(self, source_file: str, target_format: str, original_error: str = None):
        self.source_file = source_file
        self.target_format = target_format
        self.original_error = original_error
        
        message = f"Failed to convert '{source_file}' to {target_format}"
        if original_error:
            message += f": {original_error}"
            
        super().__init__(message)


class ModelLoadError(ProcessingError):
    """Raised when the Whisper model fails to load."""
    
    def __init__(self, model_name: str, original_error: str = None):
        self.model_name = model_name
        self.original_error = original_error
        
        message = f"Failed to load Whisper model '{model_name}'"
        if original_error:
            message += f": {original_error}"
            
        super().__init__(message)


class TranscriptionError(ProcessingError):
    """Raised when speech-to-text transcription fails."""
    
    def __init__(self, file_path: str, original_error: str = None):
        self.file_path = file_path
        self.original_error = original_error
        
        message = f"Failed to transcribe '{file_path}'"
        if original_error:
            message += f": {original_error}"
            
        super().__init__(message)


# System-related errors
class SystemError(SpeechToTextError):
    """Base class for system-related errors."""
    pass


class FileSystemError(SystemError):
    """Raised when file system operations fail."""
    pass


class DiskSpaceError(SystemError):
    """Raised when there's insufficient disk space for operations."""
    
    def __init__(self, required_space: int = None, available_space: int = None):
        self.required_space = required_space
        self.available_space = available_space
        
        message = "Insufficient disk space"
        if required_space and available_space:
            message += f" (required: {required_space} bytes, available: {available_space} bytes)"
            
        super().__init__(message)