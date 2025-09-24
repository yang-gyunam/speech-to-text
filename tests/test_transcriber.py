"""
Unit tests for the SpeechTranscriber class.

This module contains tests for the speech-to-text transcription functionality,
including model loading, single file transcription, and batch processing.
"""

import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.speech_to_text.exceptions import ModelLoadError, TranscriptionError
from src.speech_to_text.models import TranscriptionResult
from src.speech_to_text.transcriber import SpeechTranscriber


class TestSpeechTranscriber:
    """Test cases for the SpeechTranscriber class."""
    
    def test_init_with_valid_model_size(self):
        """Test initialization with valid model sizes."""
        with patch('src.speech_to_text.transcriber.whisper.load_model') as mock_load:
            mock_load.return_value = Mock()
            
            for model_size in SpeechTranscriber.AVAILABLE_MODELS:
                transcriber = SpeechTranscriber(model_size)
                assert transcriber.model_size == model_size
                assert transcriber._model is not None
    
    def test_init_with_invalid_model_size(self):
        """Test initialization with invalid model size raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            SpeechTranscriber("invalid_model")
        
        assert "Invalid model size 'invalid_model'" in str(exc_info.value)
        assert "Available models:" in str(exc_info.value)
    
    def test_init_default_model_size(self):
        """Test initialization with default model size."""
        with patch('src.speech_to_text.transcriber.whisper.load_model') as mock_load:
            mock_load.return_value = Mock()
            
            transcriber = SpeechTranscriber()
            assert transcriber.model_size == "base"
    
    def test_model_load_failure(self):
        """Test that ModelLoadError is raised when model loading fails."""
        with patch('src.speech_to_text.transcriber.whisper.load_model') as mock_load:
            mock_load.side_effect = Exception("Model loading failed")
            
            with pytest.raises(ModelLoadError) as exc_info:
                SpeechTranscriber("base")
            
            assert "Failed to load Whisper model 'base'" in str(exc_info.value)
            assert "Model loading failed" in str(exc_info.value)
    
    def test_transcribe_file_success(self):
        """Test successful transcription of a single file."""
        with patch('src.speech_to_text.transcriber.whisper.load_model') as mock_load:
            # Mock the Whisper model
            mock_model = Mock()
            mock_model.transcribe.return_value = {
                "text": "안녕하세요. 이것은 테스트 음성입니다."
            }
            mock_load.return_value = mock_model
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                transcriber = SpeechTranscriber("base")
                result = transcriber.transcribe_file(temp_path, "ko")
                
                # Verify the result
                assert isinstance(result, TranscriptionResult)
                assert result.original_file == str(Path(temp_path).resolve())
                assert result.transcribed_text == "안녕하세요. 이것은 테스트 음성입니다."
                assert result.language == "ko"
                assert result.confidence_score == 0.9  # High confidence for non-empty text
                assert result.processing_time > 0
                assert isinstance(result.timestamp, datetime)
                assert result.error_message is None
                
                # Verify model was called correctly
                mock_model.transcribe.assert_called_once_with(
                    str(Path(temp_path).resolve()),
                    language="ko",
                    verbose=False
                )
            
            finally:
                # Clean up
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
    
    def test_transcribe_file_empty_result(self):
        """Test transcription with empty result."""
        with patch('src.speech_to_text.transcriber.whisper.load_model') as mock_load:
            # Mock the Whisper model to return empty text
            mock_model = Mock()
            mock_model.transcribe.return_value = {"text": ""}
            mock_load.return_value = mock_model
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                transcriber = SpeechTranscriber("base")
                result = transcriber.transcribe_file(temp_path, "en")
                
                # Verify the result
                assert result.transcribed_text == ""
                assert result.language == "en"
                assert result.confidence_score == 0.0  # Low confidence for empty text
                assert result.error_message is None
            
            finally:
                # Clean up
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
    
    def test_transcribe_file_not_found(self):
        """Test transcription with non-existent file."""
        with patch('src.speech_to_text.transcriber.whisper.load_model') as mock_load:
            mock_load.return_value = Mock()
            
            transcriber = SpeechTranscriber("base")
            
            with pytest.raises(FileNotFoundError) as exc_info:
                transcriber.transcribe_file("/nonexistent/file.wav", "ko")
            
            assert "Audio file not found" in str(exc_info.value)
    
    def test_transcribe_file_with_exception(self):
        """Test transcription when Whisper raises an exception."""
        with patch('src.speech_to_text.transcriber.whisper.load_model') as mock_load:
            # Mock the Whisper model to raise an exception
            mock_model = Mock()
            mock_model.transcribe.side_effect = Exception("Transcription failed")
            mock_load.return_value = mock_model
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                transcriber = SpeechTranscriber("base")
                result = transcriber.transcribe_file(temp_path, "ko")
                
                # Verify the result contains error information
                assert result.transcribed_text == ""
                assert result.confidence_score == 0.0
                assert result.error_message == "Transcription failed"
                assert result.processing_time > 0
            
            finally:
                # Clean up
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
    
    def test_transcribe_batch_success(self):
        """Test successful batch transcription."""
        with patch('src.speech_to_text.transcriber.whisper.load_model') as mock_load:
            # Mock the Whisper model
            mock_model = Mock()
            mock_model.transcribe.side_effect = [
                {"text": "첫 번째 파일입니다."},
                {"text": "두 번째 파일입니다."},
                {"text": "세 번째 파일입니다."}
            ]
            mock_load.return_value = mock_model
            
            # Create temporary files
            temp_files = []
            for i in range(3):
                temp_file = tempfile.NamedTemporaryFile(suffix=f"_{i}.wav", delete=False)
                temp_files.append(temp_file.name)
                temp_file.close()
            
            try:
                transcriber = SpeechTranscriber("base")
                results = transcriber.transcribe_batch(temp_files, "ko")
                
                # Verify the results
                assert len(results) == 3
                
                expected_texts = [
                    "첫 번째 파일입니다.",
                    "두 번째 파일입니다.",
                    "세 번째 파일입니다."
                ]
                
                for i, result in enumerate(results):
                    assert isinstance(result, TranscriptionResult)
                    assert result.transcribed_text == expected_texts[i]
                    assert result.language == "ko"
                    assert result.confidence_score == 0.9
                    assert result.error_message is None
                
                # Verify model was called for each file
                assert mock_model.transcribe.call_count == 3
            
            finally:
                # Clean up
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
    
    def test_transcribe_batch_with_progress_callback(self):
        """Test batch transcription with progress callback."""
        with patch('src.speech_to_text.transcriber.whisper.load_model') as mock_load:
            # Mock the Whisper model
            mock_model = Mock()
            mock_model.transcribe.return_value = {"text": "테스트 텍스트"}
            mock_load.return_value = mock_model
            
            # Create temporary files
            temp_files = []
            for i in range(2):
                temp_file = tempfile.NamedTemporaryFile(suffix=f"_{i}.wav", delete=False)
                temp_files.append(temp_file.name)
                temp_file.close()
            
            # Mock progress callback
            progress_callback = Mock()
            
            try:
                transcriber = SpeechTranscriber("base")
                results = transcriber.transcribe_batch(
                    temp_files, 
                    "ko", 
                    progress_callback=progress_callback
                )
                
                # Verify results
                assert len(results) == 2
                
                # Verify progress callback was called correctly
                expected_calls = [
                    ((0, 2, temp_files[0]),),  # First file
                    ((1, 2, temp_files[1]),),  # Second file
                    ((2, 2, "Batch processing complete"),)  # Completion
                ]
                
                assert progress_callback.call_count == 3
                for i, expected_call in enumerate(expected_calls):
                    actual_call = progress_callback.call_args_list[i]
                    assert actual_call[0] == expected_call[0]
            
            finally:
                # Clean up
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
    
    def test_transcribe_batch_empty_list(self):
        """Test batch transcription with empty file list."""
        with patch('src.speech_to_text.transcriber.whisper.load_model') as mock_load:
            mock_load.return_value = Mock()
            
            transcriber = SpeechTranscriber("base")
            results = transcriber.transcribe_batch([], "ko")
            
            assert results == []
    
    def test_model_property(self):
        """Test the model property."""
        with patch('src.speech_to_text.transcriber.whisper.load_model') as mock_load:
            mock_model = Mock()
            mock_load.return_value = mock_model
            
            transcriber = SpeechTranscriber("base")
            assert transcriber.model is mock_model
    
    def test_get_model_info(self):
        """Test getting model information."""
        with patch('src.speech_to_text.transcriber.whisper.load_model') as mock_load:
            mock_load.return_value = Mock()
            
            transcriber = SpeechTranscriber("small")
            info = transcriber.get_model_info()
            
            expected_info = {
                "model_size": "small",
                "is_loaded": True,
                "available_models": ["tiny", "base", "small", "medium", "large"]
            }
            
            assert info == expected_info
    
    def test_get_model_info_not_loaded(self):
        """Test getting model information when model is not loaded."""
        with patch('src.speech_to_text.transcriber.whisper.load_model') as mock_load:
            mock_load.return_value = Mock()
            
            transcriber = SpeechTranscriber("base")
            transcriber._model = None  # Simulate unloaded model
            
            info = transcriber.get_model_info()
            assert info["is_loaded"] is False
    
    def test_available_models_constant(self):
        """Test that AVAILABLE_MODELS constant contains expected models."""
        expected_models = ["tiny", "base", "small", "medium", "large"]
        assert SpeechTranscriber.AVAILABLE_MODELS == expected_models