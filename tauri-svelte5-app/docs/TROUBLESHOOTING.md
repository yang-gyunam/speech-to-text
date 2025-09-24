# Troubleshooting Guide

This comprehensive guide helps you resolve common issues with Speech to Text.

## Emergency Quick Fixes

### App Won't Start
```bash
# Quick security fix
sudo xattr -rd com.apple.quarantine "/Applications/Speech to Text.app"
```

### App Crashes Immediately
1. Restart your Mac
2. Re-download and reinstall the app
3. Check system requirements (macOS 12.0+)

### Processing Stuck at 0%
1. Cancel processing (Cmd+.)
2. Try a smaller audio file first
3. Switch to "Base" model in settings

## Systematic Troubleshooting

### Step 1: Check System Requirements
Ensure your system meets minimum requirements:

```
✓ macOS 12.0 (Monterey) or later
✓ 4GB RAM (8GB recommended)
✓ 1GB free disk space
✓ Intel x64 or Apple Silicon processor
```

**Check your system:**
1. Apple Menu → About This Mac
2. Verify macOS version and memory
3. Check available storage in Disk Utility

### Step 2: Verify Installation
Confirm proper installation:

```
✓ App is in /Applications/ folder
✓ App icon appears correctly
✓ No quarantine attributes blocking execution
```

**Fix installation issues:**
```bash
# Remove quarantine (if needed)
sudo xattr -rd com.apple.quarantine "/Applications/Speech to Text.app"

# Check app bundle integrity
codesign -v "/Applications/Speech to Text.app"
```

### Step 3: Test Basic Functionality
Try with a known-good file:

1. Use a short (< 1 minute) M4A file
2. Select "Base" model
3. Ensure Korean or English language
4. Process in a clean environment (close other apps)

## Common Issues and Solutions

### Installation Problems

#### "App is damaged and can't be opened"
**Cause**: Incomplete download or quarantine issues
**Solutions**:
1. Re-download the DMG file completely
2. Clear quarantine attributes:
   ```bash
   sudo xattr -rd com.apple.quarantine "/Applications/Speech to Text.app"
   ```
3. Verify download integrity (check file size matches release notes)

#### "App can't be opened because Apple cannot check it for malicious software"
**Cause**: Gatekeeper security protection
**Solutions**:
1. **System Preferences Method**:
   - System Preferences → Security & Privacy
   - Click "Open Anyway" button
   - Confirm in dialog

2. **Right-click Method**:
   - Right-click app in Applications
   - Select "Open" from menu
   - Click "Open" in confirmation

3. **Terminal Method**:
   ```bash
   sudo spctl --master-disable  # Temporarily disable Gatekeeper
   # Open the app, then re-enable:
   sudo spctl --master-enable
   ```

#### Installation hangs or fails
**Cause**: Insufficient permissions or disk space
**Solutions**:
1. Check available disk space (need 2GB+)
2. Repair disk permissions:
   ```bash
   sudo diskutil repairPermissions /
   ```
3. Try installing to different location temporarily

### Performance Issues

#### Very Slow Processing
**Symptoms**: Processing takes much longer than expected
**Diagnosis**:
```bash
# Check CPU usage
top -o cpu

# Check memory usage
vm_stat

# Check disk space
df -h
```

**Solutions**:
1. **Reduce Model Size**:
   - Switch from "Large" to "Base" model
   - "Base" model is 10x smaller and 3x faster

2. **Free System Resources**:
   - Close unnecessary applications
   - Quit memory-intensive apps (browsers, video editors)
   - Restart the Mac if needed

3. **Optimize File Size**:
   - Break large files (>1 hour) into smaller segments
   - Use compressed formats (M4A, MP3) instead of WAV

4. **Check Thermal Throttling**:
   - Ensure adequate ventilation
   - Use cooling pad for laptops
   - Monitor CPU temperature with tools like TG Pro

#### High Memory Usage
**Symptoms**: System becomes sluggish, swap usage increases
**Solutions**:
1. **Model Selection**:
   ```
   Tiny:   ~1GB RAM
   Base:   ~2GB RAM
   Small:  ~3GB RAM
   Medium: ~4GB RAM
   Large:  ~6GB RAM
   ```

2. **Process Management**:
   - Process one file at a time
   - Avoid batch processing large files
   - Restart app between large processing sessions

3. **System Optimization**:
   ```bash
   # Clear system caches
   sudo purge
   
   # Check memory pressure
   memory_pressure
   ```

