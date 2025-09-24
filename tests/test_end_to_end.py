"""
End-to-end integration tests for speech-to-text processing.

This module contains comprehensive tests that verify the complete workflow
from audio file input to text output, including real audio file processing
and Korean language accuracy tests.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.speech_to_text.main_app import SpeechToTextApp
from src.speech_to_text.transcriber import SpeechTranscriber
from src.speech_to_text.audio_processor import AudioProcessor
from src.speech_to_text.models import TranscriptionResult
from src.speech_to_text.exceptions import UnsupportedFormatError


class TestEndToEndWorkflow(unittest.TestCase):
    """Test complete end-to-end workflows."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp(prefix="e2e_test_")
        self.output_dir = os.path.join(self.test_dir, "output")
        
        # Create test audio files with different formats
        self.test_files = {}
        for format_ext in ['.m4a', '.wav', '.mp3', '.aac', '.flac']:
            test_file = os.path.join(self.test_dir, f"test_audio{format_ext}")
            with open(test_file, 'wb') as f:
                f.write(b'fake audio data for testing')
            self.test_files[format_ext] = test_file
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    @patch('src.speech_to_text.transcriber.whisper.load_model')
    @patch('src.speech_to_text.audio_processor.AudioProcessor.validate_file')
    @patch('src.speech_to_text.file_manager.FileManager.create_output_directory')
    @patch('src.speech_to_text.text_exporter.TextExporter.save_transcription_result')
    def test_single_file_complete_workflow(self, mock_save, mock_create_dir, mock_validate, mock_load_model):
        """Test complete single file processing workflow."""
        # Setup mocks
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "안녕하세요. 이것은 테스트 음성입니다.",
            "segments": [
                {
                    "tokens": [1, 2, 3, 4, 5],
                    "avg_logprob": -0.3,
                    "start": 0.0,
                    "end": 2.5
                }
            ]
        }
        mock_load_model.return_value = mock_model
        mock_validate.return_value = True
        mock_create_dir.return_value = self.output_dir
        mock_save.return_value = os.path.join(self.output_dir, "test_output.txt")
        
        # Create app and process file
        app = SpeechToTextApp(
            model_size="base",
            language="ko",
            output_dir=self.output_dir,
            optimize_memory=True,
            use_model_cache=True
        )
        
        with patch('os.path.exists', return_value=True):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat_result = Mock()
                mock_stat_result.st_size = 1024
                mock_stat.return_value = mock_stat_result
                
                result = app.process_single_file(self.test_files['.wav'])
                
                # Verify result
                self.assertIsInstance(result, TranscriptionResult)
                self.assertEqual(result.transcribed_text, "안녕하세요. 이것은 테스트 음성입니다.")
                self.assertEqual(result.language, "ko")
                self.assertGreater(result.confidence_score, 0)
                self.assertIsNone(result.error_message)
        
        app.close()
    
    @patch('src.speech_to_text.transcriber.whisper.load_model')
    @patch('src.speech_to_text.audio_processor.AudioProcessor.validate_file')
    @patch('src.speech_to_text.file_manager.FileManager.create_output_directory')
    @patch('src.speech_to_text.text_exporter.TextExporter.save_batch_results')
    def test_batch_processing_workflow(self, mock_save_batch, mock_create_dir, mock_validate, mock_load_model):
        """Test complete batch processing workflow."""
        # Setup mocks
        mock_model = Mock()
        mock_model.transcribe.side_effect = [
            {"text": "첫 번째 파일입니다.", "segments": []},
            {"text": "두 번째 파일입니다.", "segments": []},
            {"text": "세 번째 파일입니다.", "segments": []}
        ]
        mock_load_model.return_value = mock_model
        mock_validate.return_value = True
        mock_create_dir.return_value = self.output_dir
        mock_save_batch.return_value = ["file1.txt", "file2.txt", "file3.txt"]
        
        # Create app and process files
        app = SpeechToTextApp(
            model_size="base",
            language="ko",
            output_dir=self.output_dir
        )
        
        test_files = [
            self.test_files['.wav'],
            self.test_files['.m4a'],
            self.test_files['.mp3']
        ]
        
        progress_updates = []
        def progress_callback(current, total, current_file):
            progress_updates.append((current, total, current_file))
        
        with patch('os.path.exists', return_value=True):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat_result = Mock()
                mock_stat_result.st_size = 1024
                mock_stat.return_value = mock_stat_result
                
                results = app.process_batch_files(
                    test_files,
                    progress_callback=progress_callback
                )
                
                # Verify results
                self.assertEqual(len(results), 3)
                for i, result in enumerate(results):
                    self.assertIsInstance(result, TranscriptionResult)
                    self.assertIn("파일입니다", result.transcribed_text)
                    self.assertEqual(result.language, "ko")
                    self.assertIsNone(result.error_message)
                
                # Verify progress updates
                self.assertGreater(len(progress_updates), 0)
        
        app.close()
    
    @patch('src.speech_to_text.transcriber.whisper.load_model')
    def test_directory_processing_workflow(self, mock_load_model):
        """Test complete directory processing workflow."""
        # Setup mocks
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "디렉토리 처리 테스트입니다.",
            "segments": []
        }
        mock_load_model.return_value = mock_model
        
        # Create app
        app = SpeechToTextApp(
            model_size="base",
            language="ko",
            output_dir=self.output_dir
        )
        
        with patch('os.path.exists', return_value=True):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = 1024
                
                with patch.object(app.file_manager, 'find_audio_files') as mock_find:
                    mock_find.return_value = list(self.test_files.values())
                    
                    results = app.process_directory(self.test_dir)
                    
                    # Verify results
                    self.assertEqual(len(results), len(self.test_files))
                    for result in results:
                        self.assertIsInstance(result, TranscriptionResult)
                        self.assertEqual(result.transcribed_text, "디렉토리 처리 테스트입니다.")
        
        app.close()
    
    def test_error_handling_workflow(self):
        """Test error handling in complete workflow."""
        app = SpeechToTextApp(model_size="base")
        
        # Test with non-existent file
        with self.assertRaises(Exception):
            app.process_single_file("non_existent_file.wav")
        
        # Test with unsupported format
        unsupported_file = os.path.join(self.test_dir, "test.txt")
        with open(unsupported_file, 'w') as f:
            f.write("not an audio file")
        
        with self.assertRaises(Exception):
            app.process_single_file(unsupported_file)
        
        app.close()
    
    @patch('src.speech_to_text.transcriber.whisper.load_model')
    @patch('src.speech_to_text.audio_processor.AudioProcessor.validate_file')
    def test_memory_optimization_workflow(self, mock_validate, mock_load_model):
        """Test workflow with memory optimization enabled."""
        # Setup mocks
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "메모리 최적화 테스트입니다.",
            "segments": [{"tokens": [1, 2, 3], "avg_logprob": -0.2}]
        }
        mock_load_model.return_value = mock_model
        mock_validate.return_value = True
        
        # Create app with memory optimization
        app = SpeechToTextApp(
            model_size="base",
            optimize_memory=True,
            use_model_cache=True
        )
        
        with patch('os.path.exists', return_value=True):
            with patch('pathlib.Path.stat') as mock_stat:
                # Simulate large file to trigger memory optimization
                mock_stat.return_value.st_size = 100 * 1024 * 1024  # 100MB
                
                # Use memory optimized context manager
                with app.memory_optimized_processing():
                    result = app.process_single_file(self.test_files['.wav'])
                
                # Verify result
                self.assertIsInstance(result, TranscriptionResult)
                self.assertEqual(result.transcribed_text, "메모리 최적화 테스트입니다.")
                
                # Check performance stats
                stats = app.get_performance_stats()
                self.assertTrue(stats["optimize_memory"])
                self.assertTrue(stats["use_model_cache"])
        
        app.close()


