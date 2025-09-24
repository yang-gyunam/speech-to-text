"""Unit tests for the AudioProcessor class."""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.speech_to_text.audio_processor import AudioProcessor, AudioFileInfo, PYDUB_AVAILABLE
from src.speech_to_text.exceptions import UnsupportedFormatError, AudioProcessingError, AudioConversionError


class TestAudioProcessor:
    """Test cases for AudioProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = AudioProcessor()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_temp_file(self, filename: str, content: bytes = b"fake audio data") -> str:
        """Create a temporary file for testing."""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(content)
        return file_path
    
    def test_init(self):
        """Test AudioProcessor initialization."""
        processor = AudioProcessor()
        assert processor.SUPPORTED_FORMATS == {'.m4a', '.wav', '.mp3', '.aac', '.flac'}
        assert len(processor.MIME_TYPE_MAPPING) > 0
    
    def test_get_supported_formats(self):
        """Test getting supported formats list."""
        formats = self.processor.get_supported_formats()
        expected_formats = ['.aac', '.flac', '.m4a', '.mp3', '.wav']
        assert formats == expected_formats
        assert isinstance(formats, list)
    
    def test_validate_file_success_m4a(self):
        """Test successful validation of .m4a file."""
        file_path = self.create_temp_file("test.m4a")
        
        with patch.object(self.processor, '_validate_mime_type', return_value=True):
            result = self.processor.validate_file(file_path)
            assert result is True
    
    def test_validate_file_success_wav(self):
        """Test successful validation of .wav file."""
        file_path = self.create_temp_file("test.wav")
        
        with patch.object(self.processor, '_validate_mime_type', return_value=True):
            result = self.processor.validate_file(file_path)
            assert result is True
    
    def test_validate_file_success_mp3(self):
        """Test successful validation of .mp3 file."""
        file_path = self.create_temp_file("test.mp3")
        
        with patch.object(self.processor, '_validate_mime_type', return_value=True):
            result = self.processor.validate_file(file_path)
            assert result is True
    
    def test_validate_file_success_aac(self):
        """Test successful validation of .aac file."""
        file_path = self.create_temp_file("test.aac")
        
        with patch.object(self.processor, '_validate_mime_type', return_value=True):
            result = self.processor.validate_file(file_path)
            assert result is True
    
    def test_validate_file_success_flac(self):
        """Test successful validation of .flac file."""
        file_path = self.create_temp_file("test.flac")
        
        with patch.object(self.processor, '_validate_mime_type', return_value=True):
            result = self.processor.validate_file(file_path)
            assert result is True
    
    def test_validate_file_case_insensitive(self):
        """Test validation works with uppercase extensions."""
        file_path = self.create_temp_file("test.M4A")
        
        with patch.object(self.processor, '_validate_mime_type', return_value=True):
            result = self.processor.validate_file(file_path)
            assert result is True
    
    def test_validate_file_not_found(self):
        """Test validation fails when file doesn't exist."""
        non_existent_file = os.path.join(self.temp_dir, "nonexistent.m4a")
        
        with pytest.raises(FileNotFoundError) as exc_info:
            self.processor.validate_file(non_existent_file)
        
        assert "Audio file not found" in str(exc_info.value)
        assert non_existent_file in str(exc_info.value)
    
    def test_validate_file_is_directory(self):
        """Test validation fails when path is a directory."""
        with pytest.raises(FileNotFoundError) as exc_info:
            self.processor.validate_file(self.temp_dir)
        
        assert "Path is not a file" in str(exc_info.value)
    
    def test_validate_file_unsupported_format(self):
        """Test validation fails for unsupported file formats."""
        file_path = self.create_temp_file("test.txt")
        
        with pytest.raises(UnsupportedFormatError) as exc_info:
            self.processor.validate_file(file_path)
        
        assert "Unsupported file format: .txt" in str(exc_info.value)
        assert "Supported formats:" in str(exc_info.value)
    
    def test_validate_file_mime_type_mismatch(self):
        """Test validation fails when MIME type doesn't match extension."""
        file_path = self.create_temp_file("test.m4a")
        
        with patch.object(self.processor, '_validate_mime_type', return_value=False):
            with pytest.raises(UnsupportedFormatError) as exc_info:
                self.processor.validate_file(file_path)
            
            assert "File MIME type doesn't match extension" in str(exc_info.value)
    
    def test_get_file_info_success(self):
        """Test getting file information successfully."""
        file_path = self.create_temp_file("test.m4a", b"fake audio content")
        
        with patch.object(self.processor, '_validate_mime_type', return_value=True):
            file_info = self.processor.get_file_info(file_path)
        
        assert isinstance(file_info, AudioFileInfo)
        assert file_info.file_path == str(Path(file_path).absolute())
        assert file_info.file_size > 0
        assert file_info.format == ".m4a"
    
    def test_get_file_info_invalid_file(self):
        """Test getting file info fails for invalid file."""
        file_path = self.create_temp_file("test.txt")
        
        with pytest.raises(UnsupportedFormatError):
            self.processor.get_file_info(file_path)
    
    def test_is_supported_format_true(self):
        """Test _is_supported_format returns True for supported formats."""
        assert self.processor._is_supported_format(".m4a") is True
        assert self.processor._is_supported_format(".wav") is True
        assert self.processor._is_supported_format(".mp3") is True
        assert self.processor._is_supported_format(".aac") is True
        assert self.processor._is_supported_format(".flac") is True
    
    def test_is_supported_format_false(self):
        """Test _is_supported_format returns False for unsupported formats."""
        assert self.processor._is_supported_format(".txt") is False
        assert self.processor._is_supported_format(".pdf") is False
        assert self.processor._is_supported_format(".doc") is False
    
    def test_is_supported_format_case_insensitive(self):
        """Test _is_supported_format is case insensitive."""
        assert self.processor._is_supported_format(".M4A") is True
        assert self.processor._is_supported_format(".WAV") is True
        assert self.processor._is_supported_format(".Mp3") is True
    
    @patch('mimetypes.guess_type')
    def test_validate_mime_type_success(self, mock_guess_type):
        """Test MIME type validation success."""
        mock_guess_type.return_value = ('audio/mp4', None)
        
        result = self.processor._validate_mime_type("test.m4a", ".m4a")
        assert result is True
    
    @patch('mimetypes.guess_type')
    def test_validate_mime_type_unknown_mime(self, mock_guess_type):
        """Test MIME type validation with unknown MIME type."""
        mock_guess_type.return_value = (None, None)
        
        result = self.processor._validate_mime_type("test.m4a", ".m4a")
        assert result is True  # Should return True for unknown MIME types
    
    @patch('mimetypes.guess_type')
    def test_validate_mime_type_unsupported_mime(self, mock_guess_type):
        """Test MIME type validation with unsupported MIME type."""
        mock_guess_type.return_value = ('application/pdf', None)
        
        result = self.processor._validate_mime_type("test.m4a", ".m4a")
        assert result is True  # Should return True for unmapped MIME types
    
    @patch('mimetypes.guess_type')
    def test_validate_mime_type_mismatch(self, mock_guess_type):
        """Test MIME type validation with format mismatch."""
        mock_guess_type.return_value = ('audio/mpeg', None)  # MP3 MIME type
        
        result = self.processor._validate_mime_type("test.m4a", ".m4a")
        assert result is False  # Should return False for mismatched types
    
    @patch('mimetypes.guess_type')
    def test_validate_mime_type_exception(self, mock_guess_type):
        """Test MIME type validation handles exceptions gracefully."""
        mock_guess_type.side_effect = Exception("MIME type error")
        
        result = self.processor._validate_mime_type("test.m4a", ".m4a")
        assert result is True  # Should return True when exception occurs
    
    def test_find_audio_files_empty_directory(self):
        """Test finding audio files in empty directory."""
        result = self.processor.find_audio_files(self.temp_dir)
        assert result == []
    
    def test_find_audio_files_with_audio_files(self):
        """Test finding audio files in directory with audio files."""
        # Create test files
        m4a_file = self.create_temp_file("test1.m4a")
        wav_file = self.create_temp_file("test2.wav")
        txt_file = self.create_temp_file("test3.txt")  # Should be ignored
        
        with patch.object(self.processor, '_validate_mime_type', return_value=True):
            result = self.processor.find_audio_files(self.temp_dir)
        
        # Should find only audio files, sorted
        expected = sorted([str(Path(m4a_file).absolute()), str(Path(wav_file).absolute())])
        assert result == expected
    
    def test_find_audio_files_recursive(self):
        """Test finding audio files recursively in subdirectories."""
        # Create subdirectory
        sub_dir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(sub_dir)
        
        # Create files in main and subdirectory
        main_file = self.create_temp_file("main.m4a")
        sub_file = os.path.join(sub_dir, "sub.wav")
        with open(sub_file, 'wb') as f:
            f.write(b"fake audio")
        
        with patch.object(self.processor, '_validate_mime_type', return_value=True):
            result = self.processor.find_audio_files(self.temp_dir, recursive=True)
        
        assert len(result) == 2
        assert str(Path(main_file).absolute()) in result
        assert str(Path(sub_file).absolute()) in result
    
    def test_find_audio_files_non_recursive(self):
        """Test finding audio files non-recursively."""
        # Create subdirectory
        sub_dir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(sub_dir)
        
        # Create files in main and subdirectory
        main_file = self.create_temp_file("main.m4a")
        sub_file = os.path.join(sub_dir, "sub.wav")
        with open(sub_file, 'wb') as f:
            f.write(b"fake audio")
        
        with patch.object(self.processor, '_validate_mime_type', return_value=True):
            result = self.processor.find_audio_files(self.temp_dir, recursive=False)
        
        # Should only find file in main directory
        assert len(result) == 1
        assert str(Path(main_file).absolute()) in result
        assert str(Path(sub_file).absolute()) not in result
    
    def test_find_audio_files_directory_not_found(self):
        """Test finding audio files in non-existent directory."""
        non_existent_dir = os.path.join(self.temp_dir, "nonexistent")
        
        with pytest.raises(FileNotFoundError) as exc_info:
            self.processor.find_audio_files(non_existent_dir)
        
        assert "Directory not found" in str(exc_info.value)
    
    def test_find_audio_files_path_is_file(self):
        """Test finding audio files when path is a file, not directory."""
        file_path = self.create_temp_file("test.m4a")
        
        with pytest.raises(FileNotFoundError) as exc_info:
            self.processor.find_audio_files(file_path)
        
        assert "Path is not a directory" in str(exc_info.value)
    
    def test_find_audio_files_with_invalid_files(self):
        """Test finding audio files skips invalid files gracefully."""
        # Create valid and invalid files
        valid_file = self.create_temp_file("valid.m4a")
        invalid_file = self.create_temp_file("invalid.m4a")
        
        def mock_validate(file_path):
            if "invalid" in file_path:
                raise UnsupportedFormatError("Invalid file")
            return True
        
        with patch.object(self.processor, 'validate_file', side_effect=mock_validate):
            result = self.processor.find_audio_files(self.temp_dir)
        
        # Should only include valid file
        assert len(result) == 1
        assert str(Path(valid_file).absolute()) in result


