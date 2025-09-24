"""Audio file processing module for speech-to-text conversion."""

import os
import mimetypes
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

try:
    from pydub import AudioSegment
    from pydub.effects import normalize
    from pydub.silence import split_on_silence
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

from .exceptions import UnsupportedFormatError, AudioProcessingError, AudioConversionError


@dataclass
class AudioFileInfo:
    """Information about an audio file."""
    file_path: str
    file_size: int
    duration: Optional[float] = None
    format: Optional[str] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None


class AudioProcessor:
    """Handles audio file validation and processing operations."""
    
    # Supported audio formats for iPhone recordings and common formats
    SUPPORTED_FORMATS = {'.m4a', '.wav', '.mp3', '.aac', '.flac'}
    
    # MIME type mappings for additional validation
    MIME_TYPE_MAPPING = {
        'audio/mp4': '.m4a',
        'audio/x-m4a': '.m4a',
        'audio/wav': '.wav',
        'audio/x-wav': '.wav',
        'audio/mpeg': '.mp3',
        'audio/mp3': '.mp3',
        'audio/aac': '.aac',
        'audio/x-aac': '.aac',
        'audio/flac': '.flac',
        'audio/x-flac': '.flac'
    }
    
    def __init__(self):
        """Initialize the AudioProcessor."""
        # Initialize mimetypes for better format detection
        mimetypes.init()
    
    def validate_file(self, file_path: str) -> bool:
        """
        Validate if the file exists and is a supported audio format.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            True if file is valid and supported
            
        Raises:
            FileNotFoundError: If file doesn't exist
            UnsupportedFormatError: If file format is not supported
        """
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        # Check if it's a file (not a directory)
        if not path.is_file():
            raise FileNotFoundError(f"Path is not a file: {file_path}")
        
        # Check file extension
        file_extension = path.suffix.lower()
        if not self._is_supported_format(file_extension):
            raise UnsupportedFormatError(
                f"Unsupported file format: {file_extension}. "
                f"Supported formats: {', '.join(sorted(self.SUPPORTED_FORMATS))}"
            )
        
        # Additional MIME type validation
        if not self._validate_mime_type(file_path, file_extension):
            raise UnsupportedFormatError(
                f"File MIME type doesn't match extension: {file_path}"
            )
        
        return True
    
    def get_file_info(self, file_path: str) -> AudioFileInfo:
        """
        Get basic information about an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            AudioFileInfo object with file metadata
        """
        # First validate the file
        self.validate_file(file_path)
        
        path = Path(file_path)
        file_size = path.stat().st_size
        file_format = path.suffix.lower()
        
        return AudioFileInfo(
            file_path=str(path.absolute()),
            file_size=file_size,
            format=file_format
        )
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported audio formats.
        
        Returns:
            List of supported file extensions
        """
        return sorted(list(self.SUPPORTED_FORMATS))
    
    def _is_supported_format(self, file_extension: str) -> bool:
        """
        Check if file extension is supported.
        
        Args:
            file_extension: File extension (with dot)
            
        Returns:
            True if format is supported
        """
        return file_extension.lower() in self.SUPPORTED_FORMATS
    
    def _validate_mime_type(self, file_path: str, expected_extension: str) -> bool:
        """
        Validate file MIME type matches the expected extension.
        
        Args:
            file_path: Path to the file
            expected_extension: Expected file extension
            
        Returns:
            True if MIME type is valid or cannot be determined
        """
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                # If we can't determine MIME type, assume it's valid
                return True
            
            # Check if MIME type matches expected extension
            expected_from_mime = self.MIME_TYPE_MAPPING.get(mime_type)
            if expected_from_mime is None:
                # Unknown MIME type, assume valid
                return True
            
            return expected_from_mime == expected_extension.lower()
        
        except Exception:
            # If MIME type detection fails, assume valid
            return True
    
    def find_audio_files(self, directory_path: str, recursive: bool = True) -> List[str]:
        """
        Find all supported audio files in a directory.
        
        Args:
            directory_path: Path to search directory
            recursive: Whether to search subdirectories
            
        Returns:
            List of audio file paths
            
        Raises:
            FileNotFoundError: If directory doesn't exist
        """
        path = Path(directory_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if not path.is_dir():
            raise FileNotFoundError(f"Path is not a directory: {directory_path}")
        
        audio_files = []
        
        # Search pattern based on recursive flag
        search_pattern = "**/*" if recursive else "*"
        
        for file_path in path.glob(search_pattern):
            if file_path.is_file():
                file_extension = file_path.suffix.lower()
                if self._is_supported_format(file_extension):
                    try:
                        # Validate each file before adding to list
                        self.validate_file(str(file_path))
                        audio_files.append(str(file_path.absolute()))
                    except (UnsupportedFormatError, FileNotFoundError):
                        # Skip invalid files
                        continue
        
        return sorted(audio_files)
    
    def convert_to_wav(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Convert audio file to WAV format.
        
        Args:
            input_path: Path to input audio file
            output_path: Optional output path. If None, creates temp file
            
        Returns:
            Path to converted WAV file
            
        Raises:
            AudioConversionError: If conversion fails
            FileNotFoundError: If input file doesn't exist
        """
        if not PYDUB_AVAILABLE:
            raise AudioConversionError(
                input_path, 
                "wav", 
                "pydub is not available. Please install it with: pip install pydub"
            )
        
        # Validate input file first
        self.validate_file(input_path)
        
        try:
            # Load audio file
            audio = self._load_audio_file(input_path)
            
            # Generate output path if not provided
            if output_path is None:
                temp_dir = tempfile.gettempdir()
                input_name = Path(input_path).stem
                output_path = os.path.join(temp_dir, f"{input_name}_converted.wav")
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Export as WAV
            audio.export(output_path, format="wav")
            
            return output_path
            
        except Exception as e:
            raise AudioConversionError(input_path, "wav", str(e))
    
    def preprocess_audio(self, input_path: str, output_path: Optional[str] = None, 
                        normalize_audio: bool = True, remove_silence: bool = False) -> str:
        """
        Preprocess audio file with normalization and noise reduction.
        
        Args:
            input_path: Path to input audio file
            output_path: Optional output path. If None, creates temp file
            normalize_audio: Whether to normalize audio levels
            remove_silence: Whether to remove silence from beginning/end
            
        Returns:
            Path to preprocessed audio file
            
        Raises:
            AudioProcessingError: If preprocessing fails
        """
        if not PYDUB_AVAILABLE:
            raise AudioProcessingError(
                "preprocessing", 
                input_path,
                "pydub is not available. Please install it with: pip install pydub"
            )
        
        # Validate input file first
        self.validate_file(input_path)
        
        try:
            # Load audio file
            audio = self._load_audio_file(input_path)
            
            # Apply preprocessing steps
            if normalize_audio:
                audio = normalize(audio)
            
            if remove_silence:
                audio = self._remove_silence(audio)
            
            # Generate output path if not provided
            if output_path is None:
                temp_dir = tempfile.gettempdir()
                input_name = Path(input_path).stem
                input_ext = Path(input_path).suffix
                output_path = os.path.join(temp_dir, f"{input_name}_preprocessed{input_ext}")
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Export preprocessed audio
            output_format = Path(output_path).suffix[1:]  # Remove dot from extension
            audio.export(output_path, format=output_format)
            
            return output_path
            
        except Exception as e:
            raise AudioProcessingError("preprocessing", input_path, str(e))
    
    def get_audio_info(self, file_path: str) -> AudioFileInfo:
        """
        Get detailed audio information including duration, sample rate, etc.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            AudioFileInfo with detailed metadata
        """
        # First get basic file info
        file_info = self.get_file_info(file_path)
        
        if not PYDUB_AVAILABLE:
            # Return basic info if pydub not available
            return file_info
        
        try:
            # Load audio to get detailed info
            audio = self._load_audio_file(file_path)
            
            # Update file info with audio details
            file_info.duration = len(audio) / 1000.0  # Convert ms to seconds
            file_info.sample_rate = audio.frame_rate
            file_info.channels = audio.channels
            
            return file_info
            
        except Exception:
            # Return basic info if audio loading fails
            return file_info
    
    def _load_audio_file(self, file_path: str) -> 'AudioSegment':
        """
        Load audio file using pydub.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            AudioSegment object
            
        Raises:
            AudioProcessingError: If loading fails
        """
        if not PYDUB_AVAILABLE:
            raise AudioProcessingError(
                "loading", 
                file_path,
                "pydub is not available"
            )
        
        try:
            file_extension = Path(file_path).suffix.lower()
            
            # Handle different audio formats
            if file_extension == '.m4a':
                return AudioSegment.from_file(file_path, format="m4a")
            elif file_extension == '.wav':
                return AudioSegment.from_wav(file_path)
            elif file_extension == '.mp3':
                return AudioSegment.from_mp3(file_path)
            elif file_extension == '.aac':
                return AudioSegment.from_file(file_path, format="aac")
            elif file_extension == '.flac':
                return AudioSegment.from_file(file_path, format="flac")
            else:
                # Try generic loading
                return AudioSegment.from_file(file_path)
                
        except Exception as e:
            raise AudioProcessingError("loading", file_path, str(e))
    
    def _remove_silence(self, audio: 'AudioSegment', silence_thresh: int = -40, 
                       min_silence_len: int = 500) -> 'AudioSegment':
        """
        Remove silence from audio.
        
        Args:
            audio: AudioSegment to process
            silence_thresh: Silence threshold in dBFS
            min_silence_len: Minimum silence length in ms
            
        Returns:
            AudioSegment with silence removed
        """
        try:
            # Split on silence and rejoin
            chunks = split_on_silence(
                audio,
                min_silence_len=min_silence_len,
                silence_thresh=silence_thresh,
                keep_silence=100  # Keep 100ms of silence for natural sound
            )
            
            if not chunks:
                # If no chunks found, return original audio
                return audio
            
            # Rejoin chunks
            processed_audio = chunks[0]
            for chunk in chunks[1:]:
                processed_audio += chunk
            
            return processed_audio
            
        except Exception:
            # If silence removal fails, return original audio
            return audio