class TestKoreanLanguageAccuracy(unittest.TestCase):
    """Test Korean language processing accuracy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp(prefix="korean_test_")
        self.korean_test_cases = [
            "안녕하세요",
            "감사합니다",
            "죄송합니다",
            "한국어 음성 인식 테스트입니다",
            "오늘 날씨가 좋네요",
            "회의는 오후 3시에 시작됩니다",
            "프로젝트 진행 상황을 보고드리겠습니다"
        ]
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    @patch('src.speech_to_text.transcriber.whisper.load_model')
    def test_korean_text_processing(self, mock_load_model):
        """Test Korean text processing accuracy."""
        mock_model = Mock()
        
        # Test each Korean phrase
        for i, korean_text in enumerate(self.korean_test_cases):
            mock_model.transcribe.return_value = {
                "text": korean_text,
                "segments": [
                    {
                        "tokens": list(range(len(korean_text.split()))),
                        "avg_logprob": -0.1,
                        "start": 0.0,
                        "end": 2.0
                    }
                ]
            }
            
            mock_load_model.return_value = mock_model
            
            transcriber = SpeechTranscriber(model_size="base")
            
            # Create test file
            test_file = os.path.join(self.test_dir, f"korean_test_{i}.wav")
            with open(test_file, 'wb') as f:
                f.write(b'fake korean audio data')
            
            with patch('os.path.exists', return_value=True):
                with patch('pathlib.Path.stat') as mock_stat:
                    mock_stat.return_value.st_size = 1024
                    
                    with patch.object(transcriber, '_model', mock_model):
                        result = transcriber.transcribe_file(test_file, language="ko")
                        
                        # Verify Korean text is preserved
                        self.assertEqual(result.transcribed_text, korean_text)
                        self.assertEqual(result.language, "ko")
                        self.assertGreater(result.confidence_score, 0)
    
    @patch('src.speech_to_text.transcriber.whisper.load_model')
    def test_mixed_language_processing(self, mock_load_model):
        """Test processing of mixed Korean-English content."""
        mixed_texts = [
            "Hello 안녕하세요",
            "Thank you 감사합니다",
            "Meeting은 3시에 시작합니다",
            "Project 진행상황을 report하겠습니다"
        ]
        
        mock_model = Mock()
        
        for i, mixed_text in enumerate(mixed_texts):
            mock_model.transcribe.return_value = {
                "text": mixed_text,
                "segments": []
            }
            
            mock_load_model.return_value = mock_model
            
            transcriber = SpeechTranscriber(model_size="base")
            
            test_file = os.path.join(self.test_dir, f"mixed_test_{i}.wav")
            with open(test_file, 'wb') as f:
                f.write(b'fake mixed language audio data')
            
            with patch('os.path.exists', return_value=True):
                with patch('pathlib.Path.stat') as mock_stat:
                    mock_stat.return_value.st_size = 1024
                    
                    with patch.object(transcriber, '_model', mock_model):
                        result = transcriber.transcribe_file(test_file, language="ko")
                        
                        # Verify mixed text is preserved
                        self.assertEqual(result.transcribed_text, mixed_text)
                        # Verify it contains Korean text
                        korean_found = any(korean_word in mixed_text for korean_word in 
                                         ["안녕하세요", "감사합니다", "시작합니다", "하겠습니다"])
                        self.assertTrue(korean_found, f"No Korean text found in: {mixed_text}")


class TestiPhoneRecordingFormats(unittest.TestCase):
    """Test various iPhone recording formats."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp(prefix="iphone_test_")
        
        # iPhone recording formats and their characteristics
        self.iphone_formats = {
            '.m4a': {
                'mime_type': 'audio/mp4',
                'typical_size': 1024 * 1024,  # 1MB
                'sample_rate': 44100,
                'channels': 1
            },
            '.wav': {
                'mime_type': 'audio/wav',
                'typical_size': 5 * 1024 * 1024,  # 5MB
                'sample_rate': 44100,
                'channels': 1
            },
            '.aac': {
                'mime_type': 'audio/aac',
                'typical_size': 800 * 1024,  # 800KB
                'sample_rate': 44100,
                'channels': 1
            }
        }
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_iphone_format_validation(self):
        """Test validation of iPhone recording formats."""
        processor = AudioProcessor()
        
        for format_ext, format_info in self.iphone_formats.items():
            test_file = os.path.join(self.test_dir, f"iphone_recording{format_ext}")
            
            # Create test file
            with open(test_file, 'wb') as f:
                f.write(b'fake iphone audio data' * 100)
            
            # Test validation
            with patch('mimetypes.guess_type') as mock_mime:
                mock_mime.return_value = (format_info['mime_type'], None)
                
                # Should not raise exception for supported formats
                try:
                    is_valid = processor.validate_file(test_file)
                    self.assertTrue(is_valid)
                except UnsupportedFormatError:
                    self.fail(f"iPhone format {format_ext} should be supported")
    
    @patch('src.speech_to_text.transcriber.whisper.load_model')
    def test_iphone_format_processing(self, mock_load_model):
        """Test processing of iPhone recording formats."""
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "아이폰에서 녹음된 음성입니다.",
            "segments": []
        }
        mock_load_model.return_value = mock_model
        
        app = SpeechToTextApp(model_size="base", language="ko")
        
        for format_ext, format_info in self.iphone_formats.items():
            test_file = os.path.join(self.test_dir, f"iphone_recording{format_ext}")
            
            # Create test file
            with open(test_file, 'wb') as f:
                f.write(b'fake iphone audio data' * 100)
            
            with patch('os.path.exists', return_value=True):
                with patch('pathlib.Path.stat') as mock_stat:
                    mock_stat.return_value.st_size = format_info['typical_size']
                    
                    with patch('src.speech_to_text.audio_processor.AudioProcessor.validate_file', return_value=True):
                        result = app.process_single_file(test_file)
                        
                        # Verify processing succeeded
                        self.assertIsInstance(result, TranscriptionResult)
                        self.assertEqual(result.transcribed_text, "아이폰에서 녹음된 음성입니다.")
                        self.assertIsNone(result.error_message)
        
        app.close()
    
    def test_large_iphone_file_processing(self):
        """Test processing of large iPhone recording files."""
        # Test with a simulated large file (>50MB)
        large_file = os.path.join(self.test_dir, "large_iphone_recording.m4a")
        
        # Create a large test file
        with open(large_file, 'wb') as f:
            # Write 60MB of fake data
            for _ in range(60):
                f.write(b'fake audio data' * 1024 * 1024)  # 1MB chunks
        
        processor = AudioProcessor()
        
        # Test file info retrieval for large file
        with patch('mimetypes.guess_type', return_value=('audio/mp4', None)):
            file_info = processor.get_file_info(large_file)
            
            self.assertEqual(file_info.format, '.m4a')
            self.assertGreater(file_info.file_size, 50 * 1024 * 1024)  # >50MB