#### App Becomes Unresponsive
**Symptoms**: UI freezes, spinning beach ball
**Immediate Actions**:
1. Wait 2-3 minutes (large models take time to load)
2. Force quit if truly frozen: Cmd+Option+Esc
3. Restart the application

**Prevention**:
1. Don't switch between apps during model loading
2. Ensure sufficient RAM available
3. Use smaller models on older Macs

### Audio File Issues

#### File Not Recognized or Won't Upload
**Symptoms**: Drag and drop doesn't work, file rejected
**Diagnosis**:
1. **Check File Format**:
   ```bash
   # Check file type
   file your-audio-file.m4a
   
   # Check file size
   ls -lh your-audio-file.m4a
   ```

2. **Supported Formats Only**:
   - ✅ M4A (iPhone recordings)
   - ✅ WAV (uncompressed)
   - ✅ MP3 (compressed)
   - ✅ AAC (Advanced Audio Coding)
   - ✅ FLAC (lossless)
   - ❌ MOV, MP4, AVI (video files)
   - ❌ WMA, OGG (unsupported audio)

**Solutions**:
1. **Convert Unsupported Files**:
   ```bash
   # Using ffmpeg (if installed)
   ffmpeg -i input.mov -vn -acodec copy output.m4a
   
   # Using QuickTime Player
   # File → Export As → Audio Only
   ```

2. **Fix Corrupted Files**:
   - Try playing file in QuickTime Player first
   - Re-export from original source if possible
   - Use audio repair tools if necessary

#### Poor Transcription Quality
**Symptoms**: Mostly incorrect text, gibberish output
**Diagnosis Checklist**:
```
□ Audio is clear and audible
□ Language setting matches audio content
□ Minimal background noise
□ Single speaker (not multiple people talking)
□ Appropriate model size selected
```

**Solutions by Issue**:

1. **Wrong Language Detected**:
   - Manually set language in Settings
   - Don't rely on auto-detection for mixed content
   - Use "Korean" for Korean speech, "English" for English

2. **Poor Audio Quality**:
   - Use noise reduction software before processing
   - Re-record in quieter environment if possible
   - Increase recording volume (but avoid clipping)

3. **Multiple Speakers**:
   - Whisper works best with single speakers
   - Consider speaker diarization tools for multi-speaker content
   - Process segments with single speakers separately

4. **Technical/Specialized Content**:
   - Use "Large" model for better accuracy
   - Manually correct technical terms after processing
   - Consider training custom vocabulary (future feature)

### Processing Errors

#### Processing Fails with Error Message
**Common Error Messages and Solutions**:

1. **"Failed to load model"**:
   ```
   Cause: Insufficient memory or corrupted model
   Solution: 
   - Try smaller model size
   - Restart application
   - Clear application cache
   ```

2. **"Audio file could not be processed"**:
   ```
   Cause: Corrupted or unsupported audio format
   Solution:
   - Verify file plays in other applications
   - Convert to supported format
   - Check file permissions
   ```

3. **"Processing timeout"**:
   ```
   Cause: File too large or system overloaded
   Solution:
   - Break file into smaller segments
   - Close other applications
   - Use smaller model size
   ```

4. **"Insufficient disk space"**:
   ```
   Cause: Not enough space for temporary files
   Solution:
   - Free up disk space (need 2x file size available)
   - Change output directory to drive with more space
   - Clear Downloads and Trash folders
   ```

#### Processing Stops Unexpectedly
**Symptoms**: Progress bar stops, no error message
**Investigation**:
```bash
# Check system logs
log show --predicate 'subsystem contains "com.gnyang.speechtotext"' --last 1h

# Check crash reports
ls ~/Library/Logs/DiagnosticReports/*SpeechToText*
```

**Solutions**:
1. **Memory Issues**:
   - Monitor memory usage during processing
   - Close other applications
   - Try smaller model or shorter files

2. **Thermal Issues**:
   - Check if Mac is getting hot
   - Ensure proper ventilation
   - Take breaks between large processing jobs

3. **File System Issues**:
   - Check disk for errors: Disk Utility → First Aid
   - Ensure output directory is writable
   - Try different output location

### UI and Interface Issues

#### Settings Don't Save
**Symptoms**: Changes revert after restart
**Causes and Solutions**:
1. **Permissions Issue**:
   ```bash
   # Check preferences directory
   ls -la ~/Library/Preferences/com.gnyang.speechtotext.*
   
   # Fix permissions if needed
   chmod 644 ~/Library/Preferences/com.gnyang.speechtotext.*
   ```