class TestAudioProcessorConversion:
    """Test cases for AudioProcessor audio conversion functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = AudioProcessor()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_temp_file(self, filename: str, content: bytes = b"fake audio data") -> str:
        """Create a temporary file for testing."""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(content)
        return file_path
    
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not available")
    @patch('src.speech_to_text.audio_processor.AudioSegment')
    def test_convert_to_wav_success(self, mock_audio_segment):
        """Test successful audio conversion to WAV."""
        # Setup mocks
        mock_audio = MagicMock()
        mock_audio_segment.from_file.return_value = mock_audio
        
        input_file = self.create_temp_file("test.m4a")
        
        with patch.object(self.processor, 'validate_file', return_value=True):
            result = self.processor.convert_to_wav(input_file)
        
        # Verify conversion was called
        mock_audio.export.assert_called_once()
        assert result.endswith("_converted.wav")
        assert os.path.dirname(result) == tempfile.gettempdir()
    
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not available")
    @patch('src.speech_to_text.audio_processor.AudioSegment')
    def test_convert_to_wav_with_output_path(self, mock_audio_segment):
        """Test audio conversion with specified output path."""
        # Setup mocks
        mock_audio = MagicMock()
        mock_audio_segment.from_file.return_value = mock_audio
        
        input_file = self.create_temp_file("test.m4a")
        output_file = os.path.join(self.temp_dir, "output.wav")
        
        with patch.object(self.processor, 'validate_file', return_value=True):
            result = self.processor.convert_to_wav(input_file, output_file)
        
        assert result == output_file
        mock_audio.export.assert_called_once_with(output_file, format="wav")
    
    @pytest.mark.skipif(PYDUB_AVAILABLE, reason="Test for when pydub is not available")
    def test_convert_to_wav_no_pydub(self):
        """Test conversion fails gracefully when pydub is not available."""
        input_file = self.create_temp_file("test.m4a")
        
        with patch.object(self.processor, 'validate_file', return_value=True):
            with pytest.raises(AudioConversionError) as exc_info:
                self.processor.convert_to_wav(input_file)
            
            assert "pydub is not available" in str(exc_info.value)
    
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not available")
    @patch('src.speech_to_text.audio_processor.AudioSegment')
    def test_convert_to_wav_conversion_error(self, mock_audio_segment):
        """Test conversion handles errors gracefully."""
        mock_audio_segment.from_file.side_effect = Exception("Conversion failed")
        
        input_file = self.create_temp_file("test.m4a")
        
        with patch.object(self.processor, 'validate_file', return_value=True):
            with pytest.raises(AudioConversionError) as exc_info:
                self.processor.convert_to_wav(input_file)
            
            assert "Conversion failed" in str(exc_info.value)
    
    def test_convert_to_wav_invalid_file(self):
        """Test conversion fails for invalid input file."""
        input_file = self.create_temp_file("test.txt")
        
        if PYDUB_AVAILABLE:
            with pytest.raises(UnsupportedFormatError):
                self.processor.convert_to_wav(input_file)
        else:
            with pytest.raises(AudioConversionError):
                self.processor.convert_to_wav(input_file)
    
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not available")
    @patch('src.speech_to_text.audio_processor.AudioSegment')
    @patch('src.speech_to_text.audio_processor.normalize')
    def test_preprocess_audio_normalize_only(self, mock_normalize, mock_audio_segment):
        """Test audio preprocessing with normalization only."""
        # Setup mocks
        mock_audio = MagicMock()
        mock_normalized = MagicMock()
        mock_audio_segment.from_file.return_value = mock_audio
        mock_normalize.return_value = mock_normalized
        
        input_file = self.create_temp_file("test.m4a")
        
        with patch.object(self.processor, 'validate_file', return_value=True):
            result = self.processor.preprocess_audio(input_file, normalize_audio=True, remove_silence=False)
        
        # Verify normalization was called
        mock_normalize.assert_called_once_with(mock_audio)
        mock_normalized.export.assert_called_once()
        assert result.endswith("_preprocessed.m4a")
    
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not available")
    @patch('src.speech_to_text.audio_processor.AudioSegment')
    def test_preprocess_audio_remove_silence(self, mock_audio_segment):
        """Test audio preprocessing with silence removal."""
        # Setup mocks
        mock_audio = MagicMock()
        mock_audio_segment.from_file.return_value = mock_audio
        
        input_file = self.create_temp_file("test.wav")
        
        with patch.object(self.processor, 'validate_file', return_value=True):
            with patch.object(self.processor, '_remove_silence', return_value=mock_audio) as mock_remove:
                result = self.processor.preprocess_audio(input_file, normalize_audio=False, remove_silence=True)
        
        # Verify silence removal was called
        mock_remove.assert_called_once_with(mock_audio)
        mock_audio.export.assert_called_once()
    
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not available")
    @patch('src.speech_to_text.audio_processor.AudioSegment')
    def test_preprocess_audio_both_options(self, mock_audio_segment):
        """Test audio preprocessing with both normalization and silence removal."""
        # Setup mocks
        mock_audio = MagicMock()
        mock_audio_segment.from_file.return_value = mock_audio
        
        input_file = self.create_temp_file("test.mp3")
        
        with patch.object(self.processor, 'validate_file', return_value=True):
            with patch('src.speech_to_text.audio_processor.normalize', return_value=mock_audio):
                with patch.object(self.processor, '_remove_silence', return_value=mock_audio):
                    result = self.processor.preprocess_audio(input_file, normalize_audio=True, remove_silence=True)
        
        mock_audio.export.assert_called_once()
        assert result.endswith("_preprocessed.mp3")
    
    @pytest.mark.skipif(PYDUB_AVAILABLE, reason="Test for when pydub is not available")
    def test_preprocess_audio_no_pydub(self):
        """Test preprocessing fails gracefully when pydub is not available."""
        input_file = self.create_temp_file("test.m4a")
        
        with patch.object(self.processor, 'validate_file', return_value=True):
            with pytest.raises(AudioProcessingError) as exc_info:
                self.processor.preprocess_audio(input_file)
            
            assert "pydub is not available" in str(exc_info.value)
    
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not available")
    @patch('src.speech_to_text.audio_processor.AudioSegment')
    def test_preprocess_audio_error(self, mock_audio_segment):
        """Test preprocessing handles errors gracefully."""
        mock_audio_segment.from_file.side_effect = Exception("Processing failed")
        
        input_file = self.create_temp_file("test.m4a")
        
        with patch.object(self.processor, 'validate_file', return_value=True):
            with pytest.raises(AudioProcessingError) as exc_info:
                self.processor.preprocess_audio(input_file)
            
            assert "Processing failed" in str(exc_info.value)
    
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not available")
    @patch('src.speech_to_text.audio_processor.AudioSegment')
    def test_get_audio_info_with_details(self, mock_audio_segment):
        """Test getting detailed audio information."""
        # Setup mocks
        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=5000)  # 5 seconds in ms
        mock_audio.frame_rate = 44100
        mock_audio.channels = 2
        mock_audio_segment.from_file.return_value = mock_audio
        
        input_file = self.create_temp_file("test.m4a", b"fake audio content")
        
        with patch.object(self.processor, 'validate_file', return_value=True):
            file_info = self.processor.get_audio_info(input_file)
        
        assert isinstance(file_info, AudioFileInfo)
        assert file_info.duration == 5.0  # 5000ms = 5.0s
        assert file_info.sample_rate == 44100
        assert file_info.channels == 2
        assert file_info.format == ".m4a"
    
    @pytest.mark.skipif(PYDUB_AVAILABLE, reason="Test for when pydub is not available")
    def test_get_audio_info_no_pydub(self):
        """Test getting audio info falls back to basic info when pydub unavailable."""
        input_file = self.create_temp_file("test.m4a", b"fake audio content")
        
        with patch.object(self.processor, 'validate_file', return_value=True):
            file_info = self.processor.get_audio_info(input_file)
        
        assert isinstance(file_info, AudioFileInfo)
        assert file_info.duration is None  # Should be None without pydub
        assert file_info.sample_rate is None
        assert file_info.channels is None
        assert file_info.format == ".m4a"
    
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not available")
    @patch('src.speech_to_text.audio_processor.AudioSegment')
    def test_get_audio_info_loading_error(self, mock_audio_segment):
        """Test getting audio info handles loading errors gracefully."""
        mock_audio_segment.from_file.side_effect = Exception("Loading failed")
        
        input_file = self.create_temp_file("test.m4a", b"fake audio content")
        
        with patch.object(self.processor, 'validate_file', return_value=True):
            file_info = self.processor.get_audio_info(input_file)
        
        # Should fall back to basic info
        assert isinstance(file_info, AudioFileInfo)
        assert file_info.duration is None
        assert file_info.format == ".m4a"
    
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not available")
    @patch('src.speech_to_text.audio_processor.AudioSegment')
    def test_load_audio_file_m4a(self, mock_audio_segment):
        """Test loading M4A audio file."""
        mock_audio = MagicMock()
        mock_audio_segment.from_file.return_value = mock_audio
        
        input_file = self.create_temp_file("test.m4a")
        
        result = self.processor._load_audio_file(input_file)
        
        mock_audio_segment.from_file.assert_called_once_with(input_file, format="m4a")
        assert result == mock_audio
    
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not available")
    @patch('src.speech_to_text.audio_processor.AudioSegment')
    def test_load_audio_file_wav(self, mock_audio_segment):
        """Test loading WAV audio file."""
        mock_audio = MagicMock()
        mock_audio_segment.from_wav.return_value = mock_audio
        
        input_file = self.create_temp_file("test.wav")
        
        result = self.processor._load_audio_file(input_file)
        
        mock_audio_segment.from_wav.assert_called_once_with(input_file)
        assert result == mock_audio
    
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not available")
    @patch('src.speech_to_text.audio_processor.AudioSegment')
    def test_load_audio_file_mp3(self, mock_audio_segment):
        """Test loading MP3 audio file."""
        mock_audio = MagicMock()
        mock_audio_segment.from_mp3.return_value = mock_audio
        
        input_file = self.create_temp_file("test.mp3")
        
        result = self.processor._load_audio_file(input_file)
        
        mock_audio_segment.from_mp3.assert_called_once_with(input_file)
        assert result == mock_audio
    
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not available")
    @patch('src.speech_to_text.audio_processor.AudioSegment')
    def test_load_audio_file_generic(self, mock_audio_segment):
        """Test loading audio file with generic method."""
        mock_audio = MagicMock()
        mock_audio_segment.from_file.return_value = mock_audio
        
        input_file = self.create_temp_file("test.aac")
        
        result = self.processor._load_audio_file(input_file)
        
        mock_audio_segment.from_file.assert_called_once_with(input_file, format="aac")
        assert result == mock_audio
    
    @pytest.mark.skipif(PYDUB_AVAILABLE, reason="Test for when pydub is not available")
    def test_load_audio_file_no_pydub(self):
        """Test loading audio file fails when pydub is not available."""
        input_file = self.create_temp_file("test.m4a")
        
        with pytest.raises(AudioProcessingError) as exc_info:
            self.processor._load_audio_file(input_file)
        
        assert "pydub is not available" in str(exc_info.value)
    
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not available")
    @patch('src.speech_to_text.audio_processor.AudioSegment')
    def test_load_audio_file_error(self, mock_audio_segment):
        """Test loading audio file handles errors."""
        mock_audio_segment.from_file.side_effect = Exception("Loading failed")
        
        input_file = self.create_temp_file("test.m4a")
        
        with pytest.raises(AudioProcessingError) as exc_info:
            self.processor._load_audio_file(input_file)
        
        assert "Loading failed" in str(exc_info.value)
    
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not available")
    @patch('src.speech_to_text.audio_processor.split_on_silence')
    def test_remove_silence_success(self, mock_split):
        """Test silence removal functionality."""
        # Create mock audio segments
        mock_audio = MagicMock()
        mock_chunk1 = MagicMock()
        mock_chunk2 = MagicMock()
        mock_split.return_value = [mock_chunk1, mock_chunk2]
        
        # Mock addition operation
        mock_chunk1.__add__ = MagicMock(return_value=MagicMock())
        
        result = self.processor._remove_silence(mock_audio)
        
        mock_split.assert_called_once_with(
            mock_audio,
            min_silence_len=500,
            silence_thresh=-40,
            keep_silence=100
        )
        mock_chunk1.__add__.assert_called_once_with(mock_chunk2)
    
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not available")
    @patch('src.speech_to_text.audio_processor.split_on_silence')
    def test_remove_silence_no_chunks(self, mock_split):
        """Test silence removal when no chunks are found."""
        mock_audio = MagicMock()
        mock_split.return_value = []
        
        result = self.processor._remove_silence(mock_audio)
        
        assert result == mock_audio  # Should return original audio
    
    @pytest.mark.skipif(not PYDUB_AVAILABLE, reason="pydub not available")
    @patch('src.speech_to_text.audio_processor.split_on_silence')
    def test_remove_silence_error(self, mock_split):
        """Test silence removal handles errors gracefully."""
        mock_audio = MagicMock()
        mock_split.side_effect = Exception("Silence removal failed")
        
        result = self.processor._remove_silence(mock_audio)
        
        assert result == mock_audio  # Should return original audio on error