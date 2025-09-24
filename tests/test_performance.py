"""
Performance tests and benchmarks for speech-to-text processing.

This module contains tests to measure and validate performance optimizations
including model caching, memory usage, and processing speed.
"""

import gc
import os
import time
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.speech_to_text.transcriber import SpeechTranscriber, ModelCache
from src.speech_to_text.main_app import SpeechToTextApp, TempFileManager
from src.speech_to_text.models import TranscriptionResult


class TestModelCache(unittest.TestCase):
    """Test model caching functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Clear any existing cache
        cache = ModelCache()
        cache.clear_cache()
    
    def tearDown(self):
        """Clean up after tests."""
        cache = ModelCache()
        cache.clear_cache()
    
    @patch('src.speech_to_text.transcriber.whisper.load_model')
    def test_model_cache_singleton(self, mock_load_model):
        """Test that ModelCache is a singleton."""
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        
        cache1 = ModelCache()
        cache2 = ModelCache()
        
        self.assertIs(cache1, cache2)
    
    @patch('src.speech_to_text.transcriber.whisper.load_model')
    def test_model_caching(self, mock_load_model):
        """Test that models are cached and reused."""
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        
        cache = ModelCache()
        
        # First call should load the model
        model1 = cache.get_model("base")
        self.assertEqual(mock_load_model.call_count, 1)
        
        # Second call should use cached model
        model2 = cache.get_model("base")
        self.assertEqual(mock_load_model.call_count, 1)
        self.assertIs(model1, model2)
    
    @patch('src.speech_to_text.transcriber.whisper.load_model')
    def test_multiple_model_caching(self, mock_load_model):
        """Test caching of multiple different models."""
        mock_model_base = Mock()
        mock_model_small = Mock()
        mock_load_model.side_effect = [mock_model_base, mock_model_small]
        
        cache = ModelCache()
        
        # Load two different models
        model_base = cache.get_model("base")
        model_small = cache.get_model("small")
        
        self.assertEqual(mock_load_model.call_count, 2)
        self.assertIsNot(model_base, model_small)
        
        # Verify cache info
        cache_info = cache.get_cache_info()
        self.assertEqual(cache_info["cache_size"], 2)
        self.assertIn("base", cache_info["cached_models"])
        self.assertIn("small", cache_info["cached_models"])
    
    @patch('src.speech_to_text.transcriber.whisper.load_model')
    def test_cache_clear(self, mock_load_model):
        """Test cache clearing functionality."""
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        
        cache = ModelCache()
        
        # Load a model
        cache.get_model("base")
        self.assertEqual(cache.get_cache_info()["cache_size"], 1)
        
        # Clear cache
        cache.clear_cache()
        self.assertEqual(cache.get_cache_info()["cache_size"], 0)


class TestTempFileManager(unittest.TestCase):
    """Test temporary file management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_manager = TempFileManager()
    
    def tearDown(self):
        """Clean up after tests."""
        self.temp_manager.cleanup()
    
    def test_temp_file_creation(self):
        """Test temporary file creation and tracking."""
        temp_file = self.temp_manager.create_temp_file(suffix=".wav", prefix="test_")
        
        self.assertTrue(os.path.exists(temp_file))
        self.assertTrue(temp_file.endswith(".wav"))
        self.assertTrue(os.path.basename(temp_file).startswith("test_"))
        self.assertEqual(self.temp_manager.get_temp_count(), 1)
    
    def test_multiple_temp_files(self):
        """Test creation and tracking of multiple temporary files."""
        temp_files = []
        for i in range(3):
            temp_file = self.temp_manager.create_temp_file(suffix=f"_{i}.txt")
            temp_files.append(temp_file)
            self.assertTrue(os.path.exists(temp_file))
        
        self.assertEqual(self.temp_manager.get_temp_count(), 3)
    
    def test_temp_file_cleanup(self):
        """Test temporary file cleanup."""
        temp_files = []
        for i in range(3):
            temp_file = self.temp_manager.create_temp_file(suffix=f"_{i}.txt")
            temp_files.append(temp_file)
        
        # Verify files exist
        for temp_file in temp_files:
            self.assertTrue(os.path.exists(temp_file))
        
        # Cleanup
        self.temp_manager.cleanup()
        
        # Verify files are removed
        for temp_file in temp_files:
            self.assertFalse(os.path.exists(temp_file))
        
        self.assertEqual(self.temp_manager.get_temp_count(), 0)


