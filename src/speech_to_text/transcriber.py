"""
Speech-to-text transcription engine using OpenAI Whisper.

This module provides the SpeechTranscriber class that handles loading
Whisper models and performing transcription operations on audio files.
"""

import gc
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import whisper

from .exceptions import ModelLoadError, TranscriptionError
from .models import TranscriptionResult


class ModelCache:
    """Thread-safe cache for Whisper models to avoid reloading."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._cache = {}
                    cls._instance._cache_lock = threading.Lock()
        return cls._instance
    
    def get_model(self, model_size: str):
        """Get cached model or load if not cached."""
        with self._cache_lock:
            if model_size not in self._cache:
                try:
                    self._cache[model_size] = whisper.load_model(model_size)
                except Exception as e:
                    raise ModelLoadError(model_size, str(e))
            return self._cache[model_size]
    
    def clear_cache(self):
        """Clear all cached models to free memory."""
        with self._cache_lock:
            self._cache.clear()
            gc.collect()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached models."""
        with self._cache_lock:
            return {
                "cached_models": list(self._cache.keys()),
                "cache_size": len(self._cache)
            }


class SpeechTranscriber:
    """
    Speech-to-text transcriber using OpenAI Whisper models.
    
    This class handles loading Whisper models and performing transcription
    operations on audio files with support for different languages and
    model sizes. Features model caching and memory optimization.
    """
    
    # Available Whisper model sizes
    AVAILABLE_MODELS = ["tiny", "base", "small", "medium", "large"]
    
    def __init__(self, model_size: str = "base", use_cache: bool = True):
        """
        Initialize the SpeechTranscriber with a specific Whisper model.
        
        Args:
            model_size: Size of the Whisper model to use. Options are:
                       "tiny", "base", "small", "medium", "large"
            use_cache: Whether to use model caching to avoid reloading
                       
        Raises:
            ModelLoadError: If the model fails to load
            ValueError: If an invalid model size is provided
        """
        if model_size not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model size '{model_size}'. "
                f"Available models: {', '.join(self.AVAILABLE_MODELS)}"
            )
        
        self.model_size = model_size
        self.use_cache = use_cache
        self._model = None
        self._model_cache = ModelCache() if use_cache else None
        self._load_model()
    
    def _load_model(self) -> None:
        """
        Load the Whisper model using cache if enabled.
        
        Raises:
            ModelLoadError: If the model fails to load
        """
        try:
            if self.use_cache and self._model_cache:
                self._model = self._model_cache.get_model(self.model_size)
            else:
                self._model = whisper.load_model(self.model_size)
        except Exception as e:
            raise ModelLoadError(self.model_size, str(e))
    
    def transcribe_file(
        self, 
        audio_path: str, 
        language: str = "ko",
        optimize_memory: bool = True
    ) -> TranscriptionResult:
        """
        Transcribe a single audio file to text with memory optimization.
        
        Args:
            audio_path: Path to the audio file to transcribe
            language: Language code for transcription (default: "ko" for Korean)
            optimize_memory: Whether to optimize memory usage during transcription
            
        Returns:
            TranscriptionResult: Object containing transcription results and metadata
            
        Raises:
            TranscriptionError: If transcription fails
            FileNotFoundError: If the audio file doesn't exist
        """
        audio_path = str(Path(audio_path).resolve())
        
        # Check if file exists
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        start_time = time.time()
        
        try:
            # Optimize transcription parameters for memory usage
            transcribe_options = {
                "language": language,
                "verbose": True  # Enable verbose output for progress tracking
            }
            
            if optimize_memory:
                # Use smaller chunk size for large files to reduce memory usage
                file_size = Path(audio_path).stat().st_size
                if file_size > 50 * 1024 * 1024:  # 50MB threshold
                    transcribe_options.update({
                        "condition_on_previous_text": False,  # Reduce memory usage
                        "compression_ratio_threshold": 2.4,   # Skip low-quality segments
                        "logprob_threshold": -1.0,           # Skip uncertain segments
                        "no_speech_threshold": 0.6           # Skip silence
                    })
            
            # Perform transcription
            result = self._model.transcribe(audio_path, **transcribe_options)
            
            processing_time = time.time() - start_time
            
            # Extract transcribed text
            transcribed_text = result.get("text", "").strip()
            
            # Calculate confidence score using segment information if available
            confidence_score = self._calculate_confidence_score(result)
            
            # Force garbage collection for memory optimization
            if optimize_memory:
                del result
                gc.collect()
            
            return TranscriptionResult(
                original_file=audio_path,
                transcribed_text=transcribed_text,
                language=language,
                confidence_score=confidence_score,
                processing_time=processing_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Force garbage collection on error
            if optimize_memory:
                gc.collect()
            
            # Return a result with error information
            return TranscriptionResult(
                original_file=audio_path,
                transcribed_text="",
                language=language,
                confidence_score=0.0,
                processing_time=processing_time,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    def transcribe_batch(
        self, 
        file_paths: List[str], 
        language: str = "ko",
        progress_callback: Optional[callable] = None,
        optimize_memory: bool = True,
        gc_frequency: int = 5
    ) -> List[TranscriptionResult]:
        """
        Transcribe multiple audio files in batch with memory optimization.
        
        Args:
            file_paths: List of paths to audio files to transcribe
            language: Language code for transcription (default: "ko" for Korean)
            progress_callback: Optional callback function to report progress.
                             Called with (current_index, total_files, current_file)
            optimize_memory: Whether to optimize memory usage during batch processing
            gc_frequency: How often to run garbage collection (every N files)
            
        Returns:
            List[TranscriptionResult]: List of transcription results for each file
        """
        results = []
        total_files = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            # Report progress if callback is provided
            if progress_callback:
                progress_callback(i, total_files, file_path)
            
            # Transcribe the file with memory optimization
            result = self.transcribe_file(file_path, language, optimize_memory)
            results.append(result)
            
            # Periodic garbage collection for memory management
            if optimize_memory and (i + 1) % gc_frequency == 0:
                gc.collect()
        
        # Final garbage collection
        if optimize_memory:
            gc.collect()
        
        # Report completion
        if progress_callback:
            progress_callback(total_files, total_files, "Batch processing complete")
        
        return results
    
    @property
    def model(self):
        """Get the loaded Whisper model."""
        return self._model
    
    def _calculate_confidence_score(self, whisper_result: Dict[str, Any]) -> float:
        """
        Calculate confidence score from Whisper result segments.
        
        Args:
            whisper_result: Result dictionary from Whisper transcription
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        segments = whisper_result.get("segments", [])
        if not segments:
            # Fallback to simple heuristic
            text = whisper_result.get("text", "").strip()
            return 0.9 if text else 0.0
        
        # Calculate average confidence from segment probabilities
        total_confidence = 0.0
        total_tokens = 0
        
        for segment in segments:
            tokens = segment.get("tokens", [])
            if tokens:
                # Use average log probability as confidence indicator
                avg_logprob = segment.get("avg_logprob", -1.0)
                # Convert log probability to confidence (rough approximation)
                segment_confidence = max(0.0, min(1.0, (avg_logprob + 1.0)))
                total_confidence += segment_confidence * len(tokens)
                total_tokens += len(tokens)
        
        if total_tokens == 0:
            return 0.5  # Default confidence
        
        return total_confidence / total_tokens
    
    def clear_model_cache(self) -> None:
        """Clear the model cache to free memory."""
        if self._model_cache:
            self._model_cache.clear_cache()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the model cache."""
        if self._model_cache:
            return self._model_cache.get_cache_info()
        return {"cached_models": [], "cache_size": 0}
    
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model and cache.
        
        Returns:
            dict: Dictionary containing model information
        """
        info = {
            "model_size": self.model_size,
            "is_loaded": self._model is not None,
            "available_models": self.AVAILABLE_MODELS,
            "use_cache": self.use_cache
        }
        
        if self.use_cache:
            info.update(self.get_cache_info())
        
        return info