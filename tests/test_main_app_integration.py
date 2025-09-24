"""
Integration tests for the main application workflow.

These tests verify the complete single file processing workflow,
including component integration, resource management, and error handling.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.speech_to_text.main_app import SpeechToTextApp
from src.speech_to_text.models import TranscriptionResult
from src.speech_to_text.exceptions import (
    SpeechToTextError, 
    UnsupportedFormatError, 
    FileSystemError,
    ModelLoadError
)


class TestSpeechToTextAppIntegration:
    """Integration tests for SpeechToTextApp complete workflows."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def sample_audio_file(self, temp_dir):
        """Create a mock audio file for testing."""
        audio_file = Path(temp_dir) / "test_recording.m4a"
        audio_file.write_bytes(b"fake audio content")
        return str(audio_file)
    
    @pytest.fixture
    def sample_audio_files(self, temp_dir):
        """Create multiple mock audio files for batch testing."""
        files = []
        for i in range(3):
            audio_file = Path(temp_dir) / f"test_recording_{i}.m4a"
            audio_file.write_bytes(b"fake audio content")
            files.append(str(audio_file))
        return files
    
    @pytest.fixture
    def mock_transcription_result(self, sample_audio_file):
        """Create a mock transcription result."""
        from datetime import datetime
        return TranscriptionResult(
            original_file=sample_audio_file,
            transcribed_text="안녕하세요. 이것은 테스트 음성입니다.",
            language="ko",
            confidence_score=0.95,
            processing_time=2.5,
            timestamp=datetime.now()
        )
    
    def test_app_initialization(self):
        """Test SpeechToTextApp initialization with default parameters."""
        app = SpeechToTextApp()
        
        assert app.model_size == "base"
        assert app.language == "ko"
        assert app.output_dir == "./output"
        assert app.include_metadata is True
        assert app._temp_files == []
    
    def test_app_initialization_with_custom_params(self):
        """Test SpeechToTextApp initialization with custom parameters."""
        app = SpeechToTextApp(
            model_size="large",
            language="en",
            output_dir="/custom/output",
            include_metadata=False
        )
        
        assert app.model_size == "large"
        assert app.language == "en"
        assert app.output_dir == "/custom/output"
        assert app.include_metadata is False
    
    def test_lazy_component_initialization(self):
        """Test that components are initialized lazily."""
        app = SpeechToTextApp()
        
        # Components should be None initially
        assert app._audio_processor is None
        assert app._file_manager is None
        assert app._transcriber is None
        assert app._text_exporter is None
        assert app._error_handler is None
        
        # Accessing properties should initialize components
        audio_processor = app.audio_processor
        assert app._audio_processor is not None
        assert audio_processor is app._audio_processor  # Should return same instance
    
    @patch('src.speech_to_text.main_app.SpeechTranscriber')
    @patch('src.speech_to_text.main_app.AudioProcessor')
    def test_single_file_processing_success(self, mock_audio_processor_class, 
                                          mock_transcriber_class, 
                                          temp_dir, sample_audio_file, 
                                          mock_transcription_result):
        """Test successful single file processing workflow."""
        # Setup mocks
        mock_audio_processor = Mock()
        mock_audio_processor.validate_file.return_value = True
        mock_audio_processor_class.return_value = mock_audio_processor
        
        mock_transcriber = Mock()
        mock_transcriber.transcribe_file.return_value = mock_transcription_result
        mock_transcriber_class.return_value = mock_transcriber
        
        # Create app and process file
        app = SpeechToTextApp(output_dir=temp_dir)
        
        with patch.object(app, 'file_manager') as mock_file_manager, \
             patch.object(app, 'text_exporter') as mock_text_exporter:
            
            mock_file_manager.create_output_directory.return_value = temp_dir
            mock_file_manager.generate_output_filename.return_value = f"{temp_dir}/output.txt"
            mock_text_exporter.save_transcription_result.return_value = f"{temp_dir}/output.txt"
            
            result = app.process_single_file(sample_audio_file)
            
            # Verify the workflow
            mock_audio_processor.validate_file.assert_called_once_with(sample_audio_file)
            mock_file_manager.create_output_directory.assert_called_once_with(temp_dir)
            mock_transcriber.transcribe_file.assert_called_once_with(sample_audio_file, "ko")
            mock_text_exporter.save_transcription_result.assert_called_once()
            
            assert result == mock_transcription_result
    
    @patch('src.speech_to_text.main_app.AudioProcessor')
    def test_single_file_processing_invalid_file(self, mock_audio_processor_class, 
                                               temp_dir, sample_audio_file):
        """Test single file processing with invalid file."""
        # Setup mock to raise validation error
        mock_audio_processor = Mock()
        mock_audio_processor.validate_file.side_effect = UnsupportedFormatError("test", [])
        mock_audio_processor_class.return_value = mock_audio_processor
        
        app = SpeechToTextApp(output_dir=temp_dir)
        
        with pytest.raises(UnsupportedFormatError):
            app.process_single_file(sample_audio_file)
    
    @patch('src.speech_to_text.main_app.SpeechTranscriber')
    @patch('src.speech_to_text.main_app.AudioProcessor')
    def test_single_file_processing_transcription_error(self, mock_audio_processor_class,
                                                      mock_transcriber_class,
                                                      temp_dir, sample_audio_file):
        """Test single file processing with transcription error."""
        from datetime import datetime
        
        # Setup mocks
        mock_audio_processor = Mock()
        mock_audio_processor.validate_file.return_value = True
        mock_audio_processor_class.return_value = mock_audio_processor
        
        # Create result with error
        error_result = TranscriptionResult(
            original_file=sample_audio_file,
            transcribed_text="",
            language="ko",
            confidence_score=0.0,
            processing_time=1.0,
            timestamp=datetime.now(),
            error_message="Transcription failed"
        )
        
        mock_transcriber = Mock()
        mock_transcriber.transcribe_file.return_value = error_result
        mock_transcriber_class.return_value = mock_transcriber
        
        app = SpeechToTextApp(output_dir=temp_dir)
        
        with patch.object(app, 'file_manager') as mock_file_manager:
            mock_file_manager.create_output_directory.return_value = temp_dir
            mock_file_manager.generate_output_filename.return_value = f"{temp_dir}/output.txt"
            
            result = app.process_single_file(sample_audio_file)
            
            assert result.error_message == "Transcription failed"
            assert result.transcribed_text == ""
    
    @patch('src.speech_to_text.main_app.SpeechTranscriber')
    @patch('src.speech_to_text.main_app.AudioProcessor')
    def test_batch_processing_success(self, mock_audio_processor_class,
                                    mock_transcriber_class,
                                    temp_dir, sample_audio_files):
        """Test successful batch processing workflow."""
        from datetime import datetime
        
        # Setup mocks
        mock_audio_processor = Mock()
        mock_audio_processor.validate_file.return_value = True
        mock_audio_processor_class.return_value = mock_audio_processor
        
        # Create mock results for each file
        mock_results = []
        for i, file_path in enumerate(sample_audio_files):
            result = TranscriptionResult(
                original_file=file_path,
                transcribed_text=f"테스트 음성 {i}",
                language="ko",
                confidence_score=0.9,
                processing_time=2.0,
                timestamp=datetime.now()
            )
            mock_results.append(result)
        
        mock_transcriber = Mock()
        mock_transcriber.transcribe_batch.return_value = mock_results
        mock_transcriber_class.return_value = mock_transcriber
        
        app = SpeechToTextApp(output_dir=temp_dir)
        
        with patch.object(app, 'file_manager') as mock_file_manager, \
             patch.object(app, 'text_exporter') as mock_text_exporter:
            
            mock_file_manager.create_output_directory.return_value = temp_dir
            mock_text_exporter.save_batch_results.return_value = {}
            
            results = app.process_batch_files(sample_audio_files)
            
            # Verify the workflow
            assert len(results) == len(sample_audio_files)
            mock_transcriber.transcribe_batch.assert_called_once()
            mock_text_exporter.save_batch_results.assert_called_once()
    
    @patch('src.speech_to_text.main_app.AudioProcessor')
    def test_batch_processing_with_invalid_files(self, mock_audio_processor_class,
                                               temp_dir, sample_audio_files):
        """Test batch processing with some invalid files."""
        # Setup mock to validate only first file
        mock_audio_processor = Mock()
        def validate_side_effect(file_path):
            if file_path == sample_audio_files[0]:
                return True
            else:
                raise UnsupportedFormatError("test", [])
        
        mock_audio_processor.validate_file.side_effect = validate_side_effect
        mock_audio_processor_class.return_value = mock_audio_processor
        
        app = SpeechToTextApp(output_dir=temp_dir)
        
        with patch.object(app, 'transcriber') as mock_transcriber, \
             patch.object(app, 'file_manager') as mock_file_manager, \
             patch.object(app, 'text_exporter') as mock_text_exporter:
            
            mock_file_manager.create_output_directory.return_value = temp_dir
            mock_transcriber.transcribe_batch.return_value = []
            mock_text_exporter.save_batch_results.return_value = {}
            
            results = app.process_batch_files(sample_audio_files)
            
            # Should only process valid files
            mock_transcriber.transcribe_batch.assert_called_once()
            call_args = mock_transcriber.transcribe_batch.call_args[0]
            assert len(call_args[0]) == 1  # Only one valid file
            assert call_args[0][0] == sample_audio_files[0]
    
    @patch('src.speech_to_text.main_app.AudioProcessor')
    def test_directory_processing_success(self, mock_audio_processor_class,
                                        temp_dir, sample_audio_files):
        """Test successful directory processing workflow."""
        mock_audio_processor = Mock()
        mock_audio_processor_class.return_value = mock_audio_processor
        
        app = SpeechToTextApp(output_dir=temp_dir)
        
        with patch.object(app, 'file_manager') as mock_file_manager, \
             patch.object(app, 'process_batch_files') as mock_process_batch:
            
            mock_file_manager.find_audio_files.return_value = sample_audio_files
            mock_process_batch.return_value = []
            
            results = app.process_directory(temp_dir)
            
            mock_file_manager.find_audio_files.assert_called_once_with(temp_dir, True)
            mock_process_batch.assert_called_once_with(sample_audio_files, None, None, None)
    
    def test_directory_processing_no_files(self, temp_dir):
        """Test directory processing with no audio files."""
        app = SpeechToTextApp(output_dir=temp_dir)
        
        with patch.object(app, 'file_manager') as mock_file_manager:
            mock_file_manager.find_audio_files.return_value = []
            
            results = app.process_directory(temp_dir)
            
            assert results == []
    
    def test_get_supported_formats(self):
        """Test getting supported audio formats."""
        app = SpeechToTextApp()
        
        with patch.object(app, 'audio_processor') as mock_audio_processor:
            mock_audio_processor.get_supported_formats.return_value = ['.m4a', '.wav', '.mp3']
            
            formats = app.get_supported_formats()
            
            assert formats == ['.m4a', '.wav', '.mp3']
            mock_audio_processor.get_supported_formats.assert_called_once()
    
    def test_get_audio_info(self, sample_audio_file):
        """Test getting audio file information."""
        app = SpeechToTextApp()
        
        mock_file_info = Mock()
        mock_file_info.file_path = sample_audio_file
        mock_file_info.file_size = 1024
        mock_file_info.duration = 10.5
        mock_file_info.format = '.m4a'
        mock_file_info.sample_rate = 44100
        mock_file_info.channels = 2
        
        with patch.object(app, 'audio_processor') as mock_audio_processor:
            mock_audio_processor.get_audio_info.return_value = mock_file_info
            
            info = app.get_audio_info(sample_audio_file)
            
            expected_info = {
                'file_path': sample_audio_file,
                'file_size': 1024,
                'duration': 10.5,
                'format': '.m4a',
                'sample_rate': 44100,
                'channels': 2
            }
            
            assert info == expected_info
    
    def test_preprocess_audio(self, temp_dir, sample_audio_file):
        """Test audio preprocessing functionality."""
        app = SpeechToTextApp()
        
        processed_path = f"{temp_dir}/processed.m4a"
        
        with patch.object(app, 'audio_processor') as mock_audio_processor:
            mock_audio_processor.preprocess_audio.return_value = processed_path
            
            result_path = app.preprocess_audio(sample_audio_file, normalize=True, remove_silence=False)
            
            assert result_path == processed_path
            assert processed_path in app._temp_files
            mock_audio_processor.preprocess_audio.assert_called_once()
    
    def test_context_manager_usage(self, temp_dir):
        """Test using SpeechToTextApp as a context manager."""
        with SpeechToTextApp(output_dir=temp_dir) as app:
            assert isinstance(app, SpeechToTextApp)
            
            # Add some temp files to test cleanup
            app._temp_files = [f"{temp_dir}/temp1.wav", f"{temp_dir}/temp2.wav"]
        
        # Temp files should be cleared after context exit
        assert app._temp_files == []
    
    def test_context_manager_with_exception(self, temp_dir):
        """Test context manager cleanup when exception occurs."""
        temp_file = Path(temp_dir) / "temp_test.wav"
        temp_file.write_bytes(b"test")
        
        try:
            with SpeechToTextApp(output_dir=temp_dir) as app:
                app._temp_files = [str(temp_file)]
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Temp file should be cleaned up even with exception
        assert not temp_file.exists()
        assert app._temp_files == []
    
    def test_cleanup_temp_files(self, temp_dir):
        """Test temporary file cleanup functionality."""
        app = SpeechToTextApp()
        
        # Create some temporary files
        temp_files = []
        for i in range(3):
            temp_file = Path(temp_dir) / f"temp_{i}.wav"
            temp_file.write_bytes(b"test")
            temp_files.append(str(temp_file))
        
        app._temp_files = temp_files
        
        # Verify files exist
        for temp_file in temp_files:
            assert Path(temp_file).exists()
        
        # Clean up
        app._cleanup_temp_files()
        
        # Verify files are removed
        for temp_file in temp_files:
            assert not Path(temp_file).exists()
        
        assert app._temp_files == []
    
    def test_close_method(self, temp_dir):
        """Test the close method for resource cleanup."""
        app = SpeechToTextApp()
        
        # Create a temporary file
        temp_file = Path(temp_dir) / "temp_close_test.wav"
        temp_file.write_bytes(b"test")
        app._temp_files = [str(temp_file)]
        
        # Close the app
        app.close()
        
        # Verify cleanup
        assert not temp_file.exists()
        assert app._temp_files == []


