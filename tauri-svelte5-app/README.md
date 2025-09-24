# Speech to Text

A modern desktop application for converting audio files to text using OpenAI's Whisper model. Built with Tauri, Svelte 5, and TypeScript.

## Features

- **Multiple Audio Formats**: M4A, WAV, MP3, AAC, FLAC support
- **Batch Processing**: Process multiple files simultaneously
- **High Accuracy**: Powered by OpenAI's Whisper model
- **Real-time Progress**: Live progress tracking with time estimates
- **Native macOS Integration**: Drag & drop, dark/light theme support

## Installation

### System Requirements
- macOS 12.0 (Monterey) or later
- 4GB RAM minimum, 8GB recommended
- Intel x64 or Apple Silicon (M1/M2/M3)

### Download and Install
1. Download the latest DMG from [Releases](https://github.com/speechtotext/tauri-gui-app/releases)
2. Open the DMG file and drag "Speech to Text" to Applications
3. Launch from Applications

## Quick Start

1. Launch the application
2. Drag audio files to the upload area
3. Click "Start Processing"
4. Review and export your transcribed text

## Development

### Prerequisites
- Node.js 18.0.0+
- Rust (latest stable)
- Xcode Command Line Tools

### Setup
```bash
git clone https://github.com/speechtotext/tauri-gui-app.git
cd tauri-gui-app
npm install
npm run tauri:dev
```

### Build
```bash
npm run tauri:build
```

## Architecture

- **Frontend**: Svelte 5 + TypeScript + Tailwind CSS
- **Backend**: Rust + Tauri
- **State Management**: Svelte runes

## Troubleshooting

### App Won't Start
- If you see a security warning: Go to System Preferences → Security & Privacy → Click "Open Anyway"
- Or run: `sudo xattr -rd com.apple.quarantine "/Applications/Speech to Text.app"`

### Processing Issues
- **Stuck at 0%**: Cancel (Cmd+.) and try a smaller file first
- **Poor quality**: Ensure clear audio with minimal background noise
- **Slow processing**: Close other apps, use smaller model size

### FAQ

**Q: Is my data sent to the cloud?**
A: No, all processing happens locally on your device.

**Q: What audio formats are supported?**
A: M4A, WAV, MP3, AAC, and FLAC files.

**Q: How accurate is the transcription?**
A: Very high accuracy with clear audio. Quality depends on audio clarity and language.

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.
