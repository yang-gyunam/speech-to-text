"""
Integration tests for the CLI interface.

Tests the main CLI functionality including argument parsing,
file processing, and user interaction.
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

import pytest
from click.testing import CliRunner

from speech_to_text.cli import transcribe, formats, info, cli, main
from speech_to_text.models import TranscriptionResult
from speech_to_text.exceptions import SpeechToTextError, UnsupportedFormatError


class TestCLIBasicFunctionality:
    """Test basic CLI functionality and argument parsing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.test_audio_file = os.path.join(self.temp_dir, "test.m4a")
        self.output_dir = os.path.join(self.temp_dir, "output")
        
        # Create a dummy audio file
        Path(self.test_audio_file).touch()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cli_help_message(self):
        """Test that help message is displayed correctly."""
        result = self.runner.invoke(transcribe, ['--help'])
        
        assert result.exit_code == 0
        assert "Convert iPhone audio recordings to text" in result.output
        assert "--output-dir" in result.output
        assert "--language" in result.output
        assert "--batch" in result.output
    
    def test_cli_version_option(self):
        """Test version option displays correctly."""
        result = self.runner.invoke(transcribe, ['--version'])
        
        assert result.exit_code == 0
        assert "0.1.0" in result.output
    
    @patch('speech_to_text.cli.AudioProcessor')
    @patch('speech_to_text.cli.SpeechTranscriber')
    @patch('speech_to_text.cli.TextExporter')
    def test_single_file_processing(self, mock_exporter, mock_transcriber, mock_processor):
        """Test processing a single audio file."""
        # Setup mocks
        mock_processor_instance = Mock()
        mock_processor.return_value = mock_processor_instance
        mock_processor_instance.validate_file.return_value = True
        
        mock_transcriber_instance = Mock()
        mock_transcriber.return_value = mock_transcriber_instance
        
        mock_result = TranscriptionResult(
            original_file=self.test_audio_file,
            transcribed_text="Test transcription",
            language="ko",
            confidence_score=0.95,
            processing_time=1.5,
            timestamp=datetime.now()
        )
        mock_transcriber_instance.transcribe_file.return_value = mock_result
        
        mock_exporter_instance = Mock()
        mock_exporter.return_value = mock_exporter_instance
        mock_exporter_instance.save_transcription_result.return_value = "/path/to/output.txt"
        
        # Run CLI command
        result = self.runner.invoke(transcribe, [
            self.test_audio_file,
            '--output-dir', self.output_dir
        ])
        
        # Verify results
        assert result.exit_code == 0
        mock_processor_instance.validate_file.assert_called_once_with(self.test_audio_file)
        mock_transcriber_instance.transcribe_file.assert_called_once_with(self.test_audio_file, "ko")
        mock_exporter_instance.save_transcription_result.assert_called_once()
    
    @patch('speech_to_text.cli.AudioProcessor')
    @patch('speech_to_text.cli.FileManager')
    @patch('speech_to_text.cli.SpeechTranscriber')
    @patch('speech_to_text.cli.TextExporter')
    def test_batch_processing(self, mock_exporter, mock_transcriber, mock_file_manager, mock_processor):
        """Test batch processing of multiple files."""
        # Create test directory with multiple files
        test_files = [
            os.path.join(self.temp_dir, "file1.m4a"),
            os.path.join(self.temp_dir, "file2.wav")
        ]
        for file_path in test_files:
            Path(file_path).touch()
        
        # Setup mocks
        mock_processor_instance = Mock()
        mock_processor.return_value = mock_processor_instance
        
        mock_file_manager_instance = Mock()
        mock_file_manager.return_value = mock_file_manager_instance
        mock_file_manager_instance.find_audio_files.return_value = test_files
        mock_file_manager_instance.create_output_directory.return_value = self.output_dir
        
        mock_transcriber_instance = Mock()
        mock_transcriber.return_value = mock_transcriber_instance
        
        mock_results = [
            TranscriptionResult(
                original_file=test_files[0],
                transcribed_text="First transcription",
                language="ko",
                confidence_score=0.9,
                processing_time=1.0,
                timestamp=datetime.now()
            ),
            TranscriptionResult(
                original_file=test_files[1],
                transcribed_text="Second transcription",
                language="ko",
                confidence_score=0.85,
                processing_time=1.2,
                timestamp=datetime.now()
            )
        ]
        mock_transcriber_instance.transcribe_batch.return_value = mock_results
        
        mock_exporter_instance = Mock()
        mock_exporter.return_value = mock_exporter_instance
        mock_exporter_instance.save_batch_results.return_value = {
            test_files[0]: "/path/to/output1.txt",
            test_files[1]: "/path/to/output2.txt",
            "_summary": "/path/to/summary.txt"
        }
        
        # Run CLI command
        result = self.runner.invoke(transcribe, [
            self.temp_dir,
            '--batch',
            '--output-dir', self.output_dir
        ])
        
        # Verify results
        assert result.exit_code == 0
        mock_file_manager_instance.find_audio_files.assert_called_once()
        mock_transcriber_instance.transcribe_batch.assert_called_once()
        mock_exporter_instance.save_batch_results.assert_called_once()
    
    def test_invalid_input_file(self):
        """Test handling of invalid input file."""
        invalid_file = os.path.join(self.temp_dir, "nonexistent.m4a")
        
        result = self.runner.invoke(transcribe, [invalid_file])
        
        assert result.exit_code != 0
    
    @patch('speech_to_text.cli.AudioProcessor')
    def test_unsupported_format_error(self, mock_processor):
        """Test handling of unsupported file format."""
        # Create unsupported file
        unsupported_file = os.path.join(self.temp_dir, "test.txt")
        Path(unsupported_file).touch()
        
        mock_processor_instance = Mock()
        mock_processor.return_value = mock_processor_instance
        mock_processor_instance.validate_file.side_effect = UnsupportedFormatError("Unsupported format")
        
        result = self.runner.invoke(transcribe, [unsupported_file])
        
        assert result.exit_code != 0


