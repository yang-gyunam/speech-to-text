"""
File management system for speech-to-text application.

This module provides file system operations including finding audio files,
managing output directories, and generating output filenames.
"""

import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .audio_processor import AudioProcessor
from .exceptions import FileSystemError


class FileManager:
    """
    Manages file system operations for the speech-to-text application.
    
    Handles finding audio files in directories, creating output directories,
    and generating appropriate output filenames.
    """
    
    def __init__(self, audio_processor: Optional[AudioProcessor] = None):
        """
        Initialize FileManager.
        
        Args:
            audio_processor: Optional AudioProcessor instance for file validation
        """
        self.audio_processor = audio_processor or AudioProcessor()
    
    def find_audio_files(self, directory: str, recursive: bool = True) -> List[str]:
        """
        Find all supported audio files in a directory recursively.
        
        Args:
            directory: Path to the directory to search
            recursive: Whether to search subdirectories (default: True)
            
        Returns:
            List of absolute paths to audio files
            
        Raises:
            FileNotFoundError: If directory doesn't exist
            FileSystemError: If directory access fails
        """
        try:
            return self.audio_processor.find_audio_files(directory, recursive)
        except FileNotFoundError:
            raise
        except Exception as e:
            raise FileSystemError(f"Failed to search directory {directory}: {str(e)}")
    
    def create_output_directory(self, path: str) -> str:
        """
        Create output directory if it doesn't exist.
        
        Args:
            path: Path to the output directory
            
        Returns:
            Absolute path to the created directory
            
        Raises:
            FileSystemError: If directory creation fails
        """
        try:
            output_path = Path(path).resolve()
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Verify directory was created and is writable
            if not output_path.exists():
                raise FileSystemError(f"Failed to create directory: {path}")
            
            if not output_path.is_dir():
                raise FileSystemError(f"Path exists but is not a directory: {path}")
            
            # Test write permissions by creating a temporary file
            test_file = output_path / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
            except Exception:
                raise FileSystemError(f"Directory is not writable: {path}")
            
            return str(output_path)
            
        except FileSystemError:
            raise
        except Exception as e:
            raise FileSystemError(f"Failed to create output directory {path}: {str(e)}")
    
    def generate_output_filename(self, input_path: str, output_dir: str, 
                                suffix: str = "", extension: str = ".txt") -> str:
        """
        Generate output filename based on input file path.
        
        Args:
            input_path: Path to the input audio file
            output_dir: Directory where output file will be saved
            suffix: Optional suffix to add to filename (default: "")
            extension: File extension for output file (default: ".txt")
            
        Returns:
            Full path to the output file
            
        Raises:
            FileSystemError: If filename generation fails
        """
        try:
            input_file = Path(input_path)
            output_directory = Path(output_dir)
            
            # Get base filename without extension
            base_name = input_file.stem
            
            # Add suffix if provided
            if suffix:
                base_name = f"{base_name}_{suffix}"
            
            # Ensure extension starts with dot
            if not extension.startswith('.'):
                extension = f".{extension}"
            
            # Always add transcription suffix with timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M")
            transcription_suffix = f"_transcription_{timestamp}"

            # Add transcription suffix to base name
            base_name_with_suffix = f"{base_name}{transcription_suffix}"

            # Generate output filename
            output_filename = f"{base_name_with_suffix}{extension}"
            output_path = output_directory / output_filename
            
            return str(output_path)
            
        except Exception as e:
            raise FileSystemError(f"Failed to generate output filename for {input_path}: {str(e)}")
    
    def ensure_directory_exists(self, file_path: str) -> str:
        """
        Ensure the directory for a file path exists.
        
        Args:
            file_path: Full path to a file
            
        Returns:
            Directory path that was created/verified
            
        Raises:
            FileSystemError: If directory creation fails
        """
        try:
            file_path_obj = Path(file_path)
            directory = file_path_obj.parent
            
            return self.create_output_directory(str(directory))
            
        except Exception as e:
            raise FileSystemError(f"Failed to ensure directory exists for {file_path}: {str(e)}")
    
    def get_file_size(self, file_path: str) -> int:
        """
        Get the size of a file in bytes.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File size in bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
            FileSystemError: If file access fails
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if not path.is_file():
                raise FileSystemError(f"Path is not a file: {file_path}")
            
            return path.stat().st_size
            
        except FileNotFoundError:
            raise
        except Exception as e:
            raise FileSystemError(f"Failed to get file size for {file_path}: {str(e)}")
    
    def is_valid_output_path(self, file_path: str) -> bool:
        """
        Check if a file path is valid for output.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if path is valid for output
        """
        try:
            path = Path(file_path)
            
            # Check if parent directory exists or can be created
            parent_dir = path.parent
            if not parent_dir.exists():
                try:
                    parent_dir.mkdir(parents=True, exist_ok=True)
                except Exception:
                    return False
            
            # Check if parent is a directory
            if not parent_dir.is_dir():
                return False
            
            # Check write permissions
            try:
                test_file = parent_dir / ".write_test"
                test_file.touch()
                test_file.unlink()
                return True
            except Exception:
                return False
                
        except Exception:
            return False
    
    def cleanup_temp_files(self, temp_files: List[str]) -> None:
        """
        Clean up temporary files.
        
        Args:
            temp_files: List of temporary file paths to remove
        """
        for temp_file in temp_files:
            try:
                path = Path(temp_file)
                if path.exists() and path.is_file():
                    path.unlink()
            except Exception:
                # Ignore cleanup errors - they're not critical
                pass
    
    def get_relative_path(self, file_path: str, base_path: str) -> str:
        """
        Get relative path from base path to file path.
        
        Args:
            file_path: Target file path
            base_path: Base directory path
            
        Returns:
            Relative path from base to file
        """
        try:
            file_path_obj = Path(file_path).resolve()
            base_path_obj = Path(base_path).resolve()
            
            return str(file_path_obj.relative_to(base_path_obj))
            
        except ValueError:
            # If paths are not related, return absolute path
            return str(Path(file_path).resolve())
        except Exception:
            # If any error occurs, return original path
            return file_path