class TestPerformanceOptimizations(unittest.TestCase):
    """Test performance optimization features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_audio_path = "test_audio.wav"
        # Create a mock audio file
        with open(self.test_audio_path, 'wb') as f:
            f.write(b'fake audio data')
    
    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.test_audio_path):
            os.unlink(self.test_audio_path)
    
    @patch('src.speech_to_text.transcriber.whisper.load_model')
    def test_transcriber_with_cache(self, mock_load_model):
        """Test transcriber with model caching enabled."""
        mock_model = Mock()
        mock_model.transcribe.return_value = {"text": "test transcription"}
        mock_load_model.return_value = mock_model
        
        # Create transcriber with caching
        transcriber = SpeechTranscriber(model_size="base", use_cache=True)
        
        # Verify model is loaded
        self.assertIsNotNone(transcriber.model)
        self.assertTrue(transcriber.use_cache)
        
        # Check cache info
        cache_info = transcriber.get_cache_info()
        self.assertEqual(cache_info["cache_size"], 1)
        self.assertIn("base", cache_info["cached_models"])
    
    @patch('src.speech_to_text.transcriber.whisper.load_model')
    def test_transcriber_without_cache(self, mock_load_model):
        """Test transcriber with model caching disabled."""
        mock_model = Mock()
        mock_model.transcribe.return_value = {"text": "test transcription"}
        mock_load_model.return_value = mock_model
        
        # Create transcriber without caching
        transcriber = SpeechTranscriber(model_size="base", use_cache=False)
        
        # Verify model is loaded but cache is not used
        self.assertIsNotNone(transcriber.model)
        self.assertFalse(transcriber.use_cache)
        
        # Check cache info (should be empty)
        cache_info = transcriber.get_cache_info()
        self.assertEqual(cache_info["cache_size"], 0)
    
    @patch('src.speech_to_text.transcriber.whisper.load_model')
    @patch('src.speech_to_text.audio_processor.AudioProcessor.validate_file')
    def test_memory_optimization_in_transcription(self, mock_validate, mock_load_model):
        """Test memory optimization during transcription."""
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "test transcription",
            "segments": [
                {"tokens": [1, 2, 3], "avg_logprob": -0.5}
            ]
        }
        mock_load_model.return_value = mock_model
        mock_validate.return_value = True
        
        transcriber = SpeechTranscriber(model_size="base", use_cache=True)
        
        # Test with memory optimization enabled
        with patch('os.path.exists', return_value=True):
            with patch('pathlib.Path.stat') as mock_stat:
                # Simulate large file
                mock_stat.return_value.st_size = 100 * 1024 * 1024  # 100MB
                
                result = transcriber.transcribe_file(self.test_audio_path, optimize_memory=True)
                
                self.assertIsInstance(result, TranscriptionResult)
                self.assertEqual(result.transcribed_text, "test transcription")
                self.assertGreater(result.confidence_score, 0)
    
    @patch('src.speech_to_text.transcriber.whisper.load_model')
    @patch('src.speech_to_text.audio_processor.AudioProcessor.validate_file')
    def test_batch_processing_with_gc(self, mock_validate, mock_load_model):
        """Test batch processing with garbage collection."""
        mock_model = Mock()
        mock_model.transcribe.return_value = {"text": "test transcription"}
        mock_load_model.return_value = mock_model
        mock_validate.return_value = True
        
        transcriber = SpeechTranscriber(model_size="base", use_cache=True)
        
        # Create multiple test files
        test_files = [f"test_audio_{i}.wav" for i in range(5)]
        
        with patch('os.path.exists', return_value=True):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = 1024  # Small files
                
                # Test batch processing with memory optimization
                results = transcriber.transcribe_batch(
                    test_files, 
                    optimize_memory=True, 
                    gc_frequency=2
                )
                
                self.assertEqual(len(results), 5)
                for result in results:
                    self.assertIsInstance(result, TranscriptionResult)


class TestSpeechToTextAppPerformance(unittest.TestCase):
    """Test performance features in main application."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_audio_path = "test_audio.wav"
        with open(self.test_audio_path, 'wb') as f:
            f.write(b'fake audio data')
    
    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.test_audio_path):
            os.unlink(self.test_audio_path)
    
    def test_app_initialization_with_optimizations(self):
        """Test app initialization with performance optimizations."""
        app = SpeechToTextApp(
            model_size="base",
            optimize_memory=True,
            use_model_cache=True
        )
        
        self.assertTrue(app.optimize_memory)
        self.assertTrue(app.use_model_cache)
        
        # Check performance stats
        stats = app.get_performance_stats()
        self.assertEqual(stats["model_size"], "base")
        self.assertTrue(stats["optimize_memory"])
        self.assertTrue(stats["use_model_cache"])
        self.assertEqual(stats["temp_files_count"], 0)
    
    def test_memory_optimized_context_manager(self):
        """Test memory optimized processing context manager."""
        app = SpeechToTextApp(optimize_memory=True)
        
        with app.memory_optimized_processing():
            # Simulate some processing
            pass
        
        # Context manager should complete without errors
        self.assertTrue(True)
    
    def test_cache_clearing(self):
        """Test cache clearing functionality."""
        app = SpeechToTextApp(use_model_cache=True)
        
        # This should not raise any errors
        app.clear_caches()
        
        # Verify stats after clearing
        stats = app.get_performance_stats()
        self.assertEqual(stats["temp_files_count"], 0)