class TestCLIOptions:
    """Test CLI options and parameters."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.test_audio_file = os.path.join(self.temp_dir, "test.m4a")
        Path(self.test_audio_file).touch()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('speech_to_text.cli.AudioProcessor')
    @patch('speech_to_text.cli.SpeechTranscriber')
    @patch('speech_to_text.cli.TextExporter')
    def test_language_option(self, mock_exporter, mock_transcriber, mock_processor):
        """Test language option is passed correctly."""
        # Setup mocks
        mock_processor_instance = Mock()
        mock_processor.return_value = mock_processor_instance
        mock_processor_instance.validate_file.return_value = True
        
        mock_transcriber_instance = Mock()
        mock_transcriber.return_value = mock_transcriber_instance
        mock_transcriber_instance.transcribe_file.return_value = Mock(error_message=None)
        
        mock_exporter_instance = Mock()
        mock_exporter.return_value = mock_exporter_instance
        mock_exporter_instance.save_transcription_result.return_value = "/path/to/output.txt"
        
        # Test with English language
        result = self.runner.invoke(transcribe, [
            self.test_audio_file,
            '--language', 'en'
        ])
        
        assert result.exit_code == 0
        mock_transcriber_instance.transcribe_file.assert_called_with(self.test_audio_file, "en")
    
    @patch('speech_to_text.cli.SpeechTranscriber')
    def test_model_size_option(self, mock_transcriber):
        """Test model size option is passed correctly."""
        mock_transcriber_instance = Mock()
        mock_transcriber.return_value = mock_transcriber_instance
        
        with patch('speech_to_text.cli.AudioProcessor'), \
             patch('speech_to_text.cli.TextExporter'):
            
            result = self.runner.invoke(transcribe, [
                self.test_audio_file,
                '--model-size', 'large'
            ])
            
            mock_transcriber.assert_called_with(model_size='large')
    
    @patch('speech_to_text.cli.AudioProcessor')
    @patch('speech_to_text.cli.SpeechTranscriber')
    @patch('speech_to_text.cli.TextExporter')
    def test_quiet_mode(self, mock_exporter, mock_transcriber, mock_processor):
        """Test quiet mode suppresses output."""
        # Setup mocks
        mock_processor_instance = Mock()
        mock_processor.return_value = mock_processor_instance
        mock_processor_instance.validate_file.return_value = True
        
        mock_transcriber_instance = Mock()
        mock_transcriber.return_value = mock_transcriber_instance
        mock_result = Mock(error_message=None, transcribed_text="Test")
        mock_transcriber_instance.transcribe_file.return_value = mock_result
        
        mock_exporter_instance = Mock()
        mock_exporter.return_value = mock_exporter_instance
        mock_exporter_instance.save_transcription_result.return_value = "/path/to/output.txt"
        
        result = self.runner.invoke(transcribe, [
            self.test_audio_file,
            '--quiet'
        ])
        
        assert result.exit_code == 0
        # In quiet mode, there should be minimal output
        assert "🎤" not in result.output
    
    def test_invalid_model_size(self):
        """Test invalid model size option."""
        result = self.runner.invoke(transcribe, [
            self.test_audio_file,
            '--model-size', 'invalid'
        ])
        
        assert result.exit_code != 0
        assert "Invalid value" in result.output


class TestCLISubcommands:
    """Test CLI subcommands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.test_audio_file = os.path.join(self.temp_dir, "test.m4a")
        Path(self.test_audio_file).touch()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_formats_command(self):
        """Test formats subcommand."""
        result = self.runner.invoke(formats)
        
        assert result.exit_code == 0
        assert "Supported audio formats:" in result.output
        assert ".m4a" in result.output
        assert ".wav" in result.output
        assert ".mp3" in result.output
    
    @patch('speech_to_text.cli.AudioProcessor')
    def test_info_command(self, mock_processor):
        """Test info subcommand."""
        mock_processor_instance = Mock()
        mock_processor.return_value = mock_processor_instance
        
        mock_file_info = Mock()
        mock_file_info.file_path = self.test_audio_file
        mock_file_info.file_size = 1024
        mock_file_info.format = ".m4a"
        mock_file_info.duration = 30.5
        mock_file_info.sample_rate = 44100
        mock_file_info.channels = 2
        
        mock_processor_instance.get_audio_info.return_value = mock_file_info
        
        result = self.runner.invoke(info, [self.test_audio_file])
        
        assert result.exit_code == 0
        assert "Audio file information:" in result.output
        assert "1,024 bytes" in result.output
        assert ".m4a" in result.output
        assert "30.50 seconds" in result.output
    
    def test_info_command_invalid_file(self):
        """Test info subcommand with invalid file."""
        result = self.runner.invoke(info, ["/nonexistent/file.m4a"])
        
        assert result.exit_code != 0


