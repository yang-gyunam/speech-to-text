"""
Command-line interface for the speech-to-text application.

This module provides the main CLI entry point using Click framework,
handling user input, progress display, and coordinating all components.
"""

import sys
import time
from pathlib import Path
from typing import List, Optional

import click

from . import (
    AudioProcessor,
    FileManager,
    SpeechTranscriber,
    TextExporter,
    ErrorHandler,
    setup_logging,
    get_logger,
)
from .exceptions import SpeechToTextError
from .config import ConfigManager, AppConfig, get_config_manager


class ProgressDisplay:
    """Handles progress display during transcription operations."""
    
    def __init__(self, quiet: bool = False):
        """
        Initialize progress display.
        
        Args:
            quiet: If True, suppress progress output
        """
        self.quiet = quiet
        self.start_time = None
    
    def start_operation(self, message: str) -> None:
        """Start a new operation with progress tracking."""
        if not self.quiet:
            click.echo(f"🎤 {message}")
        self.start_time = time.time()
    
    def show_file_progress(self, current: int, total: int, filename: str) -> None:
        """Show progress for current file being processed."""
        if self.quiet:
            return
        
        progress_percent = (current / total) * 100 if total > 0 else 0
        file_display = Path(filename).name
        
        click.echo(f"   [{current}/{total}] ({progress_percent:.1f}%) Processing: {file_display}")
    
    def show_completion(self, message: str, count: Optional[int] = None) -> None:
        """Show completion message with timing."""
        if self.quiet:
            return
        
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        if count is not None:
            click.echo(f"✅ {message} ({count} files processed in {elapsed:.1f}s)")
        else:
            click.echo(f"✅ {message} (completed in {elapsed:.1f}s)")
    
    def show_error(self, message: str) -> None:
        """Show error message."""
        if not self.quiet:
            click.echo(f"❌ {message}", err=True)
    
    def show_warning(self, message: str) -> None:
        """Show warning message."""
        if not self.quiet:
            click.echo(f"⚠️  {message}")


