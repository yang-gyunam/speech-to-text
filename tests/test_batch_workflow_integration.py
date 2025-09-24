"""
Integration tests for batch processing workflow.

These tests verify the complete batch processing workflow,
including error handling, summary reporting, and resource management.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.speech_to_text.main_app import SpeechToTextApp
from src.speech_to_text.models import TranscriptionResult
from src.speech_to_text.exceptions import (
    SpeechToTextError, 
    UnsupportedFormatError, 
    FileSystemError,
    TranscriptionError
)


class TestBatchWorkflowIntegration:
    """Integration tests for complete batch processing workflows."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def sample_audio_directory(self, temp_dir):
        """Create a directory with multiple audio files."""
        audio_dir = Path(temp_dir) / "audio_files"
        audio_dir.mkdir()
        
        # Create various audio files
        files = []
        for i in range(5):
            audio_file = audio_dir / f"recording_{i}.m4a"
            audio_file.write_bytes(b"fake audio content")
            files.append(str(audio_file))
        
        # Add some files in subdirectory
        sub_dir = audio_dir / "subdirectory"
        sub_dir.mkdir()
        for i in range(2):
            audio_file = sub_dir / f"sub_recording_{i}.wav"
            audio_file.write_bytes(b"fake audio content")
            files.append(str(audio_file))
        
        return str(audio_dir), files
    
    @pytest.fixture
    def mixed_file_directory(self, temp_dir):
        """Create a directory with mixed file types."""
        mixed_dir = Path(temp_dir) / "mixed_files"
        mixed_dir.mkdir()
        
        # Create audio files
        audio_files = []
        for i in range(3):
            audio_file = mixed_dir / f"audio_{i}.m4a"
            audio_file.write_bytes(b"fake audio content")
            audio_files.append(str(audio_file))
        
        # Create non-audio files
        for i in range(2):
            text_file = mixed_dir / f"document_{i}.txt"
            text_file.write_text("This is a text file")
        
        return str(mixed_dir), audio_files
    
    @pytest.fixture
    def mock_successful_results(self, sample_audio_directory):
        """Create mock successful transcription results."""
        _, files = sample_audio_directory
        results = []
        
        for i, file_path in enumerate(files):
            result = TranscriptionResult(
                original_file=file_path,
                transcribed_text=f"안녕하세요. 이것은 테스트 음성 {i}입니다.",
                language="ko",
                confidence_score=0.9 + (i * 0.01),  # Varying confidence
                processing_time=2.0 + (i * 0.5),    # Varying processing time
                timestamp=datetime.now()
            )
            results.append(result)
        
        return results
    
    @pytest.fixture
    def mock_mixed_results(self, sample_audio_directory):
        """Create mock results with some failures."""
        _, files = sample_audio_directory
        results = []
        
        for i, file_path in enumerate(files):
            if i % 3 == 0:  # Every third file fails
                result = TranscriptionResult(
                    original_file=file_path,
                    transcribed_text="",
                    language="ko",
                    confidence_score=0.0,
                    processing_time=1.0,
                    timestamp=datetime.now(),
                    error_message=f"Transcription failed for file {i}"
                )
            else:
                result = TranscriptionResult(
                    original_file=file_path,
                    transcribed_text=f"성공적인 음성 인식 결과 {i}",
                    language="ko",
                    confidence_score=0.85 + (i * 0.02),
                    processing_time=2.5 + (i * 0.3),
                    timestamp=datetime.now()
                )
            results.append(result)
        
        return results
    
    @patch('src.speech_to_text.main_app.SpeechTranscriber')
    @patch('src.speech_to_text.main_app.AudioProcessor')
    def test_complete_batch_workflow_success(self, mock_audio_processor_class,
                                           mock_transcriber_class,
                                           temp_dir, sample_audio_directory,
                                           mock_successful_results):
        """Test complete successful batch processing workflow."""
        audio_dir, files = sample_audio_directory
        
        # Setup mocks
        mock_audio_processor = Mock()
        mock_audio_processor.validate_file.return_value = True
        mock_audio_processor.find_audio_files.return_value = files
        mock_audio_processor_class.return_value = mock_audio_processor
        
        mock_transcriber = Mock()
        mock_transcriber.transcribe_batch.return_value = mock_successful_results
        mock_transcriber_class.return_value = mock_transcriber
        
        # Create app and process directory
        app = SpeechToTextApp(output_dir=temp_dir)
        
        with patch.object(app, 'text_exporter') as mock_text_exporter:
            mock_text_exporter.save_batch_results.return_value = {
                'file1.txt': f'{temp_dir}/file1.txt',
                'file2.txt': f'{temp_dir}/file2.txt',
                '_summary': f'{temp_dir}/summary.txt'
            }
            
            results = app.process_directory(audio_dir, recursive=True)
            
            # Verify the complete workflow
            assert len(results) == len(files)
            assert all(not r.error_message for r in results)
            
            # Verify components were called correctly
            mock_audio_processor.find_audio_files.assert_called_once_with(audio_dir, True)
            mock_transcriber.transcribe_batch.assert_called_once()
            mock_text_exporter.save_batch_results.assert_called_once()
            
            # Verify transcriber was called with correct parameters
            transcribe_call_args = mock_transcriber.transcribe_batch.call_args
            assert len(transcribe_call_args[0][0]) == len(files)  # All files processed
            assert transcribe_call_args[1]['language'] == 'ko'
    
    @patch('src.speech_to_text.main_app.SpeechTranscriber')
    @patch('src.speech_to_text.main_app.AudioProcessor')
    def test_batch_workflow_with_mixed_results(self, mock_audio_processor_class,
                                             mock_transcriber_class,
                                             temp_dir, sample_audio_directory,
                                             mock_mixed_results):
        """Test batch processing with some successful and some failed transcriptions."""
        audio_dir, files = sample_audio_directory
        
        # Setup mocks
        mock_audio_processor = Mock()
        mock_audio_processor.validate_file.return_value = True
        mock_audio_processor.find_audio_files.return_value = files
        mock_audio_processor_class.return_value = mock_audio_processor
        
        mock_transcriber = Mock()
        mock_transcriber.transcribe_batch.return_value = mock_mixed_results
        mock_transcriber_class.return_value = mock_transcriber
        
        app = SpeechToTextApp(output_dir=temp_dir)
        
        with patch.object(app, 'text_exporter') as mock_text_exporter:
            mock_text_exporter.save_batch_results.return_value = {}
            
            results = app.process_directory(audio_dir)
            
            # Verify mixed results
            successful_results = [r for r in results if not r.error_message]
            failed_results = [r for r in results if r.error_message]
            
            assert len(successful_results) > 0
            assert len(failed_results) > 0
            assert len(results) == len(files)
            
            # Verify that text exporter was still called (it should handle failed results)
            mock_text_exporter.save_batch_results.assert_called_once()
    
    @patch('src.speech_to_text.main_app.AudioProcessor')
    def test_batch_workflow_with_invalid_files(self, mock_audio_processor_class,
                                             temp_dir, mixed_file_directory):
        """Test batch processing with mixed valid and invalid files."""
        mixed_dir, audio_files = mixed_file_directory
        
        # Setup mock to validate only audio files
        mock_audio_processor = Mock()
        mock_audio_processor.find_audio_files.return_value = audio_files  # Only return audio files
        mock_audio_processor_class.return_value = mock_audio_processor
        
        app = SpeechToTextApp(output_dir=temp_dir)
        
        with patch.object(app, 'transcriber') as mock_transcriber, \
             patch.object(app, 'text_exporter') as mock_text_exporter:
            
            mock_transcriber.transcribe_batch.return_value = []
            mock_text_exporter.save_batch_results.return_value = {}
            
            results = app.process_directory(mixed_dir)
            
            # Should only process valid audio files
            mock_audio_processor.find_audio_files.assert_called_once_with(mixed_dir, True)
            mock_transcriber.transcribe_batch.assert_called_once()
            
            # Verify only audio files were passed to transcriber
            transcribe_call_args = mock_transcriber.transcribe_batch.call_args[0]
            assert len(transcribe_call_args[0]) == len(audio_files)
    
    @patch('src.speech_to_text.main_app.SpeechTranscriber')
    @patch('src.speech_to_text.main_app.AudioProcessor')
    def test_batch_workflow_with_progress_callback(self, mock_audio_processor_class,
                                                 mock_transcriber_class,
                                                 temp_dir, sample_audio_directory,
                                                 mock_successful_results):
        """Test batch processing with progress callback functionality."""
        audio_dir, files = sample_audio_directory
        
        # Setup mocks
        mock_audio_processor = Mock()
        mock_audio_processor.validate_file.return_value = True
        mock_audio_processor.find_audio_files.return_value = files
        mock_audio_processor_class.return_value = mock_audio_processor
        
        # Mock transcriber to call progress callback
        mock_transcriber = Mock()
        def mock_transcribe_batch(file_paths, language=None, progress_callback=None):
            if progress_callback:
                for i, file_path in enumerate(file_paths):
                    progress_callback(i, len(file_paths), file_path)
            return mock_successful_results
        
        mock_transcriber.transcribe_batch.side_effect = mock_transcribe_batch
        mock_transcriber_class.return_value = mock_transcriber
        
        app = SpeechToTextApp(output_dir=temp_dir)
        
        # Create a mock progress callback
        progress_callback = Mock()
        
        with patch.object(app, 'text_exporter') as mock_text_exporter:
            mock_text_exporter.save_batch_results.return_value = {}
            
            results = app.process_batch_files(files, progress_callback=progress_callback)
            
            # Verify progress callback was called
            assert progress_callback.call_count == len(files)
            
            # Verify callback was called with correct parameters
            for i, call in enumerate(progress_callback.call_args_list):
                args = call[0]
                assert args[0] == i  # current index
                assert args[1] == len(files)  # total files
                assert args[2] == files[i]  # current file
    
    @patch('src.speech_to_text.main_app.AudioProcessor')
    def test_batch_workflow_empty_directory(self, mock_audio_processor_class, temp_dir):
        """Test batch processing with empty directory."""
        empty_dir = Path(temp_dir) / "empty"
        empty_dir.mkdir()
        
        mock_audio_processor = Mock()
        mock_audio_processor.find_audio_files.return_value = []
        mock_audio_processor_class.return_value = mock_audio_processor
        
        app = SpeechToTextApp(output_dir=temp_dir)
        
        results = app.process_directory(str(empty_dir))
        
        assert results == []
        mock_audio_processor.find_audio_files.assert_called_once()
    
    @patch('src.speech_to_text.main_app.SpeechTranscriber')
    @patch('src.speech_to_text.main_app.AudioProcessor')
    def test_batch_workflow_custom_language(self, mock_audio_processor_class,
                                          mock_transcriber_class,
                                          temp_dir, sample_audio_directory,
                                          mock_successful_results):
        """Test batch processing with custom language setting."""
        audio_dir, files = sample_audio_directory
        
        # Setup mocks
        mock_audio_processor = Mock()
        mock_audio_processor.validate_file.return_value = True
        mock_audio_processor.find_audio_files.return_value = files
        mock_audio_processor_class.return_value = mock_audio_processor
        
        mock_transcriber = Mock()
        mock_transcriber.transcribe_batch.return_value = mock_successful_results
        mock_transcriber_class.return_value = mock_transcriber
        
        app = SpeechToTextApp(output_dir=temp_dir, language="ko")  # Default Korean
        
        with patch.object(app, 'text_exporter') as mock_text_exporter:
            mock_text_exporter.save_batch_results.return_value = {}
            
            # Process with English override
            results = app.process_directory(audio_dir, language="en")
            
            # Verify English was used
            transcribe_call_args = mock_transcriber.transcribe_batch.call_args
            assert transcribe_call_args[1]['language'] == 'en'
    
    @patch('src.speech_to_text.main_app.SpeechTranscriber')
    @patch('src.speech_to_text.main_app.AudioProcessor')
    def test_batch_workflow_custom_output_directory(self, mock_audio_processor_class,
                                                  mock_transcriber_class,
                                                  temp_dir, sample_audio_directory,
                                                  mock_successful_results):
        """Test batch processing with custom output directory."""
        audio_dir, files = sample_audio_directory
        custom_output = Path(temp_dir) / "custom_output"
        
        # Setup mocks
        mock_audio_processor = Mock()
        mock_audio_processor.validate_file.return_value = True
        mock_audio_processor.find_audio_files.return_value = files
        mock_audio_processor_class.return_value = mock_audio_processor
        
        mock_transcriber = Mock()
        mock_transcriber.transcribe_batch.return_value = mock_successful_results
        mock_transcriber_class.return_value = mock_transcriber
        
        app = SpeechToTextApp(output_dir=temp_dir)
        
        with patch.object(app, 'file_manager') as mock_file_manager, \
             patch.object(app, 'text_exporter') as mock_text_exporter:
            
            mock_file_manager.find_audio_files.return_value = files
            mock_file_manager.create_output_directory.return_value = str(custom_output)
            mock_text_exporter.save_batch_results.return_value = {}
            
            results = app.process_directory(audio_dir, output_dir=str(custom_output))
            
            # Verify custom output directory was used
            mock_file_manager.create_output_directory.assert_called_with(str(custom_output))
            mock_text_exporter.save_batch_results.assert_called_once()
            save_call_args = mock_text_exporter.save_batch_results.call_args
            assert save_call_args[0][1] == str(custom_output)  # output_dir parameter
    
    @patch('src.speech_to_text.main_app.SpeechTranscriber')
    @patch('src.speech_to_text.main_app.AudioProcessor')
    def test_batch_workflow_recursive_vs_non_recursive(self, mock_audio_processor_class,
                                                      mock_transcriber_class,
                                                      temp_dir, sample_audio_directory,
                                                      mock_successful_results):
        """Test batch processing with recursive and non-recursive directory scanning."""
        audio_dir, all_files = sample_audio_directory
        
        # Separate files by directory level
        main_dir_files = [f for f in all_files if "subdirectory" not in f]
        
        # Setup mocks
        mock_audio_processor = Mock()
        mock_audio_processor.validate_file.return_value = True
        mock_audio_processor_class.return_value = mock_audio_processor
        
        mock_transcriber = Mock()
        mock_transcriber.transcribe_batch.return_value = mock_successful_results
        mock_transcriber_class.return_value = mock_transcriber
        
        app = SpeechToTextApp(output_dir=temp_dir)
        
        with patch.object(app, 'text_exporter') as mock_text_exporter:
            mock_text_exporter.save_batch_results.return_value = {}
            
            # Test recursive=False
            mock_audio_processor.find_audio_files.return_value = main_dir_files
            results_non_recursive = app.process_directory(audio_dir, recursive=False)
            
            # Verify non-recursive call
            find_call_args = mock_audio_processor.find_audio_files.call_args
            assert find_call_args[0][1] == False  # recursive parameter
            
            # Test recursive=True
            mock_audio_processor.find_audio_files.return_value = all_files
            results_recursive = app.process_directory(audio_dir, recursive=True)
            
            # Verify recursive call
            find_call_args = mock_audio_processor.find_audio_files.call_args
            assert find_call_args[0][1] == True  # recursive parameter
    
    def test_batch_workflow_error_handling(self, temp_dir):
        """Test error handling in batch processing workflow."""
        app = SpeechToTextApp(output_dir=temp_dir)
        
        # Test with non-existent directory
        with pytest.raises(Exception):  # Should raise some kind of error
            app.process_directory("/nonexistent/directory")
    
    @patch('src.speech_to_text.main_app.SpeechTranscriber')
    @patch('src.speech_to_text.main_app.AudioProcessor')
    def test_batch_workflow_resource_cleanup(self, mock_audio_processor_class,
                                           mock_transcriber_class,
                                           temp_dir, sample_audio_directory,
                                           mock_successful_results):
        """Test that resources are properly cleaned up after batch processing."""
        audio_dir, files = sample_audio_directory
        
        # Setup mocks
        mock_audio_processor = Mock()
        mock_audio_processor.validate_file.return_value = True
        mock_audio_processor.find_audio_files.return_value = files
        mock_audio_processor_class.return_value = mock_audio_processor
        
        mock_transcriber = Mock()
        mock_transcriber.transcribe_batch.return_value = mock_successful_results
        mock_transcriber_class.return_value = mock_transcriber
        
        # Use context manager to ensure cleanup
        with SpeechToTextApp(output_dir=temp_dir) as app:
            # Add some temporary files to simulate processing
            temp_file = Path(temp_dir) / "temp_processing_file.wav"
            temp_file.write_bytes(b"temp data")
            app._temp_files.append(str(temp_file))
            
            with patch.object(app, 'text_exporter') as mock_text_exporter:
                mock_text_exporter.save_batch_results.return_value = {}
                
                results = app.process_directory(audio_dir)
                
                # Verify processing completed
                assert len(results) == len(files)
        
        # After context exit, temp files should be cleaned up
        assert not temp_file.exists()
        assert app._temp_files == []
    
    @patch('src.speech_to_text.main_app.SpeechTranscriber')
    @patch('src.speech_to_text.main_app.AudioProcessor')
    def test_batch_workflow_summary_reporting(self, mock_audio_processor_class,
                                            mock_transcriber_class,
                                            temp_dir, sample_audio_directory,
                                            mock_mixed_results):
        """Test that batch processing generates proper summary reports."""
        audio_dir, files = sample_audio_directory
        
        # Setup mocks
        mock_audio_processor = Mock()
        mock_audio_processor.validate_file.return_value = True
        mock_audio_processor.find_audio_files.return_value = files
        mock_audio_processor_class.return_value = mock_audio_processor
        
        mock_transcriber = Mock()
        mock_transcriber.transcribe_batch.return_value = mock_mixed_results
        mock_transcriber_class.return_value = mock_transcriber
        
        app = SpeechToTextApp(output_dir=temp_dir)
        
        with patch.object(app, 'text_exporter') as mock_text_exporter:
            # Mock the save_batch_results to return summary info
            mock_text_exporter.save_batch_results.return_value = {
                'file1.txt': f'{temp_dir}/file1.txt',
                'file2.txt': f'{temp_dir}/file2.txt',
                '_summary': f'{temp_dir}/batch_summary.txt'
            }
            
            results = app.process_directory(audio_dir)
            
            # Verify summary was requested
            save_call_args = mock_text_exporter.save_batch_results.call_args
            assert save_call_args[1]['create_summary'] == True
            
            # Verify results contain both successful and failed transcriptions
            successful = [r for r in results if not r.error_message]
            failed = [r for r in results if r.error_message]
            assert len(successful) > 0
            assert len(failed) > 0


