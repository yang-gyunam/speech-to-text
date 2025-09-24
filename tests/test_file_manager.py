"""
Unit tests for the FileManager class.

Tests file system operations including finding audio files,
creating output directories, and generating output filenames.
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from src.speech_to_text.file_manager import FileManager
from src.speech_to_text.audio_processor import AudioProcessor
from src.speech_to_text.exceptions import FileSystemError


class TestFileManager:
    """Test cases for FileManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManager()
        
        # Create test directory structure
        self.test_audio_dir = Path(self.temp_dir) / "audio_files"
        self.test_audio_dir.mkdir()
        
        self.test_output_dir = Path(self.temp_dir) / "output"
        
        # Create some test files
        self.test_files = {
            "test1.m4a": self.test_audio_dir / "test1.m4a",
            "test2.wav": self.test_audio_dir / "test2.wav",
            "test3.mp3": self.test_audio_dir / "test3.mp3",
            "not_audio.txt": self.test_audio_dir / "not_audio.txt",
        }
        
        for filename, filepath in self.test_files.items():
            filepath.touch()
        
        # Create subdirectory with audio files
        self.sub_dir = self.test_audio_dir / "subdir"
        self.sub_dir.mkdir()
        self.sub_audio_file = self.sub_dir / "sub_test.aac"
        self.sub_audio_file.touch()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_default_audio_processor(self):
        """Test FileManager initialization with default AudioProcessor."""
        fm = FileManager()
        assert isinstance(fm.audio_processor, AudioProcessor)
    
    def test_init_custom_audio_processor(self):
        """Test FileManager initialization with custom AudioProcessor."""
        mock_processor = Mock(spec=AudioProcessor)
        fm = FileManager(audio_processor=mock_processor)
        assert fm.audio_processor is mock_processor
    
    def test_find_audio_files_recursive(self):
        """Test finding audio files recursively."""
        # Mock the audio processor to return our test files
        expected_files = [
            str(self.test_files["test1.m4a"]),
            str(self.test_files["test2.wav"]),
            str(self.test_files["test3.mp3"]),
            str(self.sub_audio_file)
        ]
        
        with patch.object(self.file_manager.audio_processor, 'find_audio_files') as mock_find:
            mock_find.return_value = expected_files
            
            result = self.file_manager.find_audio_files(str(self.test_audio_dir))
            
            mock_find.assert_called_once_with(str(self.test_audio_dir), True)
            assert result == expected_files
    
    def test_find_audio_files_non_recursive(self):
        """Test finding audio files non-recursively."""
        expected_files = [
            str(self.test_files["test1.m4a"]),
            str(self.test_files["test2.wav"]),
            str(self.test_files["test3.mp3"])
        ]
        
        with patch.object(self.file_manager.audio_processor, 'find_audio_files') as mock_find:
            mock_find.return_value = expected_files
            
            result = self.file_manager.find_audio_files(str(self.test_audio_dir), recursive=False)
            
            mock_find.assert_called_once_with(str(self.test_audio_dir), False)
            assert result == expected_files
    
    def test_find_audio_files_directory_not_found(self):
        """Test finding audio files in non-existent directory."""
        non_existent_dir = str(Path(self.temp_dir) / "non_existent")
        
        with patch.object(self.file_manager.audio_processor, 'find_audio_files') as mock_find:
            mock_find.side_effect = FileNotFoundError(f"Directory not found: {non_existent_dir}")
            
            with pytest.raises(FileNotFoundError):
                self.file_manager.find_audio_files(non_existent_dir)
    
    def test_find_audio_files_access_error(self):
        """Test finding audio files with access error."""
        with patch.object(self.file_manager.audio_processor, 'find_audio_files') as mock_find:
            mock_find.side_effect = PermissionError("Access denied")
            
            with pytest.raises(FileSystemError) as exc_info:
                self.file_manager.find_audio_files(str(self.test_audio_dir))
            
            assert "Failed to search directory" in str(exc_info.value)
    
    def test_create_output_directory_new(self):
        """Test creating a new output directory."""
        output_path = str(self.test_output_dir)
        
        result = self.file_manager.create_output_directory(output_path)
        
        assert result == str(self.test_output_dir.resolve())
        assert self.test_output_dir.exists()
        assert self.test_output_dir.is_dir()
    
    def test_create_output_directory_existing(self):
        """Test creating output directory that already exists."""
        self.test_output_dir.mkdir()
        output_path = str(self.test_output_dir)
        
        result = self.file_manager.create_output_directory(output_path)
        
        assert result == str(self.test_output_dir.resolve())
        assert self.test_output_dir.exists()
    
    def test_create_output_directory_nested(self):
        """Test creating nested output directories."""
        nested_dir = self.test_output_dir / "nested" / "deep"
        output_path = str(nested_dir)
        
        result = self.file_manager.create_output_directory(output_path)
        
        assert result == str(nested_dir.resolve())
        assert nested_dir.exists()
        assert nested_dir.is_dir()
    
    def test_create_output_directory_permission_error(self):
        """Test creating output directory with permission error."""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")
            
            with pytest.raises(FileSystemError) as exc_info:
                self.file_manager.create_output_directory(str(self.test_output_dir))
            
            assert "Failed to create output directory" in str(exc_info.value)
    
    def test_generate_output_filename_basic(self):
        """Test generating basic output filename."""
        input_path = str(self.test_files["test1.m4a"])
        output_dir = str(self.test_output_dir)
        self.test_output_dir.mkdir()
        
        result = self.file_manager.generate_output_filename(input_path, output_dir)
        
        expected = str(self.test_output_dir / "test1.txt")
        assert result == expected
    
    def test_generate_output_filename_with_suffix(self):
        """Test generating output filename with suffix."""
        input_path = str(self.test_files["test1.m4a"])
        output_dir = str(self.test_output_dir)
        self.test_output_dir.mkdir()
        
        result = self.file_manager.generate_output_filename(
            input_path, output_dir, suffix="transcribed"
        )
        
        expected = str(self.test_output_dir / "test1_transcribed.txt")
        assert result == expected
    
    def test_generate_output_filename_custom_extension(self):
        """Test generating output filename with custom extension."""
        input_path = str(self.test_files["test1.m4a"])
        output_dir = str(self.test_output_dir)
        self.test_output_dir.mkdir()
        
        result = self.file_manager.generate_output_filename(
            input_path, output_dir, extension=".json"
        )
        
        expected = str(self.test_output_dir / "test1.json")
        assert result == expected
    
    def test_generate_output_filename_extension_without_dot(self):
        """Test generating output filename with extension without dot."""
        input_path = str(self.test_files["test1.m4a"])
        output_dir = str(self.test_output_dir)
        self.test_output_dir.mkdir()
        
        result = self.file_manager.generate_output_filename(
            input_path, output_dir, extension="json"
        )
        
        expected = str(self.test_output_dir / "test1.json")
        assert result == expected
    
    def test_generate_output_filename_conflict_resolution(self):
        """Test generating output filename with conflict resolution."""
        input_path = str(self.test_files["test1.m4a"])
        output_dir = str(self.test_output_dir)
        self.test_output_dir.mkdir()
        
        # Create existing file
        existing_file = self.test_output_dir / "test1.txt"
        existing_file.touch()
        
        with patch('src.speech_to_text.file_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20231201_143000"
            
            result = self.file_manager.generate_output_filename(input_path, output_dir)
            
            expected = str(self.test_output_dir / "test1_20231201_143000.txt")
            assert result == expected
    
    def test_ensure_directory_exists(self):
        """Test ensuring directory exists for file path."""
        file_path = str(self.test_output_dir / "subdir" / "file.txt")
        
        result = self.file_manager.ensure_directory_exists(file_path)
        
        expected_dir = str((self.test_output_dir / "subdir").resolve())
        assert result == expected_dir
        assert (self.test_output_dir / "subdir").exists()
    
    def test_get_file_size(self):
        """Test getting file size."""
        test_file = self.test_files["test1.m4a"]
        test_content = b"test content"
        test_file.write_bytes(test_content)
        
        result = self.file_manager.get_file_size(str(test_file))
        
        assert result == len(test_content)
    
    def test_get_file_size_not_found(self):
        """Test getting file size for non-existent file."""
        non_existent = str(Path(self.temp_dir) / "non_existent.txt")
        
        with pytest.raises(FileNotFoundError):
            self.file_manager.get_file_size(non_existent)
    
    def test_get_file_size_not_file(self):
        """Test getting file size for directory."""
        with pytest.raises(FileSystemError) as exc_info:
            self.file_manager.get_file_size(str(self.test_audio_dir))
        
        assert "Path is not a file" in str(exc_info.value)
    
    def test_is_valid_output_path_valid(self):
        """Test checking valid output path."""
        self.test_output_dir.mkdir()
        file_path = str(self.test_output_dir / "output.txt")
        
        result = self.file_manager.is_valid_output_path(file_path)
        
        assert result is True
    
    def test_is_valid_output_path_creates_directory(self):
        """Test checking output path that requires directory creation."""
        file_path = str(self.test_output_dir / "output.txt")
        
        result = self.file_manager.is_valid_output_path(file_path)
        
        assert result is True
        assert self.test_output_dir.exists()
    
    def test_is_valid_output_path_invalid(self):
        """Test checking invalid output path."""
        # Create a file where we want a directory
        invalid_parent = self.test_output_dir.parent / "invalid_parent"
        invalid_parent.touch()
        file_path = str(invalid_parent / "output.txt")
        
        result = self.file_manager.is_valid_output_path(file_path)
        
        assert result is False
    
    def test_cleanup_temp_files(self):
        """Test cleaning up temporary files."""
        temp_files = []
        for i in range(3):
            temp_file = Path(self.temp_dir) / f"temp_{i}.tmp"
            temp_file.touch()
            temp_files.append(str(temp_file))
        
        # Add non-existent file to test error handling
        temp_files.append(str(Path(self.temp_dir) / "non_existent.tmp"))
        
        self.file_manager.cleanup_temp_files(temp_files)
        
        # Check that existing files were removed
        for i in range(3):
            temp_file = Path(self.temp_dir) / f"temp_{i}.tmp"
            assert not temp_file.exists()
    
    def test_get_relative_path_related(self):
        """Test getting relative path for related paths."""
        base_path = str(self.test_audio_dir)
        file_path = str(self.test_files["test1.m4a"])
        
        result = self.file_manager.get_relative_path(file_path, base_path)
        
        assert result == "test1.m4a"
    
    def test_get_relative_path_unrelated(self):
        """Test getting relative path for unrelated paths."""
        base_path = "/completely/different/path"
        file_path = str(self.test_files["test1.m4a"])
        
        result = self.file_manager.get_relative_path(file_path, base_path)
        
        # Should return absolute path when paths are unrelated
        assert result == str(Path(file_path).resolve())
    
    def test_get_relative_path_error(self):
        """Test getting relative path with error."""
        # Test with invalid paths - should return the resolved absolute path
        result = self.file_manager.get_relative_path("invalid_path", "invalid_base")
        
        # When paths can't be made relative, it returns the absolute path
        expected = str(Path("invalid_path").resolve())
        assert result == expected