@click.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option(
    '--output-dir', '-o',
    help='Output directory for transcribed text files'
)
@click.option(
    '--language', '-l',
    help='Language code for transcription'
)
@click.option(
    '--model-size', '-m',
    type=click.Choice(['tiny', 'base', 'small', 'medium', 'large']),
    help='Whisper model size'
)
@click.option(
    '--batch/--single', '-b/-s',
    default=None,
    help='Process all audio files in directory (batch mode) or single file'
)
@click.option(
    '--recursive/--no-recursive', '-r/-nr',
    default=None,
    help='Search subdirectories recursively in batch mode'
)
@click.option(
    '--include-metadata/--no-metadata',
    default=None,
    help='Include metadata in output files'
)
@click.option(
    '--quiet', '-q',
    is_flag=True,
    help='Suppress progress output'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose logging'
)
@click.option(
    '--config', '-c',
    type=click.Path(),
    help='Path to configuration file'
)
@click.option(
    '--save-config',
    type=click.Path(),
    help='Save current settings to configuration file and exit'
)
@click.version_option(version='0.1.0', prog_name='speech-to-text')
def transcribe(
    input_path: str,
    output_dir: Optional[str],
    language: Optional[str],
    model_size: Optional[str],
    batch: Optional[bool],
    recursive: Optional[bool],
    include_metadata: Optional[bool],
    quiet: bool,
    verbose: bool,
    config: Optional[str],
    save_config: Optional[str]
):
    """
    Convert iPhone audio recordings to text using OpenAI Whisper.
    
    INPUT_PATH can be either a single audio file or a directory containing audio files.
    
    Supported formats: .m4a, .wav, .mp3, .aac, .flac
    
    Examples:
    
        # Transcribe a single file
        speech-to-text recording.m4a
        
        # Transcribe all files in a directory
        speech-to-text --batch ./recordings/
        
        # Use different language and model
        speech-to-text --language en --model-size large recording.wav
        
        # Quiet mode with custom output directory
        speech-to-text --quiet --output-dir ./transcripts recording.m4a
        
        # Use configuration file
        speech-to-text --config ./my-config.json recording.m4a
        
        # Save current settings to config file
        speech-to-text --save-config ./my-config.json --language en --model-size large
    """
    # Load configuration
    config_manager = get_config_manager()
    
    try:
        app_config = config_manager.load_config(config)
        config_manager.validate_config()
    except Exception as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)
    
    # Override config with command line options (only if explicitly provided)
    if output_dir is not None:
        app_config.output_dir = output_dir
    if language is not None:
        app_config.language = language
    if model_size is not None:
        app_config.model_size = model_size
    if batch is not None:
        app_config.batch_mode = batch
    if recursive is not None:
        app_config.recursive = recursive
    if include_metadata is not None:
        app_config.include_metadata = include_metadata
    if quiet:
        app_config.quiet = quiet
    if verbose:
        app_config.verbose = verbose
    
    # Handle save-config option
    if save_config:
        try:
            config_manager.save_config(save_config, app_config)
            click.echo(f"Configuration saved to: {save_config}")
            sys.exit(0)
        except Exception as e:
            click.echo(f"Failed to save configuration: {e}", err=True)
            sys.exit(1)
    
    # Setup logging
    log_level = 'DEBUG' if app_config.verbose else app_config.log_level
    setup_logging(log_level=log_level, debug_mode=app_config.verbose, log_dir=app_config.log_dir)
    logger = get_logger(__name__)
    
    # Initialize progress display
    progress = ProgressDisplay(quiet=app_config.quiet)
    
    try:
        # Initialize components
        audio_processor = AudioProcessor()
        file_manager = FileManager(audio_processor)
        text_exporter = TextExporter()
        error_handler = ErrorHandler()
        
        # Create output directory
        output_path = file_manager.create_output_directory(app_config.output_dir)
        
        # Determine input files
        input_files = _get_input_files(
            input_path, app_config.batch_mode, app_config.recursive, audio_processor, file_manager, progress
        )
        
        if not input_files:
            progress.show_error("No audio files found to process")
            sys.exit(1)
        
        # Initialize transcriber
        progress.start_operation(f"Loading Whisper model ({app_config.model_size})...")
        transcriber = SpeechTranscriber(model_size=app_config.model_size)
        
        # Process files
        if len(input_files) == 1:
            _process_single_file(
                input_files[0], output_path, app_config.language, transcriber, 
                text_exporter, app_config.include_metadata, progress, logger
            )
        else:
            _process_batch_files(
                input_files, output_path, app_config.language, transcriber,
                text_exporter, app_config.include_metadata, progress, logger
            )
        
    except SpeechToTextError as e:
        error_handler.handle_error(e)
        progress.show_error(f"Application error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        progress.show_warning("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        progress.show_error(f"Unexpected error: {e}")
        sys.exit(1)


def _get_input_files(
    input_path: str,
    batch: bool,
    recursive: bool,
    audio_processor: AudioProcessor,
    file_manager: FileManager,
    progress: ProgressDisplay
) -> List[str]:
    """Get list of input files to process."""
    input_path_obj = Path(input_path)
    
    if input_path_obj.is_file():
        # Single file mode
        if batch:
            progress.show_warning("Input is a file but batch mode is enabled. Processing single file.")
        
        # Validate the file
        audio_processor.validate_file(input_path)
        return [input_path]
    
    elif input_path_obj.is_dir():
        # Directory mode
        if not batch:
            progress.show_error("Input is a directory but batch mode is not enabled. Use --batch flag.")
            return []
        
        # Find audio files in directory
        progress.start_operation(f"Scanning directory for audio files...")
        files = file_manager.find_audio_files(input_path, recursive=recursive)
        
        if files:
            progress.show_completion(f"Found {len(files)} audio files")
        
        return files
    
    else:
        progress.show_error(f"Invalid input path: {input_path}")
        return []


def _process_single_file(
    file_path: str,
    output_dir: str,
    language: str,
    transcriber: SpeechTranscriber,
    text_exporter: TextExporter,
    include_metadata: bool,
    progress: ProgressDisplay,
    logger
) -> None:
    """Process a single audio file."""
    file_name = Path(file_path).name
    progress.start_operation(f"Transcribing {file_name}...")
    
    # Transcribe the file
    result = transcriber.transcribe_file(file_path, language)
    
    if result.error_message:
        progress.show_error(f"Transcription failed: {result.error_message}")
        return
    
    # Generate output filename
    file_manager = FileManager()
    output_file = file_manager.generate_output_filename(file_path, output_dir)
    
    # Save the result
    saved_path = text_exporter.save_transcription_result(
        result, output_file, include_metadata=include_metadata
    )
    
    progress.show_completion(f"Transcription saved to: {saved_path}")
    
    # Show transcription preview if not quiet
    if not progress.quiet:
        preview = result.transcribed_text[:200]
        if len(result.transcribed_text) > 200:
            preview += "..."
        click.echo(f"\n📝 Preview: {preview}\n")


def _process_batch_files(
    file_paths: List[str],
    output_dir: str,
    language: str,
    transcriber: SpeechTranscriber,
    text_exporter: TextExporter,
    include_metadata: bool,
    progress: ProgressDisplay,
    logger
) -> None:
    """Process multiple audio files in batch."""
    total_files = len(file_paths)
    progress.start_operation(f"Starting batch transcription of {total_files} files...")
    
    # Progress callback for batch processing
    def progress_callback(current: int, total: int, current_file: str) -> None:
        if current < total:
            progress.show_file_progress(current + 1, total, current_file)
    
    # Transcribe all files
    results = transcriber.transcribe_batch(
        file_paths, language=language, progress_callback=progress_callback
    )
    
    # Save results
    saved_files = text_exporter.save_batch_results(
        results, output_dir, create_summary=True
    )
    
    # Calculate statistics
    successful = len([r for r in results if not r.error_message])
    failed = total_files - successful
    
    progress.show_completion(f"Batch processing complete", total_files)
    
    # Show summary if not quiet
    if not progress.quiet:
        click.echo(f"\n📊 Summary:")
        click.echo(f"   ✅ Successful: {successful}")
        if failed > 0:
            click.echo(f"   ❌ Failed: {failed}")
        click.echo(f"   📁 Output directory: {output_dir}")
        
        if 'summary' in saved_files:
            click.echo(f"   📋 Summary report: {saved_files['_summary']}")


# Additional CLI commands for advanced features
@click.group()
def cli():
    """Speech-to-Text CLI application."""
    pass


@cli.command()
def formats():
    """List supported audio formats."""
    audio_processor = AudioProcessor()
    supported = audio_processor.get_supported_formats()
    
    click.echo("Supported audio formats:")
    for fmt in supported:
        click.echo(f"  • {fmt}")


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def info(file_path: str):
    """Show information about an audio file."""
    try:
        audio_processor = AudioProcessor()
        file_info = audio_processor.get_audio_info(file_path)
        
        click.echo(f"Audio file information:")
        click.echo(f"  File: {file_info.file_path}")
        click.echo(f"  Size: {file_info.file_size:,} bytes")
        click.echo(f"  Format: {file_info.format}")
        
        if file_info.duration:
            click.echo(f"  Duration: {file_info.duration:.2f} seconds")
        if file_info.sample_rate:
            click.echo(f"  Sample rate: {file_info.sample_rate:,} Hz")
        if file_info.channels:
            click.echo(f"  Channels: {file_info.channels}")
            
    except Exception as e:
        click.echo(f"Error reading file info: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', type=click.Path(), help='Output file path for the config')
@click.option('--format', 'config_format', type=click.Choice(['json', 'yaml']), default='json', help='Config file format')
def init_config(output: Optional[str], config_format: str):
    """Create a default configuration file."""
    if not output:
        output = f"speech-to-text.{config_format}"
    
    try:
        config_manager = get_config_manager()
        config_manager.create_default_config(output)
        click.echo(f"Default configuration created: {output}")
        
        # Show example content
        click.echo("\nExample configuration:")
        click.echo(config_manager.get_example_config())
        
    except Exception as e:
        click.echo(f"Failed to create config file: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to configuration file')
def show_config(config: Optional[str]):
    """Show current configuration settings."""
    try:
        config_manager = get_config_manager()
        app_config = config_manager.load_config(config)
        
        click.echo("Current configuration:")
        click.echo("=" * 40)
        
        config_dict = app_config.to_dict()
        for key, value in config_dict.items():
            click.echo(f"  {key}: {value}")
        
        config_file = config_manager.get_config_file_path()
        if config_file:
            click.echo(f"\nLoaded from: {config_file}")
        else:
            click.echo("\nUsing default settings (no config file found)")
            
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
def examples():
    """Show usage examples and tips."""
    examples_text = """
Usage Examples:

Basic Usage:
  speech-to-text recording.m4a                    # Transcribe single file
  speech-to-text --batch ./recordings/            # Transcribe all files in directory
  speech-to-text --language en recording.wav      # Use English language model

Advanced Usage:
  speech-to-text --model-size large --verbose recording.m4a    # Use large model with verbose output
  speech-to-text --quiet --output-dir ./output recording.m4a   # Quiet mode with custom output
  speech-to-text --batch --no-recursive ./recordings/         # Batch mode, no subdirectories

Configuration:
  speech-to-text init-config                       # Create default config file
  speech-to-text init-config --format yaml        # Create YAML config file
  speech-to-text show-config                       # Show current settings
  speech-to-text --config ./my-config.json recording.m4a      # Use custom config

Saving Settings:
  speech-to-text --save-config ./my-settings.json --language en --model-size large
  
Environment Variables:
  export SPEECH_TO_TEXT_LANGUAGE=en
  export SPEECH_TO_TEXT_MODEL_SIZE=large
  export SPEECH_TO_TEXT_OUTPUT_DIR=./transcripts
  speech-to-text recording.m4a                    # Uses environment settings

Tips:
  • Use --model-size tiny for faster processing with lower accuracy
  • Use --model-size large for best accuracy (slower processing)
  • Korean language (ko) is the default, use --language en for English
  • Batch mode automatically processes all supported audio files in a directory
  • Use --quiet for scripts and automation
  • Use --verbose for troubleshooting
  • Configuration files are searched in current directory and home directory
  • Command line options override configuration file settings
  • Environment variables override configuration file settings
    """
    
    click.echo(examples_text)


@cli.command()
def doctor():
    """Check system requirements and configuration."""
    click.echo("Speech-to-Text System Check")
    click.echo("=" * 40)
    
    # Check Python version
    import sys
    click.echo(f"✓ Python version: {sys.version.split()[0]}")
    
    # Check dependencies
    try:
        import whisper
        click.echo("✓ OpenAI Whisper: Available")
    except ImportError:
        click.echo("✗ OpenAI Whisper: Not installed")
    
    try:
        import pydub
        click.echo("✓ pydub: Available")
    except ImportError as e:
        click.echo(f"✗ pydub: Not installed ({e})")
    except Exception as e:
        click.echo(f"⚠ pydub: Available but has issues ({e})")
    
    try:
        import yaml
        click.echo("✓ PyYAML: Available")
    except ImportError:
        click.echo("✗ PyYAML: Not installed")
    
    # Check FFmpeg
    try:
        from pydub.utils import which
        if which("ffmpeg"):
            click.echo("✓ FFmpeg: Available")
        else:
            click.echo("✗ FFmpeg: Not found in PATH")
    except:
        click.echo("? FFmpeg: Unable to check")
    
    # Check configuration
    try:
        config_manager = get_config_manager()
        app_config = config_manager.load_config()
        config_manager.validate_config()
        click.echo("✓ Configuration: Valid")
        
        config_file = config_manager.get_config_file_path()
        if config_file:
            click.echo(f"  Config file: {config_file}")
        else:
            click.echo("  Using default settings")
            
    except Exception as e:
        click.echo(f"✗ Configuration: {e}")
    
    # Check write permissions for default output directory
    try:
        from pathlib import Path
        output_dir = Path("./output")
        output_dir.mkdir(exist_ok=True)
        test_file = output_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
        click.echo("✓ Output directory: Writable")
    except Exception as e:
        click.echo(f"✗ Output directory: {e}")
    
    click.echo("\nIf you see any ✗ marks, please install the missing dependencies or fix the issues.")
    click.echo("Run 'pip install -r requirements.txt' to install missing Python packages.")


# Make transcribe the default command when no subcommand is provided
def main():
    """Main entry point for the CLI application."""
    import sys
    
    # List of subcommands
    subcommands = ['formats', 'info', 'init-config', 'show-config', 'examples', 'doctor']
    
    # If no arguments or first argument doesn't match a subcommand, use transcribe
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and not sys.argv[1] in subcommands):
        transcribe()
    else:
        cli()


# Add commands to the group
cli.add_command(transcribe, name='transcribe')
cli.add_command(formats)
cli.add_command(info)
cli.add_command(init_config, name='init-config')
cli.add_command(show_config, name='show-config')
cli.add_command(examples)
cli.add_command(doctor)


if __name__ == '__main__':
    main()