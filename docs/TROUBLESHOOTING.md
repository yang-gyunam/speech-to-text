# Troubleshooting Guide

This guide helps you resolve common issues when using the Speech-to-Text application.

Note: This application works offline after initial setup. Most issues occur during installation or first-time model download.

## Quick Diagnostics

Before troubleshooting specific issues, run the system check:

```bash
speech-to-text doctor
```

This command checks:
- Python version compatibility
- Required dependencies
- FFmpeg installation
- Configuration validity
- File system permissions

## Installation Issues

### 1. Python Version Error

**Error**: `Python 3.8+ required`

**Solution**:
```bash
# Check your Python version
python3 --version

# Install Python 3.8+ using Homebrew
brew install python@3.11

# Or update your PATH to use the correct Python
export PATH="/usr/local/bin:$PATH"
```

### 2. FFmpeg Not Found

**Error**: `FFmpeg not found in PATH` or `FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'`

**Solutions**:
```bash
# Install FFmpeg using Homebrew (recommended)
brew install ffmpeg

# Install using MacPorts
sudo port install ffmpeg

# Verify installation
ffmpeg -version

# If still not found, add to PATH
export PATH="/usr/local/bin:$PATH"
```

### 3. Whisper Installation Issues

**Error**: `No module named 'whisper'` or `Failed to load Whisper model`

**Solutions**:
```bash
# Reinstall OpenAI Whisper
pip uninstall openai-whisper
pip install openai-whisper

# If you have Apple Silicon Mac, ensure you have the right version
pip install openai-whisper --upgrade

# Clear pip cache if needed
pip cache purge
```

### 4. pydub Installation Issues

**Error**: `No module named 'pydub'` or `AudioSegment` errors

**Solutions**:
```bash
# Reinstall pydub
pip uninstall pydub
pip install pydub

# Install with additional audio format support
pip install pydub[scipy]
```

## Runtime Issues

### 1. File Not Found Errors

**Error**: `FileNotFoundError: [Errno 2] No such file or directory: 'filename.m4a'`

**Solutions**:
```bash
# Check if file exists
ls -la filename.m4a

# Use absolute path
speech-to-text /full/path/to/filename.m4a

# Check file permissions
chmod 644 filename.m4a

# Verify file is not corrupted
speech-to-text info filename.m4a
```

### 2. Unsupported Format Errors

**Error**: `Unsupported audio format` or `Could not load audio file`

**Solutions**:
```bash
# Check supported formats
speech-to-text formats

# Convert unsupported format using FFmpeg
ffmpeg -i input.mov -acodec aac output.m4a
ffmpeg -i input.webm -acodec aac output.m4a

# Check file format
file filename.m4a
```

### 3. Permission Denied Errors

**Error**: `PermissionError: [Errno 13] Permission denied`

**Solutions**:
```bash
# Fix file permissions
chmod 644 audio-file.m4a

# Fix directory permissions
chmod 755 /path/to/audio/directory

# Check if file is in use by another application
lsof audio-file.m4a

# Run with different user (if necessary)
sudo speech-to-text audio-file.m4a
```

### 4. Memory Issues

**Error**: `MemoryError` or `Out of memory` or system becomes unresponsive

**Solutions**:
```bash
# Use smaller model
speech-to-text --model-size tiny large-file.m4a

# Split large files
ffmpeg -i large-file.m4a -f segment -segment_time 300 -c copy part_%03d.m4a

# Check available memory
top -l 1 | grep PhysMem

# Close other applications
# Process files one at a time instead of batch
```

### 5. Disk Space Issues

**Error**: `No space left on device` or `OSError: [Errno 28]`

**Solutions**:
```bash
# Check disk space
df -h

# Clean up temporary files
rm -rf /tmp/whisper_*
rm -rf ~/.cache/whisper

# Use different output directory
speech-to-text --output-dir /path/to/larger/disk recording.m4a

# Clean up old transcripts
find ./output -name "*.txt" -mtime +30 -delete
```

## Audio Processing Issues