class TestBatchWorkflowPerformance:
    """Performance-related tests for batch processing."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def large_file_set(self, temp_dir):
        """Create a large set of files for performance testing."""
        audio_dir = Path(temp_dir) / "large_set"
        audio_dir.mkdir()
        
        files = []
        for i in range(20):  # Create 20 files
            audio_file = audio_dir / f"large_recording_{i:03d}.m4a"
            audio_file.write_bytes(b"fake audio content" * 100)  # Larger fake content
            files.append(str(audio_file))
        
        return str(audio_dir), files
    
    @patch('src.speech_to_text.main_app.SpeechTranscriber')
    @patch('src.speech_to_text.main_app.AudioProcessor')
    def test_batch_processing_large_file_set(self, mock_audio_processor_class,
                                           mock_transcriber_class,
                                           temp_dir, large_file_set):
        """Test batch processing with a large number of files."""
        audio_dir, files = large_file_set
        
        # Create mock results for all files
        mock_results = []
        for i, file_path in enumerate(files):
            result = TranscriptionResult(
                original_file=file_path,
                transcribed_text=f"Large file transcription {i}",
                language="ko",
                confidence_score=0.9,
                processing_time=1.0,
                timestamp=datetime.now()
            )
            mock_results.append(result)
        
        # Setup mocks
        mock_audio_processor = Mock()
        mock_audio_processor.validate_file.return_value = True
        mock_audio_processor.find_audio_files.return_value = files
        mock_audio_processor_class.return_value = mock_audio_processor
        
        mock_transcriber = Mock()
        mock_transcriber.transcribe_batch.return_value = mock_results
        mock_transcriber_class.return_value = mock_transcriber
        
        app = SpeechToTextApp(output_dir=temp_dir)
        
        with patch.object(app, 'text_exporter') as mock_text_exporter:
            mock_text_exporter.save_batch_results.return_value = {}
            
            # Process large file set
            results = app.process_directory(audio_dir)
            
            # Verify all files were processed
            assert len(results) == len(files)
            assert all(not r.error_message for r in results)
            
            # Verify batch processing was used (not individual file processing)
            mock_transcriber.transcribe_batch.assert_called_once()
            transcribe_call_args = mock_transcriber.transcribe_batch.call_args[0]
            assert len(transcribe_call_args[0]) == len(files)


if __name__ == "__main__":
    pytest.main([__file__])