class TestSpeechToTextAppErrorHandling:
    """Test error handling in SpeechToTextApp."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @patch('src.speech_to_text.main_app.SpeechTranscriber')
    def test_model_load_error_handling(self, mock_transcriber_class):
        """Test handling of model loading errors."""
        mock_transcriber_class.side_effect = ModelLoadError("base", "Model not found")
        
        app = SpeechToTextApp()
        
        with pytest.raises(ModelLoadError):
            _ = app.transcriber  # This should trigger model loading
    
    @patch('src.speech_to_text.main_app.AudioProcessor')
    def test_file_system_error_handling(self, mock_audio_processor_class, temp_dir):
        """Test handling of file system errors."""
        mock_audio_processor = Mock()
        mock_audio_processor.validate_file.side_effect = FileSystemError("Disk full")
        mock_audio_processor_class.return_value = mock_audio_processor
        
        app = SpeechToTextApp(output_dir=temp_dir)
        
        with pytest.raises(FileSystemError):
            app.process_single_file("nonexistent.m4a")
    
    def test_error_handler_integration(self, temp_dir):
        """Test integration with error handler."""
        app = SpeechToTextApp(output_dir=temp_dir)
        
        with patch.object(app, 'error_handler') as mock_error_handler:
            mock_error_handler.handle_error.return_value = None
            
            # This should trigger error handling
            with pytest.raises(Exception):
                app.process_single_file("nonexistent.m4a")
            
            # Verify error handler was called
            mock_error_handler.handle_error.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])