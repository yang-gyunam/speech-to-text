"""
Main application class that orchestrates all components for speech-to-text processing.

This module provides the SpeechToTextApp class that coordinates all components
to provide single file and batch processing workflows with proper resource
management and error handling.
"""

import gc
import os
import tempfile
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
from contextlib import contextmanager

from .audio_processor import AudioProcessor
from .file_manager import FileManager
from .transcriber import SpeechTranscriber
from .text_exporter import TextExporter
from .error_handler import ErrorHandler
from .models import TranscriptionResult
from .exceptions import SpeechToTextError, FileSystemError
from .logger import get_logger


class TempFileManager:
    """Thread-safe temporary file manager with automatic cleanup."""
    
    def __init__(self):
        self._temp_files: List[str] = []
        self._lock = threading.Lock()
        self._temp_dir = None
    
    def create_temp_file(self, suffix: str = "", prefix: str = "stt_") -> str:
        """Create a temporary file and track it for cleanup."""
        with self._lock:
            if self._temp_dir is None:
                self._temp_dir = tempfile.mkdtemp(prefix="speech_to_text_")
            
            fd, temp_path = tempfile.mkstemp(
                suffix=suffix, 
                prefix=prefix, 
                dir=self._temp_dir
            )
            os.close(fd)  # Close file descriptor, we just need the path
            
            self._temp_files.append(temp_path)
            return temp_path
    
    def cleanup(self) -> None:
        """Clean up all tracked temporary files and directories."""
        with self._lock:
            for temp_file in self._temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception:
                    pass  # Ignore cleanup errors
            
            if self._temp_dir and os.path.exists(self._temp_dir):
                try:
                    os.rmdir(self._temp_dir)
                except Exception:
                    pass  # Ignore cleanup errors
            
            self._temp_files.clear()
            self._temp_dir = None
    
    def get_temp_count(self) -> int:
        """Get number of tracked temporary files."""
        with self._lock:
            return len(self._temp_files)