2. **Corrupted Preferences**:
   ```bash
   # Reset to defaults
   rm ~/Library/Preferences/com.gnyang.speechtotext.*
   # Restart app to recreate defaults
   ```

#### Interface Elements Missing or Broken
**Symptoms**: Buttons don't appear, layout issues
**Solutions**:
1. **Display Issues**:
   - Try different window sizes
   - Reset window position: Window → Zoom
   - Check display scaling settings

2. **Theme Issues**:
   - Switch between light/dark mode
   - Reset appearance settings
   - Update macOS if using older version

#### Drag and Drop Not Working
**Symptoms**: Files don't register when dragged
**Solutions**:
1. **Permissions**:
   - Grant file access permissions when prompted
   - Check Privacy settings: System Preferences → Security & Privacy → Files and Folders

2. **File Association**:
   - Try "Browse Files" button instead
   - Check if files are locked or in use by other apps
   - Verify file formats are supported

## Advanced Diagnostics

### Collecting Debug Information

#### System Information
```bash
# System details
system_profiler SPSoftwareDataType SPHardwareDataType

# Memory and CPU
vm_stat && sysctl -n hw.ncpu hw.memsize

# Disk space
df -h && du -sh ~/Library/Caches/com.gnyang.speechtotext.*
```

#### Application Logs
```bash
# Application logs
log show --predicate 'subsystem contains "speechtotext"' --last 2h

# Crash reports
ls -la ~/Library/Logs/DiagnosticReports/*SpeechToText*

# Console messages
log stream --predicate 'subsystem contains "speechtotext"'
```

#### Performance Monitoring
```bash
# CPU usage by process
top -o cpu -n 10

# Memory usage details
vm_stat 1 10

# Disk I/O
iostat 1 10
```

### Creating Minimal Test Cases

When reporting issues, create a minimal test case:

1. **Use Short Audio File** (< 30 seconds)
2. **Default Settings** (Base model, Korean language)
3. **Clean Environment** (restart Mac, close other apps)
4. **Document Steps** exactly as performed
5. **Include System Info** (macOS version, Mac model, RAM)

### Performance Benchmarking

Test your system's performance:

```bash
# Create test audio file (if you have ffmpeg)
ffmpeg -f lavfi -i "sine=frequency=1000:duration=60" -ar 16000 test.wav

# Time the processing
time "/Applications/Speech to Text.app/Contents/MacOS/speech-to-text" test.wav
```

Expected processing times (Base model):
- **Apple Silicon**: ~1:4 ratio (1 min audio = 4 min processing)
- **Intel Mac**: ~1:8 ratio (1 min audio = 8 min processing)

## Getting Additional Help

### Before Contacting Support

1. **Try Safe Mode**: Restart Mac holding Shift key
2. **Test with Different File**: Use known-good audio file
3. **Check Recent Changes**: New software, system updates, etc.
4. **Document Everything**: Screenshots, error messages, steps

### Information to Include in Bug Reports

```
System Information:
- macOS version: 
- Mac model: 
- RAM: 
- Available disk space: 

Application Information:
- App version: 
- Model size used: 
- Language setting: 

Problem Description:
- What you were trying to do: 
- What happened instead: 
- Error messages (exact text): 
- Steps to reproduce: 

Files:
- Audio file format: 
- File size: 
- Duration: 
- Sample rate (if known): 
```

### Support Channels

1. **GitHub Issues**: [Report bugs and request features](https://github.com/speechtotext/tauri-gui-app/issues)
2. **Documentation**: Check all docs in the `docs/` folder
3. **Community**: User discussions (future)

### Emergency Contacts

For critical issues affecting business operations:
- Create high-priority GitHub issue
- Include "URGENT" in title
- Provide complete system information
- Include steps to reproduce

---

## Prevention Tips

### Regular Maintenance
- Keep macOS updated
- Restart the app periodically during heavy use
- Clear caches monthly
- Monitor available disk space

### Best Practices
- Test with small files first
- Use appropriate model sizes for your hardware
- Keep original audio files as backups
- Save transcriptions frequently

### Performance Optimization
- Close unnecessary applications during processing
- Use wired internet for downloads (not WiFi)
- Ensure adequate cooling for long processing sessions
- Consider upgrading RAM for heavy usage

Remember: Most issues are resolved by restarting the application or using a smaller model size. When in doubt, try the simplest solution first!