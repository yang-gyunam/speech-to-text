# CLI Usage Examples

This document provides comprehensive examples of how to use the Speech-to-Text CLI application in various scenarios.

Note: This application works completely offline after initial setup. All processing is done locally on your machine.

## Basic Examples

### Single File Transcription

```bash
# Transcribe an iPhone recording
speech-to-text recording.m4a

# Transcribe with custom output directory
speech-to-text --output-dir ./my-transcripts recording.m4a

# Transcribe in English instead of Korean (default)
speech-to-text --language en english-recording.wav
```

### Batch Processing

```bash
# Process all audio files in a directory
speech-to-text --batch ./recordings/

# Process files recursively (including subdirectories)
speech-to-text --batch --recursive ./recordings/

# Batch process with custom output directory
speech-to-text --batch ./recordings/ --output-dir ./transcripts
```

## Advanced Examples

### Model Selection

```bash
# Use tiny model for fast processing (lower accuracy)
speech-to-text --model-size tiny recording.m4a

# Use large model for best accuracy (slower processing)
speech-to-text --model-size large important-meeting.m4a

# Compare different models
speech-to-text --model-size tiny recording.m4a --output-dir ./tiny-results
speech-to-text --model-size large recording.m4a --output-dir ./large-results
```

### Output Options

```bash
# Include metadata in output files
speech-to-text --include-metadata recording.m4a

# Quiet mode (no progress output) - useful for scripts
speech-to-text --quiet recording.m4a

# Verbose mode for debugging
speech-to-text --verbose recording.m4a
```

## Configuration Examples

### Using Configuration Files

```bash
# Create a default configuration file
speech-to-text init-config

# Create a YAML configuration file
speech-to-text init-config --format yaml --output my-settings.yaml

# Use a specific configuration file
speech-to-text --config ./my-settings.json recording.m4a
```

Example configuration file (`my-settings.json`):
```json
{
  "language": "ko",
  "model_size": "base",
  "output_dir": "./transcripts",
  "batch_mode": false,
  "recursive": true,
  "include_metadata": true,
  "quiet": false,
  "verbose": false,
  "log_level": "INFO"
}
```

### Saving Current Settings

```bash
# Save current command-line options to a config file
speech-to-text --save-config ./my-preset.json --language en --model-size large --include-metadata

# Then use the saved settings
speech-to-text --config ./my-preset.json recording.m4a
```

### Environment Variables

```bash
# Set default language
export SPEECH_TO_TEXT_LANGUAGE=en

# Set default model size
export SPEECH_TO_TEXT_MODEL_SIZE=large

# Set default output directory
export SPEECH_TO_TEXT_OUTPUT_DIR=./transcripts

# Now these settings will be used by default
speech-to-text recording.m4a
```

## Real-World Scenarios

### Scenario 1: Meeting Transcription

```bash
# High-accuracy transcription for important meetings
speech-to-text --model-size large --include-metadata --verbose meeting-2024-01-15.m4a

# Batch process multiple meeting recordings
speech-to-text --batch --model-size large --include-metadata ./meetings/
```

### Scenario 2: Quick Voice Memos

```bash
# Fast transcription for quick voice memos
speech-to-text --model-size tiny --quiet voice-memo.m4a

# Process daily voice memos in batch
speech-to-text --batch --model-size tiny ./daily-memos/
```

### Scenario 3: Interview Transcription

```bash
# Create configuration for interview transcription
cat > interview-config.json << EOF
{
  "language": "ko",
  "model_size": "medium",
  "include_metadata": true,
  "output_dir": "./interview-transcripts",
  "verbose": true
}
EOF

# Use the configuration
speech-to-text --config interview-config.json interview-01.m4a
```

### Scenario 4: Automated Processing Script