### 1. Poor Transcription Quality

**Problem**: Transcription is inaccurate or contains many errors

**Solutions**:
```bash
# Use larger model for better accuracy
speech-to-text --model-size large recording.m4a

# Verify correct language setting
speech-to-text --language ko recording.m4a  # for Korean
speech-to-text --language en recording.m4a  # for English

# Check audio quality
speech-to-text info recording.m4a

# Preprocess audio to improve quality
ffmpeg -i noisy-audio.m4a -af "highpass=f=200,lowpass=f=3000" clean-audio.m4a
```

### 2. No Audio Detected

**Problem**: Transcription returns empty text or "No speech detected"

**Solutions**:
```bash
# Check if audio file has content
speech-to-text info recording.m4a

# Verify audio is not silent
ffmpeg -i recording.m4a -af "volumedetect" -f null -

# Increase audio volume
ffmpeg -i quiet-audio.m4a -af "volume=2.0" louder-audio.m4a

# Try different model
speech-to-text --model-size medium recording.m4a
```

### 3. Audio Conversion Failures

**Error**: `Audio conversion failed` or `Could not convert audio format`

**Solutions**:
```bash
# Check if FFmpeg can read the file
ffmpeg -i problematic-file.m4a

# Try manual conversion first
ffmpeg -i problematic-file.m4a -acodec aac converted-file.m4a

# Check file integrity
ffmpeg -v error -i problematic-file.m4a -f null -

# Use different audio codec
ffmpeg -i input.m4a -acodec libmp3lame output.mp3
```

## Configuration Issues

### 1. Configuration File Errors

**Error**: `Configuration error` or `Invalid configuration`

**Solutions**:
```bash
# Validate configuration file
speech-to-text show-config --config my-config.json

# Create new default configuration
speech-to-text init-config --output new-config.json

# Check JSON syntax
python -m json.tool my-config.json

# Use minimal configuration
echo '{"language": "ko"}' > minimal-config.json
speech-to-text --config minimal-config.json recording.m4a
```

### 2. Environment Variable Issues

**Problem**: Environment variables not being recognized

**Solutions**:
```bash
# Check current environment variables
env | grep SPEECH_TO_TEXT

# Set variables correctly
export SPEECH_TO_TEXT_LANGUAGE=ko
export SPEECH_TO_TEXT_MODEL_SIZE=base

# Verify variables are set
echo $SPEECH_TO_TEXT_LANGUAGE

# Add to shell profile for persistence
echo 'export SPEECH_TO_TEXT_LANGUAGE=ko' >> ~/.zshrc
source ~/.zshrc
```

## Performance Issues

### 1. Slow Processing

**Problem**: Transcription takes too long

**Solutions**:
```bash
# Use faster model
speech-to-text --model-size tiny recording.m4a

# Check system resources
top -l 1

# Close other applications
# Ensure sufficient RAM available

# Process smaller chunks
ffmpeg -i long-recording.m4a -f segment -segment_time 600 -c copy chunk_%03d.m4a
```

### 2. High CPU Usage

**Problem**: Application uses too much CPU

**Solutions**:
```bash
# Use smaller model
speech-to-text --model-size tiny recording.m4a

# Process files sequentially instead of batch
for file in *.m4a; do
    speech-to-text "$file"
    sleep 5  # Brief pause between files
done

# Monitor CPU usage
top -pid $(pgrep -f speech-to-text)
```

## Network and Model Issues

### 1. Model Download Failures

**Error**: `Failed to download model` or `Connection timeout`

**Solutions**:
```bash
# Check internet connection
ping github.com

# Clear model cache and retry
rm -rf ~/.cache/whisper
speech-to-text --model-size base recording.m4a

# Download model manually
python -c "import whisper; whisper.load_model('base')"

# Use different model size
speech-to-text --model-size tiny recording.m4a
```

### 2. Model Loading Errors

**Error**: `Failed to load model` or `Model not found`