class TestProgressDisplay:
    """Test progress display functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('speech_to_text.cli.AudioProcessor')
    @patch('speech_to_text.cli.FileManager')
    @patch('speech_to_text.cli.SpeechTranscriber')
    @patch('speech_to_text.cli.TextExporter')
    def test_progress_display_in_batch_mode(self, mock_exporter, mock_transcriber, 
                                          mock_file_manager, mock_processor):
        """Test progress display during batch processing."""
        # Create test files
        test_files = [
            os.path.join(self.temp_dir, "file1.m4a"),
            os.path.join(self.temp_dir, "file2.m4a")
        ]
        for file_path in test_files:
            Path(file_path).touch()
        
        # Setup mocks
        mock_processor_instance = Mock()
        mock_processor.return_value = mock_processor_instance
        
        mock_file_manager_instance = Mock()
        mock_file_manager.return_value = mock_file_manager_instance
        mock_file_manager_instance.find_audio_files.return_value = test_files
        mock_file_manager_instance.create_output_directory.return_value = self.temp_dir
        
        mock_transcriber_instance = Mock()
        mock_transcriber.return_value = mock_transcriber_instance
        
        # Mock batch processing with progress callback
        def mock_transcribe_batch(file_paths, language, progress_callback):
            for i, file_path in enumerate(file_paths):
                progress_callback(i, len(file_paths), file_path)
            
            return [Mock(error_message=None) for _ in file_paths]
        
        mock_transcriber_instance.transcribe_batch.side_effect = mock_transcribe_batch
        
        mock_exporter_instance = Mock()
        mock_exporter.return_value = mock_exporter_instance
        mock_exporter_instance.save_batch_results.return_value = {}
        
        # Run command
        result = self.runner.invoke(transcribe, [
            self.temp_dir,
            '--batch'
        ])
        
        assert result.exit_code == 0
        # Check that progress indicators are present
        assert "[1/2]" in result.output or "[2/2]" in result.output


class TestErrorHandling:
    """Test error handling in CLI."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('speech_to_text.cli.AudioProcessor')
    def test_keyboard_interrupt_handling(self, mock_processor):
        """Test handling of keyboard interrupt."""
        mock_processor_instance = Mock()
        mock_processor.return_value = mock_processor_instance
        mock_processor_instance.validate_file.side_effect = KeyboardInterrupt()
        
        test_file = os.path.join(self.temp_dir, "test.m4a")
        Path(test_file).touch()
        
        result = self.runner.invoke(transcribe, [test_file])
        
        assert result.exit_code == 130  # Standard exit code for SIGINT
        assert "cancelled by user" in result.output
    
    @patch('speech_to_text.cli.AudioProcessor')
    def test_unexpected_error_handling(self, mock_processor):
        """Test handling of unexpected errors."""
        mock_processor_instance = Mock()
        mock_processor.return_value = mock_processor_instance
        mock_processor_instance.validate_file.side_effect = RuntimeError("Unexpected error")
        
        test_file = os.path.join(self.temp_dir, "test.m4a")
        Path(test_file).touch()
        
        result = self.runner.invoke(transcribe, [test_file])
        
        assert result.exit_code == 1
        assert "Unexpected error" in result.output


class TestMainEntryPoint:
    """Test main entry point function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('speech_to_text.cli.transcribe')
    def test_main_calls_transcribe_by_default(self, mock_transcribe):
        """Test that main() calls transcribe by default."""
        with patch('sys.argv', ['speech-to-text', 'test.m4a']):
            main()
        
        mock_transcribe.assert_called_once()
    
    @patch('speech_to_text.cli.cli')
    def test_main_calls_cli_for_subcommands(self, mock_cli):
        """Test that main() calls cli for subcommands."""
        with patch('sys.argv', ['speech-to-text', 'formats']):
            main()
        
        mock_cli.assert_called_once()