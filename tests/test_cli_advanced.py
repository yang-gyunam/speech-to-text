"""
Tests for advanced CLI features including configuration management,
help system, and additional commands.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from click.testing import CliRunner

from speech_to_text.cli import (
    cli, init_config, show_config, examples, doctor,
    transcribe
)
from speech_to_text.config import ConfigManager, AppConfig


class TestConfigurationFeatures:
    """Test configuration file support and management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test-config.json")
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_config_json(self):
        """Test creating a JSON configuration file."""
        result = self.runner.invoke(init_config, [
            '--output', self.config_file,
            '--format', 'json'
        ])
        
        assert result.exit_code == 0
        assert "Default configuration created" in result.output
        assert Path(self.config_file).exists()
        
        # Verify the config file content
        with open(self.config_file, 'r') as f:
            config_data = json.load(f)
        
        assert 'output_dir' in config_data
        assert 'language' in config_data
        assert 'model_size' in config_data
    
    def test_init_config_yaml(self):
        """Test creating a YAML configuration file."""
        yaml_config = os.path.join(self.temp_dir, "test-config.yaml")
        
        result = self.runner.invoke(init_config, [
            '--output', yaml_config,
            '--format', 'yaml'
        ])
        
        assert result.exit_code == 0
        assert Path(yaml_config).exists()
    
    def test_show_config_with_file(self):
        """Test showing configuration from a specific file."""
        # Create a test config file
        config_data = {
            "output_dir": "./test-output",
            "language": "en",
            "model_size": "large"
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f)
        
        result = self.runner.invoke(show_config, [
            '--config', self.config_file
        ])
        
        assert result.exit_code == 0
        assert "Current configuration:" in result.output
        assert "output_dir: ./test-output" in result.output
        assert "language: en" in result.output
        assert "model_size: large" in result.output
    
    def test_show_config_default(self):
        """Test showing default configuration."""
        result = self.runner.invoke(show_config)
        
        assert result.exit_code == 0
        assert "Current configuration:" in result.output
        assert "output_dir:" in result.output
        assert "language:" in result.output
    
    @patch('speech_to_text.cli.AudioProcessor')
    @patch('speech_to_text.cli.FileManager')
    @patch('speech_to_text.cli.SpeechTranscriber')
    @patch('speech_to_text.cli.TextExporter')
    def test_transcribe_with_config_file(self, mock_exporter, mock_transcriber, mock_file_manager, mock_processor):
        """Test transcription using configuration file."""
        # Create test audio file
        test_audio = os.path.join(self.temp_dir, "test.m4a")
        Path(test_audio).touch()
        
        # Create config file
        config_data = {
            "output_dir": self.temp_dir,
            "language": "en",
            "model_size": "small",
            "include_metadata": False
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Setup mocks
        mock_processor_instance = Mock()
        mock_processor.return_value = mock_processor_instance
        mock_processor_instance.validate_file.return_value = True
        
        mock_file_manager_instance = Mock()
        mock_file_manager.return_value = mock_file_manager_instance
        mock_file_manager_instance.create_output_directory.return_value = self.temp_dir
        mock_file_manager_instance.generate_output_filename.return_value = os.path.join(self.temp_dir, "output.txt")
        
        mock_transcriber_instance = Mock()
        mock_transcriber.return_value = mock_transcriber_instance
        mock_transcriber_instance.transcribe_file.return_value = Mock(error_message=None)
        
        mock_exporter_instance = Mock()
        mock_exporter.return_value = mock_exporter_instance
        mock_exporter_instance.save_transcription_result.return_value = "/path/to/output.txt"
        
        # Run transcription with config
        result = self.runner.invoke(transcribe, [
            test_audio,
            '--config', self.config_file
        ])
        
        assert result.exit_code == 0
        
        # Verify that config settings were used
        mock_transcriber.assert_called_with(model_size='small')
        mock_transcriber_instance.transcribe_file.assert_called_with(test_audio, "en")
    
    @patch('speech_to_text.cli.AudioProcessor')
    @patch('speech_to_text.cli.SpeechTranscriber')
    @patch('speech_to_text.cli.TextExporter')
    def test_save_config_option(self, mock_exporter, mock_transcriber, mock_processor):
        """Test saving configuration with --save-config option."""
        # Create test audio file
        test_audio = os.path.join(self.temp_dir, "test.m4a")
        Path(test_audio).touch()
        
        result = self.runner.invoke(transcribe, [
            test_audio,
            '--save-config', self.config_file,
            '--language', 'en',
            '--model-size', 'large',
            '--output-dir', self.temp_dir
        ])
        
        assert result.exit_code == 0
        assert "Configuration saved to" in result.output
        assert Path(self.config_file).exists()
        
        # Verify saved config
        with open(self.config_file, 'r') as f:
            config_data = json.load(f)
        
        assert config_data['language'] == 'en'
        assert config_data['model_size'] == 'large'
        assert config_data['output_dir'] == self.temp_dir


class TestHelpAndDocumentation:
    """Test help system and documentation features."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_examples_command(self):
        """Test examples command output."""
        result = self.runner.invoke(examples)
        
        assert result.exit_code == 0
        assert "Usage Examples:" in result.output
        assert "Basic Usage:" in result.output
        assert "Advanced Usage:" in result.output
        assert "Configuration:" in result.output
        assert "Environment Variables:" in result.output
        assert "Tips:" in result.output
    
    def test_doctor_command(self):
        """Test system check command."""
        result = self.runner.invoke(doctor)
        
        assert result.exit_code == 0
        assert "Speech-to-Text System Check" in result.output
        assert "Python version:" in result.output
        assert "Configuration:" in result.output
    
    def test_main_help(self):
        """Test main help message includes all commands."""
        result = self.runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "init-config" in result.output
        assert "show-config" in result.output
        assert "examples" in result.output
        assert "doctor" in result.output
        assert "formats" in result.output
        assert "info" in result.output


class TestEnvironmentVariables:
    """Test environment variable support."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.original_env = os.environ.copy()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
    
    @patch('speech_to_text.cli.AudioProcessor')
    @patch('speech_to_text.cli.FileManager')
    @patch('speech_to_text.cli.SpeechTranscriber')
    @patch('speech_to_text.cli.TextExporter')
    def test_environment_variable_override(self, mock_exporter, mock_transcriber, mock_file_manager, mock_processor):
        """Test that environment variables override default settings."""
        # Set environment variables
        os.environ['SPEECH_TO_TEXT_LANGUAGE'] = 'en'
        os.environ['SPEECH_TO_TEXT_MODEL_SIZE'] = 'large'
        os.environ['SPEECH_TO_TEXT_OUTPUT_DIR'] = self.temp_dir
        
        # Create test audio file
        test_audio = os.path.join(self.temp_dir, "test.m4a")
        Path(test_audio).touch()
        
        # Setup mocks
        mock_processor_instance = Mock()
        mock_processor.return_value = mock_processor_instance
        mock_processor_instance.validate_file.return_value = True
        
        mock_file_manager_instance = Mock()
        mock_file_manager.return_value = mock_file_manager_instance
        mock_file_manager_instance.create_output_directory.return_value = self.temp_dir
        mock_file_manager_instance.generate_output_filename.return_value = os.path.join(self.temp_dir, "output.txt")
        
        mock_transcriber_instance = Mock()
        mock_transcriber.return_value = mock_transcriber_instance
        mock_transcriber_instance.transcribe_file.return_value = Mock(error_message=None)
        
        mock_exporter_instance = Mock()
        mock_exporter.return_value = mock_exporter_instance
        mock_exporter_instance.save_transcription_result.return_value = "/path/to/output.txt"
        
        # Run transcription
        result = self.runner.invoke(transcribe, [test_audio])
        
        assert result.exit_code == 0
        
        # Verify environment settings were used
        mock_transcriber.assert_called_with(model_size='large')
        mock_transcriber_instance.transcribe_file.assert_called_with(test_audio, "en")


class TestConfigManager:
    """Test ConfigManager class functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_default_config(self):
        """Test loading default configuration."""
        config = self.config_manager.load_config()
        
        assert isinstance(config, AppConfig)
        assert config.language == "ko"
        assert config.model_size == "base"
        assert config.output_dir == "./output"
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        config_file = os.path.join(self.temp_dir, "test-config.json")
        
        # Create custom config
        custom_config = AppConfig(
            language="en",
            model_size="large",
            output_dir=self.temp_dir
        )
        
        # Save config
        self.config_manager.save_config(config_file, custom_config)
        assert Path(config_file).exists()
        
        # Load config
        loaded_config = self.config_manager.load_config(config_file)
        
        assert loaded_config.language == "en"
        assert loaded_config.model_size == "large"
        assert loaded_config.output_dir == self.temp_dir
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config should not raise
        self.config_manager.config = AppConfig()
        self.config_manager.validate_config()  # Should not raise
        
        # Invalid model size should raise
        self.config_manager.config.model_size = "invalid"
        with pytest.raises(ValueError, match="Invalid model size"):
            self.config_manager.validate_config()
        
        # Invalid log level should raise
        self.config_manager.config.model_size = "base"  # Reset to valid
        self.config_manager.config.log_level = "INVALID"
        with pytest.raises(ValueError, match="Invalid log level"):
            self.config_manager.validate_config()
    
    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "language": "en",
            "model_size": "large",
            "output_dir": "./custom-output",
            "unknown_key": "should_be_ignored"
        }
        
        config = AppConfig.from_dict(config_dict)
        
        assert config.language == "en"
        assert config.model_size == "large"
        assert config.output_dir == "./custom-output"
        # Unknown keys should be ignored, not cause errors
    
    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = AppConfig(language="en", model_size="large")
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict['language'] == "en"
        assert config_dict['model_size'] == "large"
        assert 'output_dir' in config_dict


class TestVerboseAndQuietModes:
    """Test verbose and quiet mode functionality."""
    
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
    def test_verbose_mode_logging(self, mock_exporter, mock_transcriber, mock_file_manager, mock_processor):
        """Test that verbose mode enables debug logging."""
        # Create test audio file
        test_audio = os.path.join(self.temp_dir, "test.m4a")
        Path(test_audio).touch()
        
        # Setup mocks
        mock_processor_instance = Mock()
        mock_processor.return_value = mock_processor_instance
        mock_processor_instance.validate_file.return_value = True
        
        mock_file_manager_instance = Mock()
        mock_file_manager.return_value = mock_file_manager_instance
        mock_file_manager_instance.create_output_directory.return_value = self.temp_dir
        mock_file_manager_instance.generate_output_filename.return_value = os.path.join(self.temp_dir, "output.txt")
        
        mock_transcriber_instance = Mock()
        mock_transcriber.return_value = mock_transcriber_instance
        mock_transcriber_instance.transcribe_file.return_value = Mock(error_message=None)
        
        mock_exporter_instance = Mock()
        mock_exporter.return_value = mock_exporter_instance
        mock_exporter_instance.save_transcription_result.return_value = "/path/to/output.txt"
        
        with patch('speech_to_text.cli.setup_logging') as mock_setup_logging:
            result = self.runner.invoke(transcribe, [
                test_audio,
                '--verbose'
            ])
            
            assert result.exit_code == 0
            # Verify that debug logging was enabled
            mock_setup_logging.assert_called_once()
            call_args = mock_setup_logging.call_args
            assert call_args[1]['log_level'] == 'DEBUG'
            assert call_args[1]['debug_mode'] is True
    
    @patch('speech_to_text.cli.AudioProcessor')
    @patch('speech_to_text.cli.SpeechTranscriber')
    @patch('speech_to_text.cli.TextExporter')
    def test_quiet_mode_suppresses_output(self, mock_exporter, mock_transcriber, mock_processor):
        """Test that quiet mode suppresses progress output."""
        # Create test audio file
        test_audio = os.path.join(self.temp_dir, "test.m4a")
        Path(test_audio).touch()
        
        # Setup mocks
        mock_processor_instance = Mock()
        mock_processor.return_value = mock_processor_instance
        mock_processor_instance.validate_file.return_value = True
        
        mock_transcriber_instance = Mock()
        mock_transcriber.return_value = mock_transcriber_instance
        mock_transcriber_instance.transcribe_file.return_value = Mock(
            error_message=None, 
            transcribed_text="Test transcription"
        )
        
        mock_exporter_instance = Mock()
        mock_exporter.return_value = mock_exporter_instance
        mock_exporter_instance.save_transcription_result.return_value = "/path/to/output.txt"
        
        result = self.runner.invoke(transcribe, [
            test_audio,
            '--quiet'
        ])
        
        assert result.exit_code == 0
        # In quiet mode, progress indicators should not be present
        assert "🎤" not in result.output
        assert "Loading Whisper model" not in result.output