class SpeechToTextApp:
    """
    Main application class that orchestrates all components for speech-to-text processing.
    
    This class provides a high-level interface for single file and batch processing
    workflows, handling resource management, temporary files, and error recovery.
    Features performance optimizations including model caching and memory management.
    """
    
    def __init__(self, 
                 model_size: str = "base",
                 language: str = "ko",
                 output_dir: str = "./output",
                 include_metadata: bool = True,
                 optimize_memory: bool = True,
                 use_model_cache: bool = True):
        """
        Initialize the SpeechToTextApp with performance optimizations.
        
        Args:
            model_size: Whisper model size to use
            language: Default language for transcription
            output_dir: Default output directory
            include_metadata: Whether to include metadata in output files
            optimize_memory: Whether to enable memory optimizations
            use_model_cache: Whether to use model caching
        """
        self.model_size = model_size
        self.language = language
        self.output_dir = output_dir
        self.include_metadata = include_metadata
        self.optimize_memory = optimize_memory
        self.use_model_cache = use_model_cache
        
        # Initialize logger
        self.logger = get_logger(__name__)
        
        # Initialize components (lazy loading)
        self._audio_processor = None
        self._file_manager = None
        self._transcriber = None
        self._text_exporter = None
        self._error_handler = None
        
        # Enhanced temporary file management
        self._temp_file_manager = TempFileManager()
        
        self.logger.info(f"SpeechToTextApp initialized with model_size={model_size}, "
                        f"language={language}, optimize_memory={optimize_memory}, "
                        f"use_model_cache={use_model_cache}")
    
    @property
    def audio_processor(self) -> AudioProcessor:
        """Get or create AudioProcessor instance."""
        if self._audio_processor is None:
            self._audio_processor = AudioProcessor()
            self.logger.debug("AudioProcessor initialized")
        return self._audio_processor
    
    @audio_processor.setter
    def audio_processor(self, value: AudioProcessor) -> None:
        """Set AudioProcessor instance."""
        self._audio_processor = value
    
    @audio_processor.deleter
    def audio_processor(self) -> None:
        """Delete AudioProcessor instance."""
        self._audio_processor = None
    
    @property
    def file_manager(self) -> FileManager:
        """Get or create FileManager instance."""
        if self._file_manager is None:
            self._file_manager = FileManager(self.audio_processor)
            self.logger.debug("FileManager initialized")
        return self._file_manager
    
    @file_manager.setter
    def file_manager(self, value: FileManager) -> None:
        """Set FileManager instance."""
        self._file_manager = value
    
    @file_manager.deleter
    def file_manager(self) -> None:
        """Delete FileManager instance."""
        self._file_manager = None
    
    @property
    def transcriber(self) -> SpeechTranscriber:
        """Get or create SpeechTranscriber instance with caching."""
        if self._transcriber is None:
            self.logger.info(f"Loading Whisper model: {self.model_size} (cache: {self.use_model_cache})")
            self._transcriber = SpeechTranscriber(
                model_size=self.model_size,
                use_cache=self.use_model_cache
            )
            self.logger.info("Whisper model loaded successfully")
        return self._transcriber
    
    @transcriber.setter
    def transcriber(self, value: SpeechTranscriber) -> None:
        """Set SpeechTranscriber instance."""
        self._transcriber = value
    
    @transcriber.deleter
    def transcriber(self) -> None:
        """Delete SpeechTranscriber instance."""
        self._transcriber = None
    
    @property
    def text_exporter(self) -> TextExporter:
        """Get or create TextExporter instance."""
        if self._text_exporter is None:
            self._text_exporter = TextExporter()
            self.logger.debug("TextExporter initialized")
        return self._text_exporter
    
    @text_exporter.setter
    def text_exporter(self, value: TextExporter) -> None:
        """Set TextExporter instance."""
        self._text_exporter = value
    
    @text_exporter.deleter
    def text_exporter(self) -> None:
        """Delete TextExporter instance."""
        self._text_exporter = None
    
    @property
    def error_handler(self) -> ErrorHandler:
        """Get or create ErrorHandler instance."""
        if self._error_handler is None:
            self._error_handler = ErrorHandler()
            self.logger.debug("ErrorHandler initialized")
        return self._error_handler
    
    @error_handler.setter
    def error_handler(self, value: ErrorHandler) -> None:
        """Set ErrorHandler instance."""
        self._error_handler = value
    
    @error_handler.deleter
    def error_handler(self) -> None:
        """Delete ErrorHandler instance."""
        self._error_handler = None
    
    def process_single_file(self, 
                          input_path: str,
                          output_path: Optional[str] = None,
                          language: Optional[str] = None) -> TranscriptionResult:
        """
        Process a single audio file and return the transcription result.
        
        Args:
            input_path: Path to the audio file to transcribe
            output_path: Optional output path. If None, generates automatically
            language: Optional language override. If None, uses default
            
        Returns:
            TranscriptionResult: The transcription result
            
        Raises:
            SpeechToTextError: If processing fails
        """
        try:
            self.logger.info(f"Starting single file processing: {input_path}")
            
            # Use provided language or default
            lang = language or self.language
            
            # Validate input file
            self.audio_processor.validate_file(input_path)
            self.logger.debug(f"Input file validated: {input_path}")
            
            # Create output directory
            output_dir = self.file_manager.create_output_directory(self.output_dir)
            self.logger.debug(f"Output directory created: {output_dir}")
            
            # Generate output path if not provided
            if output_path is None:
                output_path = self.file_manager.generate_output_filename(
                    input_path, output_dir
                )
            
            # Transcribe the file with memory optimization
            self.logger.info(f"Transcribing file with language: {lang}")
            result = self.transcriber.transcribe_file(input_path, lang, self.optimize_memory)
            
            if result.error_message:
                self.logger.error(f"Transcription failed: {result.error_message}")
                return result
            
            # Save the result
            self.logger.info(f"Saving transcription to: {output_path}")
            saved_path = self.text_exporter.save_transcription_result(
                result, output_path, include_metadata=self.include_metadata
            )
            
            self.logger.info(f"Single file processing completed successfully: {saved_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"Single file processing failed: {str(e)}")
            self.error_handler.handle_error(e)
            raise
        finally:
            # Clean up any temporary files
            self._cleanup_temp_files()
            # Force garbage collection if memory optimization is enabled
            if self.optimize_memory:
                gc.collect()
    
    def process_batch_files(self,
                          input_paths: List[str],
                          output_dir: Optional[str] = None,
                          language: Optional[str] = None,
                          progress_callback: Optional[Callable[[int, int, str], None]] = None) -> List[TranscriptionResult]:
        """
        Process multiple audio files in batch.
        
        Args:
            input_paths: List of paths to audio files to transcribe
            output_dir: Optional output directory. If None, uses default
            language: Optional language override. If None, uses default
            progress_callback: Optional callback for progress updates
            
        Returns:
            List[TranscriptionResult]: List of transcription results
            
        Raises:
            SpeechToTextError: If batch processing fails
        """
        try:
            self.logger.info(f"Starting batch processing of {len(input_paths)} files")
            
            # Use provided parameters or defaults
            lang = language or self.language
            output_directory = output_dir or self.output_dir
            
            # Create output directory
            output_directory = self.file_manager.create_output_directory(output_directory)
            self.logger.debug(f"Output directory created: {output_directory}")
            
            # Validate all input files first
            valid_files = []
            for file_path in input_paths:
                try:
                    self.audio_processor.validate_file(file_path)
                    valid_files.append(file_path)
                except Exception as e:
                    self.logger.warning(f"Skipping invalid file {file_path}: {str(e)}")
            
            self.logger.info(f"Processing {len(valid_files)} valid files out of {len(input_paths)}")
            
            # Process files with progress tracking
            def batch_progress_callback(current: int, total: int, current_file: str) -> None:
                self.logger.debug(f"Processing file {current + 1}/{total}: {Path(current_file).name}")
                if progress_callback:
                    progress_callback(current, total, current_file)
            
            # Transcribe all files with memory optimization
            results = self.transcriber.transcribe_batch(
                valid_files, 
                language=lang, 
                progress_callback=batch_progress_callback,
                optimize_memory=self.optimize_memory
            )
            
            # Save all results
            self.logger.info("Saving batch transcription results")
            saved_files = self.text_exporter.save_batch_results(
                results, output_directory, create_summary=True
            )
            
            # Log statistics
            successful = len([r for r in results if not r.error_message])
            failed = len(results) - successful
            
            self.logger.info(f"Batch processing completed: {successful} successful, {failed} failed")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {str(e)}")
            self.error_handler.handle_error(e)
            raise
        finally:
            # Clean up any temporary files
            self._cleanup_temp_files()
            # Force garbage collection if memory optimization is enabled
            if self.optimize_memory:
                gc.collect()
    
    def process_directory(self,
                         directory_path: str,
                         recursive: bool = True,
                         output_dir: Optional[str] = None,
                         language: Optional[str] = None,
                         progress_callback: Optional[Callable[[int, int, str], None]] = None) -> List[TranscriptionResult]:
        """
        Process all audio files in a directory.
        
        Args:
            directory_path: Path to directory containing audio files
            recursive: Whether to search subdirectories
            output_dir: Optional output directory. If None, uses default
            language: Optional language override. If None, uses default
            progress_callback: Optional callback for progress updates
            
        Returns:
            List[TranscriptionResult]: List of transcription results
            
        Raises:
            SpeechToTextError: If directory processing fails
        """
        try:
            self.logger.info(f"Starting directory processing: {directory_path}")
            
            # Find all audio files in directory
            audio_files = self.file_manager.find_audio_files(directory_path, recursive)
            
            if not audio_files:
                self.logger.warning(f"No audio files found in directory: {directory_path}")
                return []
            
            self.logger.info(f"Found {len(audio_files)} audio files in directory")
            
            # Process the files as a batch
            return self.process_batch_files(
                audio_files, output_dir, language, progress_callback
            )
            
        except Exception as e:
            self.logger.error(f"Directory processing failed: {str(e)}")
            self.error_handler.handle_error(e)
            raise
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported audio formats.
        
        Returns:
            List of supported file extensions
        """
        return self.audio_processor.get_supported_formats()
    
    def get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary containing audio file information
            
        Raises:
            SpeechToTextError: If file info retrieval fails
        """
        try:
            file_info = self.audio_processor.get_audio_info(file_path)
            return {
                'file_path': file_info.file_path,
                'file_size': file_info.file_size,
                'duration': file_info.duration,
                'format': file_info.format,
                'sample_rate': file_info.sample_rate,
                'channels': file_info.channels
            }
        except Exception as e:
            self.logger.error(f"Failed to get audio info for {file_path}: {str(e)}")
            self.error_handler.handle_error(e)
            raise
    
    def preprocess_audio(self, 
                        input_path: str,
                        normalize: bool = True,
                        remove_silence: bool = False) -> str:
        """
        Preprocess an audio file and return path to processed file.
        
        Args:
            input_path: Path to input audio file
            normalize: Whether to normalize audio levels
            remove_silence: Whether to remove silence
            
        Returns:
            Path to preprocessed audio file
            
        Raises:
            SpeechToTextError: If preprocessing fails
        """
        try:
            self.logger.info(f"Preprocessing audio file: {input_path}")
            
            # Create temporary file for preprocessed audio using temp file manager
            input_ext = Path(input_path).suffix
            temp_path = self._temp_file_manager.create_temp_file(
                suffix=f"_preprocessed{input_ext}",
                prefix=f"{Path(input_path).stem}_"
            )
            
            # Preprocess the audio
            processed_path = self.audio_processor.preprocess_audio(
                input_path, temp_path, normalize, remove_silence
            )
            
            self.logger.info(f"Audio preprocessing completed: {processed_path}")
            return processed_path
            
        except Exception as e:
            self.logger.error(f"Audio preprocessing failed: {str(e)}")
            self.error_handler.handle_error(e)
            raise
    
    def _cleanup_temp_files(self) -> None:
        """Clean up temporary files created during processing."""
        temp_count = self._temp_file_manager.get_temp_count()
        if temp_count > 0:
            self.logger.debug(f"Cleaning up {temp_count} temporary files")
        
        self._temp_file_manager.cleanup()
    
    @contextmanager
    def memory_optimized_processing(self):
        """Context manager for memory-optimized processing."""
        try:
            if self.optimize_memory:
                # Clear any existing model cache before processing
                if hasattr(self, '_transcriber') and self._transcriber:
                    cache_info = self._transcriber.get_cache_info()
                    if cache_info.get('cache_size', 0) > 1:
                        self.logger.debug("Clearing excess models from cache")
                        # Keep only current model in cache
                        self._transcriber.clear_model_cache()
                        # Reload current model
                        self._transcriber = None
            yield
        finally:
            if self.optimize_memory:
                gc.collect()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics and cache information."""
        stats = {
            "model_size": self.model_size,
            "optimize_memory": self.optimize_memory,
            "use_model_cache": self.use_model_cache,
            "temp_files_count": self._temp_file_manager.get_temp_count()
        }
        
        if hasattr(self, '_transcriber') and self._transcriber:
            stats.update(self._transcriber.get_model_info())
        
        return stats
    
    def clear_caches(self) -> None:
        """Clear all caches to free memory."""
        if hasattr(self, '_transcriber') and self._transcriber:
            self._transcriber.clear_model_cache()
        gc.collect()
        self.logger.info("Cleared all caches and forced garbage collection")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self._cleanup_temp_files()
        
        if exc_type is not None:
            self.logger.error(f"Exception occurred in context: {exc_type.__name__}: {exc_val}")
        
        return False  # Don't suppress exceptions
    
    def close(self) -> None:
        """Clean up resources and temporary files."""
        self.logger.info("Closing SpeechToTextApp and cleaning up resources")
        self._cleanup_temp_files()
        self.clear_caches()