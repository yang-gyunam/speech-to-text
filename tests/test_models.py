"""
Unit tests for data models in the speech-to-text application.

Tests validation, serialization, and behavior of TranscriptionResult
and AudioFileInfo dataclasses.
"""

import pytest
from datetime import datetime
from src.speech_to_text.models import TranscriptionResult, AudioFileInfo


class TestTranscriptionResult:
    """Test cases for TranscriptionResult dataclass."""
    
    def test_valid_transcription_result_creation(self):
        """Test creating a valid TranscriptionResult instance."""
        timestamp = datetime.now()
        result = TranscriptionResult(
            original_file="/path/to/audio.m4a",
            transcribed_text="안녕하세요. 테스트입니다.",
            language="ko",
            confidence_score=0.95,
            processing_time=12.5,
            timestamp=timestamp
        )
        
        assert result.original_file == "/path/to/audio.m4a"
        assert result.transcribed_text == "안녕하세요. 테스트입니다."
        assert result.language == "ko"
        assert result.confidence_score == 0.95
        assert result.processing_time == 12.5
        assert result.timestamp == timestamp
        assert result.error_message is None
    
    def test_transcription_result_with_error_message(self):
        """Test creating TranscriptionResult with error message."""
        timestamp = datetime.now()
        result = TranscriptionResult(
            original_file="/path/to/audio.m4a",
            transcribed_text="",
            language="ko",
            confidence_score=0.0,
            processing_time=5.0,
            timestamp=timestamp,
            error_message="File not found"
        )
        
        assert result.error_message == "File not found"
    
    def test_empty_original_file_raises_error(self):
        """Test that empty original_file raises ValueError."""
        with pytest.raises(ValueError, match="original_file cannot be empty"):
            TranscriptionResult(
                original_file="",
                transcribed_text="test",
                language="ko",
                confidence_score=0.5,
                processing_time=1.0,
                timestamp=datetime.now()
            )
    
    def test_invalid_confidence_score_type_raises_error(self):
        """Test that non-numeric confidence_score raises TypeError."""
        with pytest.raises(TypeError, match="confidence_score must be a number"):
            TranscriptionResult(
                original_file="/path/to/audio.m4a",
                transcribed_text="test",
                language="ko",
                confidence_score="invalid",
                processing_time=1.0,
                timestamp=datetime.now()
            )
    
    def test_confidence_score_out_of_range_raises_error(self):
        """Test that confidence_score outside 0-1 range raises ValueError."""
        with pytest.raises(ValueError, match="confidence_score must be between 0.0 and 1.0"):
            TranscriptionResult(
                original_file="/path/to/audio.m4a",
                transcribed_text="test",
                language="ko",
                confidence_score=1.5,
                processing_time=1.0,
                timestamp=datetime.now()
            )
        
        with pytest.raises(ValueError, match="confidence_score must be between 0.0 and 1.0"):
            TranscriptionResult(
                original_file="/path/to/audio.m4a",
                transcribed_text="test",
                language="ko",
                confidence_score=-0.1,
                processing_time=1.0,
                timestamp=datetime.now()
            )
    
    def test_invalid_processing_time_type_raises_error(self):
        """Test that non-numeric processing_time raises TypeError."""
        with pytest.raises(TypeError, match="processing_time must be a number"):
            TranscriptionResult(
                original_file="/path/to/audio.m4a",
                transcribed_text="test",
                language="ko",
                confidence_score=0.5,
                processing_time="invalid",
                timestamp=datetime.now()
            )
    
    def test_negative_processing_time_raises_error(self):
        """Test that negative processing_time raises ValueError."""
        with pytest.raises(ValueError, match="processing_time cannot be negative"):
            TranscriptionResult(
                original_file="/path/to/audio.m4a",
                transcribed_text="test",
                language="ko",
                confidence_score=0.5,
                processing_time=-1.0,
                timestamp=datetime.now()
            )
    
    def test_invalid_timestamp_type_raises_error(self):
        """Test that non-datetime timestamp raises TypeError."""
        with pytest.raises(TypeError, match="timestamp must be a datetime object"):
            TranscriptionResult(
                original_file="/path/to/audio.m4a",
                transcribed_text="test",
                language="ko",
                confidence_score=0.5,
                processing_time=1.0,
                timestamp="2023-01-01"
            )


