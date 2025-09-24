"""
Configuration management for the speech-to-text application.

This module provides configuration file support, default settings management,
and configuration validation.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict

from .exceptions import FileSystemError


@dataclass
class AppConfig:
    """Application configuration settings."""
    
    # Default settings
    output_dir: str = "./output"
    language: str = "ko"
    model_size: str = "base"
    batch_mode: bool = False
    recursive: bool = True
    include_metadata: bool = True
    quiet: bool = False
    verbose: bool = False
    
    # Advanced settings
    log_level: str = "INFO"
    log_dir: Optional[str] = None
    enable_structured_logging: bool = False
    max_file_size_mb: int = 100
    timeout_seconds: int = 300
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Create config from dictionary."""
        # Filter out unknown keys
        valid_keys = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)


class ConfigManager:
    """Manages application configuration from files and environment variables."""
    
    CONFIG_FILENAMES = [
        "speech-to-text.json",
        "speech-to-text.yaml",
        "speech-to-text.yml",
        ".speech-to-text.json",
        ".speech-to-text.yaml",
        ".speech-to-text.yml"
    ]
    
    def __init__(self):
        """Initialize configuration manager."""
        self.config = AppConfig()
        self._config_file_path: Optional[str] = None
    
    def load_config(self, config_path: Optional[str] = None) -> AppConfig:
        """
        Load configuration from file.
        
        Args:
            config_path: Optional path to config file. If None, searches for config files.
            
        Returns:
            AppConfig object with loaded settings
            
        Raises:
            FileSystemError: If config file cannot be read or parsed
        """
        if config_path:
            # Load specific config file
            self._load_config_file(config_path)
        else:
            # Search for config files in current directory and home directory
            self._search_and_load_config()
        
        # Override with environment variables
        self._load_from_environment()
        
        return self.config
    
    def save_config(self, config_path: str, config: Optional[AppConfig] = None) -> None:
        """
        Save configuration to file.
        
        Args:
            config_path: Path where to save the config file
            config: Optional config object to save. If None, uses current config.
            
        Raises:
            FileSystemError: If config file cannot be written
        """
        if config is None:
            config = self.config
        
        try:
            config_file = Path(config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = config.to_dict()
            
            if config_path.endswith(('.yaml', '.yml')):
                with open(config_file, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, default_flow_style=False, indent=2)
            else:
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2)
            
            self._config_file_path = str(config_file)
            
        except Exception as e:
            raise FileSystemError(f"Failed to save config file {config_path}: {str(e)}")
    
    def get_config_file_path(self) -> Optional[str]:
        """Get the path of the loaded config file."""
        return self._config_file_path
    
    def create_default_config(self, config_path: str) -> None:
        """
        Create a default configuration file.
        
        Args:
            config_path: Path where to create the config file
        """
        default_config = AppConfig()
        self.save_config(config_path, default_config)
    
    def _search_and_load_config(self) -> None:
        """Search for config files in standard locations."""
        search_paths = [
            Path.cwd(),  # Current directory
            Path.home(),  # Home directory
        ]
        
        for search_path in search_paths:
            for filename in self.CONFIG_FILENAMES:
                config_file = search_path / filename
                if config_file.exists():
                    try:
                        self._load_config_file(str(config_file))
                        return
                    except Exception:
                        # Continue searching if this file fails to load
                        continue
    
    def _load_config_file(self, config_path: str) -> None:
        """
        Load configuration from a specific file.
        
        Args:
            config_path: Path to the config file
            
        Raises:
            FileSystemError: If config file cannot be read or parsed
        """
        try:
            config_file = Path(config_path)
            
            if not config_file.exists():
                raise FileSystemError(f"Config file not found: {config_path}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_path.endswith(('.yaml', '.yml')):
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
            
            if config_data:
                self.config = AppConfig.from_dict(config_data)
            
            self._config_file_path = str(config_file)
            
        except Exception as e:
            raise FileSystemError(f"Failed to load config file {config_path}: {str(e)}")
    
    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        env_mappings = {
            'SPEECH_TO_TEXT_OUTPUT_DIR': 'output_dir',
            'SPEECH_TO_TEXT_LANGUAGE': 'language',
            'SPEECH_TO_TEXT_MODEL_SIZE': 'model_size',
            'SPEECH_TO_TEXT_BATCH_MODE': 'batch_mode',
            'SPEECH_TO_TEXT_RECURSIVE': 'recursive',
            'SPEECH_TO_TEXT_INCLUDE_METADATA': 'include_metadata',
            'SPEECH_TO_TEXT_QUIET': 'quiet',
            'SPEECH_TO_TEXT_VERBOSE': 'verbose',
            'SPEECH_TO_TEXT_LOG_LEVEL': 'log_level',
            'SPEECH_TO_TEXT_LOG_DIR': 'log_dir',
            'SPEECH_TO_TEXT_MAX_FILE_SIZE_MB': 'max_file_size_mb',
            'SPEECH_TO_TEXT_TIMEOUT_SECONDS': 'timeout_seconds',
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert string values to appropriate types
                if config_key in ['batch_mode', 'recursive', 'include_metadata', 'quiet', 'verbose', 'enable_structured_logging']:
                    env_value = env_value.lower() in ('true', '1', 'yes', 'on')
                elif config_key in ['max_file_size_mb', 'timeout_seconds']:
                    env_value = int(env_value)
                
                setattr(self.config, config_key, env_value)
    
    def validate_config(self) -> None:
        """
        Validate the current configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate model size
        valid_models = ['tiny', 'base', 'small', 'medium', 'large']
        if self.config.model_size not in valid_models:
            raise ValueError(f"Invalid model size: {self.config.model_size}. Valid options: {valid_models}")
        
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.config.log_level not in valid_log_levels:
            raise ValueError(f"Invalid log level: {self.config.log_level}. Valid options: {valid_log_levels}")
        
        # Validate file size limit
        if self.config.max_file_size_mb <= 0:
            raise ValueError("max_file_size_mb must be positive")
        
        # Validate timeout
        if self.config.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
    
    def get_example_config(self) -> str:
        """Get an example configuration file content."""
        example_config = {
            "output_dir": "./transcripts",
            "language": "ko",
            "model_size": "base",
            "batch_mode": False,
            "recursive": True,
            "include_metadata": True,
            "quiet": False,
            "verbose": False,
            "log_level": "INFO",
            "log_dir": "./logs",
            "max_file_size_mb": 100,
            "timeout_seconds": 300
        }
        
        return json.dumps(example_config, indent=2)


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load application configuration."""
    return get_config_manager().load_config(config_path)


def save_config(config_path: str, config: Optional[AppConfig] = None) -> None:
    """Save application configuration."""
    get_config_manager().save_config(config_path, config)