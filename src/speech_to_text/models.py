"""
Data models for the speech-to-text application.

This module contains dataclasses and types used throughout the application
for representing transcription results, audio file information, and other
core data structures.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TranscriptionResult:
    """
    Represents the result of a speech-to-text transcription operation.
    
    Attributes:
        original_file: Path to the original audio file
        transcribed_text: The transcribed text content
        language: Language code used for transcription (e.g., 'ko', 'en')
        confidence_score: Confidence score of the transcription (0.0 to 1.0)
        processing_time: Time taken to process the file in seconds
        timestamp: When the transcription was completed
        error_message: Optional error message if transcription failed
    """
    original_file: str
    transcribed_text: str
    language: str
    confidence_score: float
    processing_time: float
    timestamp: datetime
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Validate the data after initialization."""
        if not self.original_file:
            raise ValueError("original_file cannot be empty")
        
        if not isinstance(self.confidence_score, (int, float)):
            raise TypeError("confidence_score must be a number")
            
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("confidence_score must be between 0.0 and 1.0")
            
        if not isinstance(self.processing_time, (int, float)):
            raise TypeError("processing_time must be a number")
            
        if self.processing_time < 0:
            raise ValueError("processing_time cannot be negative")
            
        if not isinstance(self.timestamp, datetime):
            raise TypeError("timestamp must be a datetime object")


@dataclass
class AudioFileInfo:
    """
    Contains metadata information about an audio file.
    
    Attributes:
        file_path: Path to the audio file
        file_size: Size of the file in bytes
        duration: Duration of the audio in seconds
        format: Audio format/extension (e.g., 'm4a', 'wav', 'mp3')
        sample_rate: Sample rate in Hz
        channels: Number of audio channels
    """
    file_path: str
    file_size: int
    duration: float
    format: str
    sample_rate: int
    channels: int
    
    def __post_init__(self):
        """Validate the data after initialization."""
        if not self.file_path:
            raise ValueError("file_path cannot be empty")
            
        if not isinstance(self.file_size, int) or self.file_size < 0:
            raise ValueError("file_size must be a non-negative integer")
            
        if not isinstance(self.duration, (int, float)) or self.duration < 0:
            raise ValueError("duration must be a non-negative number")
            
        if not self.format:
            raise ValueError("format cannot be empty")
            
        if not isinstance(self.sample_rate, int) or self.sample_rate <= 0:
            raise ValueError("sample_rate must be a positive integer")
            
        if not isinstance(self.channels, int) or self.channels <= 0:
            raise ValueError("channels must be a positive integer")