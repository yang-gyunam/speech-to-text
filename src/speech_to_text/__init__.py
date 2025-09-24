"""Speech-to-Text application for converting iPhone audio recordings to text."""

from .audio_processor import AudioProcessor
from .config import ConfigManager, AppConfig, get_config_manager, load_config, save_config
from .error_handler import ErrorHandler
from .exceptions import (
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
    DiskSpaceError,
)
from .file_manager import FileManager
from .logger import SpeechToTextLogger, PerformanceMonitor, get_logger, setup_logging
from .main_app import SpeechToTextApp
from .models import TranscriptionResult, AudioFileInfo
from .text_exporter import TextExporter
from .transcriber import SpeechTranscriber

__version__ = "0.1.0"
__author__ = "Speech-to-Text Developer"
__description__ = "Convert iPhone audio recordings to text using OpenAI Whisper"

__all__ = [
    "AudioProcessor",
    "ConfigManager",
    "AppConfig",
    "get_config_manager",
    "load_config",
    "save_config",
    "ErrorHandler",
    "FileManager",
    "SpeechToTextApp",
    "SpeechTranscriber",
    "TextExporter",
    "TranscriptionResult",
    "AudioFileInfo",
    "SpeechToTextLogger",
    "PerformanceMonitor",
    "get_logger",
    "setup_logging",
    "SpeechToTextError",
    "FileError",
    "UnsupportedFormatError",
    "ProcessingError",
    "AudioProcessingError",
    "AudioConversionError",
    "ModelLoadError",
    "TranscriptionError",
    "SystemError",
    "FileSystemError",
    "DiskSpaceError",
]