```bash
#!/bin/bash
# automated-transcription.sh

# Set up environment
export SPEECH_TO_TEXT_LANGUAGE=ko
export SPEECH_TO_TEXT_MODEL_SIZE=base
export SPEECH_TO_TEXT_OUTPUT_DIR=./daily-transcripts

# Create output directory with today's date
OUTPUT_DIR="./transcripts/$(date +%Y-%m-%d)"
mkdir -p "$OUTPUT_DIR"

# Process all new recordings
speech-to-text --batch --quiet --output-dir "$OUTPUT_DIR" ./new-recordings/

# Move processed files to archive
mv ./new-recordings/* ./archive/

echo "Daily transcription complete. Results in: $OUTPUT_DIR"
```

## Utility Commands

### File Information

```bash
# Get information about an audio file
speech-to-text info recording.m4a

# Check supported formats
speech-to-text formats

# System health check
speech-to-text doctor
```

### Configuration Management

```bash
# Show current configuration
speech-to-text show-config

# Show current configuration with custom config file
speech-to-text show-config --config ./my-settings.json

# Get help and examples
speech-to-text examples
speech-to-text --help
```

## Integration Examples

### With Other Tools

```bash
# Convert video to audio, then transcribe
ffmpeg -i video.mp4 -vn -acodec aac audio.m4a
speech-to-text audio.m4a

# Transcribe and immediately open result
speech-to-text recording.m4a && open ./output/recording.txt

# Transcribe multiple files and create a combined document
speech-to-text --batch ./recordings/
cat ./output/*.txt > combined-transcript.txt
```

### Automation with cron

```bash
# Add to crontab for daily processing
# Process recordings every day at 2 AM
0 2 * * * /path/to/speech-to-text --batch --quiet /path/to/recordings/ --output-dir /path/to/transcripts/$(date +\%Y-\%m-\%d)
```

## Performance Optimization

### For Large Files

```bash
# Split large files before processing
ffmpeg -i large-recording.m4a -f segment -segment_time 600 -c copy part_%03d.m4a

# Process parts in batch
speech-to-text --batch --model-size base ./parts/

# Combine results
cat ./output/part_*.txt > complete-transcript.txt
```

### For Many Small Files

```bash
# Use smaller model for faster batch processing
speech-to-text --batch --model-size tiny ./voice-memos/

# Process with minimal output
speech-to-text --batch --quiet --model-size base ./recordings/
```

## Error Handling Examples

### Handling Failed Files

```bash
# Process batch and check for errors
speech-to-text --batch --verbose ./recordings/ 2>&1 | tee processing.log

# Find failed files from log
grep "ERROR" processing.log

# Retry failed files with different settings
speech-to-text --model-size small failed-file.m4a
```

### Validation Before Processing

```bash
# Check file info before transcribing
speech-to-text info suspicious-file.m4a

# Validate system before batch processing
speech-to-text doctor

# Test with a small file first
speech-to-text --model-size tiny test-file.m4a
```

## Tips and Best Practices

1. **Start Small**: Test with a small file and `tiny` model first
2. **Choose Right Model**: Use `base` for most cases, `large` for important content
3. **Batch Processing**: More efficient than processing files individually
4. **Configuration Files**: Save time by creating presets for different use cases
5. **System Check**: Run `speech-to-text doctor` if you encounter issues
6. **Audio Quality**: Better audio quality = better transcription results
7. **Language Setting**: Ensure correct language setting for best results
8. **Output Organization**: Use dated output directories for better organization

## Common Workflows

### Daily Voice Memo Processing

```bash
# 1. Create daily directory
mkdir -p "./transcripts/$(date +%Y-%m-%d)"

# 2. Process today's recordings
speech-to-text --batch --quiet ./voice-memos/ --output-dir "./transcripts/$(date +%Y-%m-%d)"

# 3. Archive processed files
mv ./voice-memos/* ./archive/voice-memos/
```

### Meeting Documentation Workflow

```bash
# 1. High-quality transcription
speech-to-text --model-size large --include-metadata meeting.m4a

# 2. Review and edit the transcript
open ./output/meeting.txt

# 3. Create summary (manual step)
# Edit the file to create meeting minutes
```

### Multi-language Content

```bash
# Process Korean content
speech-to-text --language ko korean-recording.m4a

# Process English content
speech-to-text --language en english-recording.wav

# Process mixed content (use auto-detection)
speech-to-text --language auto mixed-language.m4a
```