**Solutions**:
```bash
# Clear model cache
rm -rf ~/.cache/whisper

# Reinstall whisper
pip uninstall openai-whisper
pip install openai-whisper

# Check available disk space
df -h ~/.cache

# Try different model
speech-to-text --model-size tiny recording.m4a
```

## Batch Processing Issues

### 1. Batch Processing Stops

**Problem**: Batch processing stops partway through

**Solutions**:
```bash
# Use verbose mode to see where it stops
speech-to-text --batch --verbose ./recordings/

# Process files individually to identify problematic files
for file in ./recordings/*.m4a; do
    echo "Processing: $file"
    speech-to-text "$file" || echo "Failed: $file"
done

# Skip problematic files
speech-to-text --batch ./recordings/ 2>&1 | tee batch.log
```

### 2. Mixed Results in Batch

**Problem**: Some files process successfully, others fail

**Solutions**:
```bash
# Check individual file info
for file in ./recordings/*.m4a; do
    speech-to-text info "$file"
done

# Process with error handling
speech-to-text --batch --verbose ./recordings/ 2>&1 | tee batch-results.log

# Retry failed files with different settings
grep "ERROR" batch-results.log | # extract failed files and retry
```

## macOS-Specific Issues

### 1. Gatekeeper Issues

**Error**: `"speech-to-text" cannot be opened because the developer cannot be verified`

**Solutions**:
```bash
# Allow the application
sudo spctl --master-disable

# Or add specific exception
sudo spctl --add /path/to/speech-to-text

# Re-enable Gatekeeper after use
sudo spctl --master-enable
```

### 2. Microphone Permissions

**Problem**: Issues with audio file access

**Solutions**:
1. Go to System Preferences → Security & Privacy → Privacy
2. Select "Microphone" or "Files and Folders"
3. Add Terminal or your terminal application
4. Restart terminal and try again

### 3. Path Issues on macOS

**Problem**: Command not found after installation

**Solutions**:
```bash
# Check if installed correctly
pip show speech-to-text

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Or use full path
python -m speech_to_text recording.m4a

# Add to shell profile
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

## Getting Additional Help

### 1. Enable Debug Mode

```bash
# Run with verbose output
speech-to-text --verbose recording.m4a

# Check log files
ls -la logs/
cat logs/speech_to_text.log
```

### 2. Collect System Information

```bash
# System check
speech-to-text doctor

# Python environment info
pip list | grep -E "(whisper|pydub|click)"

# System information
uname -a
python --version
ffmpeg -version
```

### 3. Create Minimal Test Case

```bash
# Test with a small, known-good file
# Create a short test recording on your iPhone
# Try with minimal options
speech-to-text --model-size tiny test-recording.m4a
```

### 4. Check for Updates

```bash
# Update the application
git pull  # if installed from source
pip install --upgrade openai-whisper

# Check for newer versions
pip list --outdated
```

## Common Error Messages and Solutions

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| `FFmpeg not found` | FFmpeg not installed | `brew install ffmpeg` |
| `No module named 'whisper'` | Whisper not installed | `pip install openai-whisper` |
| `Permission denied` | File permissions | `chmod 644 file.m4a` |
| `Unsupported format` | Wrong file format | Convert with FFmpeg |
| `Out of memory` | File too large | Use smaller model or split file |
| `No space left` | Disk full | Free up space or use different output dir |
| `Model not found` | Model download failed | Clear cache and retry |
| `Connection timeout` | Network issue | Check internet connection |

## Prevention Tips

1. **Regular Updates**: Keep dependencies updated
2. **System Maintenance**: Regularly clean up temporary files
3. **File Organization**: Keep audio files organized and accessible
4. **Backup Configurations**: Save working configuration files
5. **Test First**: Test with small files before batch processing
6. **Monitor Resources**: Keep an eye on disk space and memory usage
7. **Quality Audio**: Use good quality audio files for better results

If you continue to experience issues after trying these solutions, please check the project's issue tracker or create a new issue with:
- Your system information (`speech-to-text doctor` output)
- The exact error message
- Steps to reproduce the problem
- Sample audio file (if possible)