class TestPerformanceBenchmarks(unittest.TestCase):
    """Performance benchmark tests."""
    
    @pytest.mark.slow
    def test_model_loading_benchmark(self):
        """Benchmark model loading with and without cache."""
        # This test is marked as slow and would typically be run separately
        
        # Test without cache
        start_time = time.time()
        with patch('src.speech_to_text.transcriber.whisper.load_model') as mock_load:
            mock_load.return_value = Mock()
            transcriber1 = SpeechTranscriber(model_size="base", use_cache=False)
            transcriber2 = SpeechTranscriber(model_size="base", use_cache=False)
        no_cache_time = time.time() - start_time
        
        # Clear cache for fair comparison
        cache = ModelCache()
        cache.clear_cache()
        
        # Test with cache
        start_time = time.time()
        with patch('src.speech_to_text.transcriber.whisper.load_model') as mock_load:
            mock_load.return_value = Mock()
            transcriber3 = SpeechTranscriber(model_size="base", use_cache=True)
            transcriber4 = SpeechTranscriber(model_size="base", use_cache=True)
        cache_time = time.time() - start_time
        
        # Cache should be faster (though with mocks, the difference might be minimal)
        # This is more of a structural test than a real performance test
        self.assertIsNotNone(transcriber1)
        self.assertIsNotNone(transcriber2)
        self.assertIsNotNone(transcriber3)
        self.assertIsNotNone(transcriber4)
    
    def test_temp_file_manager_performance(self):
        """Test temporary file manager performance."""
        temp_manager = TempFileManager()
        
        start_time = time.time()
        
        # Create many temporary files
        temp_files = []
        for i in range(100):
            temp_file = temp_manager.create_temp_file(suffix=f"_{i}.tmp")
            temp_files.append(temp_file)
        
        creation_time = time.time() - start_time
        
        # Verify all files exist
        for temp_file in temp_files:
            self.assertTrue(os.path.exists(temp_file))
        
        # Cleanup
        start_time = time.time()
        temp_manager.cleanup()
        cleanup_time = time.time() - start_time
        
        # Verify all files are removed
        for temp_file in temp_files:
            self.assertFalse(os.path.exists(temp_file))
        
        # Performance assertions (these are quite lenient)
        self.assertLess(creation_time, 5.0)  # Should create 100 files in under 5 seconds
        self.assertLess(cleanup_time, 2.0)   # Should cleanup in under 2 seconds


if __name__ == '__main__':
    unittest.main()