class TestAudioFileInfo:
    """Test cases for AudioFileInfo dataclass."""
    
    def test_valid_audio_file_info_creation(self):
        """Test creating a valid AudioFileInfo instance."""
        info = AudioFileInfo(
            file_path="/path/to/audio.m4a",
            file_size=1024000,
            duration=60.5,
            format="m4a",
            sample_rate=44100,
            channels=2
        )
        
        assert info.file_path == "/path/to/audio.m4a"
        assert info.file_size == 1024000
        assert info.duration == 60.5
        assert info.format == "m4a"
        assert info.sample_rate == 44100
        assert info.channels == 2
    
    def test_empty_file_path_raises_error(self):
        """Test that empty file_path raises ValueError."""
        with pytest.raises(ValueError, match="file_path cannot be empty"):
            AudioFileInfo(
                file_path="",
                file_size=1024,
                duration=10.0,
                format="wav",
                sample_rate=44100,
                channels=1
            )
    
    def test_invalid_file_size_raises_error(self):
        """Test that invalid file_size raises ValueError."""
        with pytest.raises(ValueError, match="file_size must be a non-negative integer"):
            AudioFileInfo(
                file_path="/path/to/audio.wav",
                file_size=-1,
                duration=10.0,
                format="wav",
                sample_rate=44100,
                channels=1
            )
        
        with pytest.raises(ValueError, match="file_size must be a non-negative integer"):
            AudioFileInfo(
                file_path="/path/to/audio.wav",
                file_size=10.5,
                duration=10.0,
                format="wav",
                sample_rate=44100,
                channels=1
            )
    
    def test_invalid_duration_raises_error(self):
        """Test that invalid duration raises ValueError."""
        with pytest.raises(ValueError, match="duration must be a non-negative number"):
            AudioFileInfo(
                file_path="/path/to/audio.wav",
                file_size=1024,
                duration=-1.0,
                format="wav",
                sample_rate=44100,
                channels=1
            )
    
    def test_empty_format_raises_error(self):
        """Test that empty format raises ValueError."""
        with pytest.raises(ValueError, match="format cannot be empty"):
            AudioFileInfo(
                file_path="/path/to/audio.wav",
                file_size=1024,
                duration=10.0,
                format="",
                sample_rate=44100,
                channels=1
            )
    
    def test_invalid_sample_rate_raises_error(self):
        """Test that invalid sample_rate raises ValueError."""
        with pytest.raises(ValueError, match="sample_rate must be a positive integer"):
            AudioFileInfo(
                file_path="/path/to/audio.wav",
                file_size=1024,
                duration=10.0,
                format="wav",
                sample_rate=0,
                channels=1
            )
        
        with pytest.raises(ValueError, match="sample_rate must be a positive integer"):
            AudioFileInfo(
                file_path="/path/to/audio.wav",
                file_size=1024,
                duration=10.0,
                format="wav",
                sample_rate=44100.5,
                channels=1
            )
    
    def test_invalid_channels_raises_error(self):
        """Test that invalid channels raises ValueError."""
        with pytest.raises(ValueError, match="channels must be a positive integer"):
            AudioFileInfo(
                file_path="/path/to/audio.wav",
                file_size=1024,
                duration=10.0,
                format="wav",
                sample_rate=44100,
                channels=0
            )
        
        with pytest.raises(ValueError, match="channels must be a positive integer"):
            AudioFileInfo(
                file_path="/path/to/audio.wav",
                file_size=1024,
                duration=10.0,
                format="wav",
                sample_rate=44100,
                channels=2.5
            )