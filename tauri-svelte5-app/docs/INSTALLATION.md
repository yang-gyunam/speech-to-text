# Installation Guide

This guide provides detailed instructions for installing and setting up the Speech to Text application on macOS.

## System Requirements

### Minimum Requirements
- **Operating System**: macOS 12.0 (Monterey) or later
- **Memory**: 4GB RAM
- **Storage**: 1GB free disk space
- **Processor**: Intel x64 or Apple Silicon (M1/M2/M3)

### Recommended Requirements
- **Operating System**: macOS 13.0 (Ventura) or later
- **Memory**: 8GB RAM or more
- **Storage**: 2GB free disk space
- **Processor**: Apple Silicon (M1/M2/M3) for optimal performance

## Installation Methods

### Method 1: Download from Releases (Recommended)

1. **Download the Application**
   - Visit the [Releases page](https://github.com/speechtotext/tauri-gui-app/releases)
   - Download the appropriate DMG file for your Mac:
     - `Speech-to-Text-x86_64.dmg` for Intel Macs
     - `Speech-to-Text-aarch64.dmg` for Apple Silicon Macs

2. **Install the Application**
   - Double-click the downloaded DMG file
   - Drag the "Speech to Text" app to your Applications folder
   - Eject the DMG file

3. **First Launch**
   - Open the Applications folder
   - Double-click "Speech to Text" to launch
   - If you see a security warning, follow the steps in the [Security](#security) section below

### Method 2: Build from Source

If you prefer to build the application yourself:

1. **Prerequisites**
   ```bash
   # Install Node.js (18.0.0 or later)
   # Install Rust toolchain
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   
   # Install Xcode Command Line Tools
   xcode-select --install
   ```

2. **Clone and Build**
   ```bash
   git clone https://github.com/speechtotext/tauri-gui-app.git
   cd tauri-gui-app
   npm install
   npm run build:release
   ```

3. **Install Built Application**
   - The built app will be in `src-tauri/target/release/bundle/macos/`
   - Copy it to your Applications folder

## Security

### Gatekeeper and Code Signing

When you first launch the application, macOS may show a security warning because the app is not from the Mac App Store.

#### If you see "App can't be opened because it is from an unidentified developer":

1. **Method 1: System Preferences**
   - Go to System Preferences → Security & Privacy
   - Click "Open Anyway" next to the blocked app message
   - Click "Open" in the confirmation dialog

2. **Method 2: Right-click Method**
   - Right-click the app in Applications
   - Select "Open" from the context menu
   - Click "Open" in the confirmation dialog

3. **Method 3: Terminal Override**
   ```bash
   sudo xattr -rd com.apple.quarantine "/Applications/Speech to Text.app"
   ```

### Privacy Permissions

The application may request the following permissions:

- **File Access**: To read audio files you select
- **Downloads Folder**: To save transcription results
- **Microphone** (Future): For live transcription features

Grant these permissions when prompted for full functionality.

## Configuration

### Initial Setup

1. **Launch the Application**
   - The app will open with default settings optimized for Korean language

2. **Configure Settings**
   - Click the Settings icon in the top-right corner
   - Adjust language, model size, and output directory as needed
   - Click "Save" to apply changes

3. **Test with Sample File**
   - Drag and drop a small audio file to test the installation
   - Verify the transcription works correctly

### Recommended Settings

For optimal performance:

- **Language**: Select your primary language (Korean/English)
- **Model Size**: 
  - "Base" for balanced speed and accuracy
  - "Large" for maximum accuracy (requires more resources)
- **Output Directory**: Choose a convenient location for saving results

## Troubleshooting

### Common Issues

#### Application Won't Launch
- **Cause**: Security restrictions or corrupted download
- **Solution**: 
  1. Try the security override methods above
  2. Re-download the DMG file
  3. Check system requirements

#### "Command not found" Errors
- **Cause**: Missing Python dependencies
- **Solution**: The app includes all necessary dependencies, but if issues persist:
  ```bash
  # Install Python 3.8+ if not present
  brew install python@3.11
  
  # Install required packages (usually not needed)
  pip3 install openai-whisper
  ```

#### Slow Processing
- **Cause**: Insufficient system resources or large model size
- **Solution**:
  1. Close other applications to free up memory
  2. Use a smaller model size in settings
  3. Process smaller files or shorter audio segments

#### Audio File Not Recognized
- **Cause**: Unsupported file format
- **Solution**: 
  - Supported formats: M4A, WAV, MP3, AAC, FLAC
  - Convert unsupported files using QuickTime Player or other tools

### Getting Help

If you encounter issues not covered here:

1. **Check the FAQ**: [docs/FAQ.md](FAQ.md)
2. **Search Issues**: [GitHub Issues](https://github.com/speechtotext/tauri-gui-app/issues)
3. **Report a Bug**: Create a new issue with:
   - macOS version
   - Application version
   - Steps to reproduce
   - Error messages or screenshots

## Uninstallation

To remove the application:

1. **Remove Application**
   ```bash
   # Move app to Trash
   mv "/Applications/Speech to Text.app" ~/.Trash/
   ```

2. **Remove User Data** (Optional)
   ```bash
   # Remove settings and cache
   rm -rf ~/Library/Application\ Support/com.gnyang.speechtotext.app
   rm -rf ~/Library/Caches/com.gnyang.speechtotext.app
   rm -rf ~/Library/Preferences/com.gnyang.speechtotext.app.plist
   ```

## Updates

### Automatic Updates (Future Feature)
The application will include automatic update checking in future versions.

### Manual Updates
1. Download the latest version from the Releases page
2. Replace the old app in Applications folder
3. Launch the new version

Your settings and preferences will be preserved across updates.

## Advanced Configuration

### Command Line Interface
The application includes a CLI mode for advanced users:

```bash
# Access CLI (if installed via Homebrew in the future)
speech-to-text --help

# Or use the bundled CLI
"/Applications/Speech to Text.app/Contents/Resources/cli" --help
```

### Custom Models
Future versions will support custom Whisper models. Stay tuned for updates.

### Integration with Other Apps
The application registers file associations for audio formats, allowing you to:
- Right-click audio files → "Open with Speech to Text"
- Set as default application for audio files

## Performance Optimization

### For Intel Macs
- Ensure adequate cooling during long processing sessions
- Close unnecessary applications to free up CPU resources
- Consider using smaller model sizes for faster processing

### For Apple Silicon Macs
- Take advantage of the unified memory architecture
- Larger models perform significantly better on M1/M2/M3 chips
- Processing is generally 2-3x faster than Intel equivalents

## Support

For additional support:
- **Documentation**: [docs/](docs/)
- **GitHub Issues**: [Issues Page](https://github.com/speechtotext/tauri-gui-app/issues)
- **Email**: support@speechtotext.app (if available)

---

**Note**: This application is open source and provided as-is. While we strive for reliability, please backup important audio files before processing.