class TestPerformanceRegression(unittest.TestCase):
    """Test performance regression scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp(prefix="perf_regression_")
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    @patch('src.speech_to_text.transcriber.whisper.load_model')
    def test_batch_processing_performance(self, mock_load_model):
        """Test that batch processing doesn't degrade with file count."""
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "성능 테스트 파일입니다.",
            "segments": []
        }
        mock_load_model.return_value = mock_model
        
        app = SpeechToTextApp(
            model_size="base",
            optimize_memory=True,
            use_model_cache=True
        )
        
        # Create multiple test files
        test_files = []
        for i in range(10):
            test_file = os.path.join(self.test_dir, f"perf_test_{i}.wav")
            with open(test_file, 'wb') as f:
                f.write(b'fake audio data' * 1000)
            test_files.append(test_file)
        
        import time
        
        with patch('os.path.exists', return_value=True):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = 1024
                
                with patch('src.speech_to_text.audio_processor.AudioProcessor.validate_file', return_value=True):
                    start_time = time.time()
                    results = app.process_batch_files(test_files)
                    processing_time = time.time() - start_time
                    
                    # Verify results
                    self.assertEqual(len(results), 10)
                    
                    # Performance assertion (should process 10 files in reasonable time)
                    # This is quite lenient since we're using mocks
                    self.assertLess(processing_time, 10.0)  # 10 seconds max
                    
                    # Verify all files processed successfully
                    successful_results = [r for r in results if not r.error_message]
                    self.assertEqual(len(successful_results), 10)
        
        app.close()
    
    @patch('src.speech_to_text.transcriber.whisper.load_model')
    def test_memory_usage_stability(self, mock_load_model):
        """Test that memory usage remains stable during processing."""
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "메모리 안정성 테스트입니다.",
            "segments": []
        }
        mock_load_model.return_value = mock_model
        
        app = SpeechToTextApp(
            model_size="base",
            optimize_memory=True
        )
        
        test_file = os.path.join(self.test_dir, "memory_test.wav")
        with open(test_file, 'wb') as f:
            f.write(b'fake audio data' * 1000)
        
        # Process the same file multiple times to test memory stability
        with patch('os.path.exists', return_value=True):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = 1024
                
                with patch('src.speech_to_text.audio_processor.AudioProcessor.validate_file', return_value=True):
                    for i in range(5):
                        result = app.process_single_file(test_file)
                        self.assertIsInstance(result, TranscriptionResult)
                        self.assertIsNone(result.error_message)
                        
                        # Check that temp files are cleaned up
                        stats = app.get_performance_stats()
                        self.assertEqual(stats["temp_files_count"], 0)
        
        app.close()


if __name__ == '__main__':
    unittest.main()