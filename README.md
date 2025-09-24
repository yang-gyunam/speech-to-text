# Speech-to-Text CLI Application

A command-line application for audio transcription using OpenAI Whisper, with an optional desktop UI built with Tauri and Svelte. All processing is done locally on your machine - no internet connection required after initial setup.

![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Tauri](https://img.shields.io/badge/Tauri-2.0-orange)
![Svelte](https://img.shields.io/badge/Svelte-5.0-red)

## Features

- High-Quality Transcription: Powered by OpenAI Whisper for accurate speech recognition
- Multi-Language Support: Supports Korean, English, and other languages
- Batch Processing: Process multiple audio files simultaneously
- Real-time Progress: Live progress tracking with percentage and time estimates
- Cross-Platform: Native desktop app for Windows, macOS, and Linux
- Modern UI: Clean, intuitive interface built with Svelte 5
- Fast Performance: Rust backend for optimal performance
- Multiple Formats: Support for M4A, WAV, MP3, AAC, FLAC audio files
- Auto-Save: Automatic file naming with timestamps
- Dark Mode: System theme support
- Cancellable: Cancel processing at any time
- Offline Operation: All processing happens locally - no internet required after initial setup

## Quick Start

### For End Users (Easy Installation)

Download the installer for your platform:

#### macOS
1. Download the DMG file from the releases page
2. Open the DMG file by double-clicking
3. Drag the app to your Applications folder
4. Launch the app from Applications or Launchpad
5. First run: macOS might ask for permission - click "Open" when prompted

#### Windows (Coming Soon)
- Windows installer will be available in future releases

No technical knowledge required! The app works completely offline after installation.

---

### For Developers (Source Installation)

#### Prerequisites

- Python 3.8+ with pip
- FFmpeg (for audio processing)
- Node.js 18+ with npm (only for desktop UI)
- Rust (only for desktop UI)
- Internet connection (only for initial model download - after setup, works completely offline)

#### Installation

1. Clone the repository
   ```bash
   git clone <repository-url>
   cd speech-to-text
   ```

2. Set up Python environment
   ```bash
   # Run the setup script (recommended)
   ./scripts/setup_env.sh

   # Or manually:
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Test the CLI
   ```bash
   speech-to-text --help
   ```

#### Running the CLI Application

Basic Usage:
```bash
# Transcribe a single file
speech-to-text recording.m4a

# Batch process files
speech-to-text --batch ./recordings/

# Use different model size
speech-to-text --model-size large recording.m4a
```

#### Desktop UI Development

To run the desktop interface in development mode:

```bash
cd tauri-svelte5-app
npm install
npm run tauri:dev
```

## Usage

CLI Usage:

```bash
# Basic transcription
speech-to-text recording.m4a

# Batch processing
speech-to-text --batch ./recordings/

# With options
speech-to-text --language en --model-size large --output-dir ./transcripts recording.wav

# Get help
speech-to-text --help
speech-to-text examples
speech-to-text doctor  # System check
```

Desktop UI Usage:

1. Launch the Application - Start the desktop app
2. Select Audio File - Choose audio files (`.m4a`, `.wav`, `.mp3`, `.aac`, `.flac`)
3. Choose Model Size - Select accuracy vs speed trade-off
4. Start Transcription - Monitor real-time progress
5. View Results - Text appears with auto-save

## Architecture

```
├── src/                          # Python CLI for Whisper processing
│   ├── speech_to_text/          # Core transcription logic
│   └── requirements.txt         # Python dependencies
├── tauri-svelte5-app/           # Tauri desktop application
│   ├── src/                     # Svelte frontend
│   ├── src-tauri/               # Rust backend
│   └── package.json             # Node.js dependencies
└── LICENSE                      # Apache 2.0 License
```

### Technology Stack

- Frontend: Svelte 5, TypeScript, Tailwind CSS
- Backend: Rust with Tauri framework
- AI Engine: OpenAI Whisper
- Audio Processing: FFmpeg, PyDub
- Build System: Vite, Cargo

## Configuration

### Model Sizes

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| Base  | 74MB | Fast  | Good     |
| Small | 244MB| Medium| Better   |
| Medium| 769MB| Slow  | Great    |
| Large | 1550MB| Slowest| Best   |

### Output Settings

- Files are saved next to the original audio file
- Naming pattern: `{original_name}_transcription_{timestamp}.txt`
- Example: `interview_transcription_202409221530.txt`

## Supported Audio Formats

- .m4a - iPhone default recording format
- .wav - Uncompressed audio
- .mp3 - Compressed audio
- .aac - Advanced Audio Coding
- .flac - Lossless compression

## Output

### Text Files
Transcribed text is saved as `.txt` files in the output directory with the same name as the input file.

### Metadata (Optional)
When `--include-metadata` is used, additional information is included:
- Original filename
- Processing time
- Confidence score
- Language detected
- Model used
- Timestamp

### Batch Processing Summary
For batch operations, a summary report is generated showing:
- Total files processed
- Success/failure counts
- Processing time
- List of failed files (if any)

## Documentation

### Core Documentation
- [Installation Guide](docs/INSTALLATION_GUIDE.md) - Detailed setup instructions for all platforms
- [Build Instructions](docs/BUILD_INSTRUCTIONS.md) - Building from source
- [Usage Examples](docs/EXAMPLES.md) - Comprehensive CLI usage examples and scenarios
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Changelog](docs/CHANGELOG.md) - Version history and updates

### Desktop UI Documentation
- [User Guide](tauri-svelte5-app/docs/USER_GUIDE.md) - Desktop application user manual
- [Architecture](tauri-svelte5-app/docs/ARCHITECTURE.md) - Technical architecture overview
- [API Reference](tauri-svelte5-app/docs/API.md) - API documentation
- [Features](tauri-svelte5-app/docs/FEATURES.md) - Feature overview and roadmap
- [Quick Start](tauri-svelte5-app/docs/QUICK_START.md) - Fast setup for desktop UI
- [Building](tauri-svelte5-app/docs/BUILDING.md) - Build instructions
- [Contributing](tauri-svelte5-app/docs/CONTRIBUTING.md) - Contribution guidelines
- [FAQ](tauri-svelte5-app/docs/FAQ.md) - Frequently asked questions

### Testing Documentation
- [Manual Test Scenarios](tauri-svelte5-app/docs/testing/manual-test-scenarios.md)
- [Performance Testing](tauri-svelte5-app/docs/testing/performance-testing-guide.md)
- [Accessibility Testing](tauri-svelte5-app/docs/testing/accessibility-testing-guide.md)
- [User Acceptance Testing](tauri-svelte5-app/docs/testing/user-acceptance-testing-guide.md)

### Quick Help

```bash
# Show help for main command
speech-to-text --help

# Show detailed examples
speech-to-text examples

# Check system status
speech-to-text doctor

# Get file info
speech-to-text info your-file.m4a
```

## Development

### Project Structure

```
tauri-svelte5-app/
├── src/                         # Svelte frontend
│   ├── components/             # UI components
│   ├── services/               # API services
│   ├── store/                  # State management
│   └── utils/                  # Utilities
├── src-tauri/                  # Rust backend
│   ├── src/
│   │   ├── cli.rs             # CLI integration
│   │   ├── models.rs          # Data models
│   │   └── utils.rs           # Helper functions
│   └── Cargo.toml             # Rust dependencies
└── package.json               # Frontend dependencies
```

### Available Scripts

```bash
# Development
npm run tauri:dev              # Start development server
npm run dev                    # Frontend only development

# Building
npm run tauri:build           # Build production app
npm run build                 # Build frontend only

# Testing
npm run test                  # Run tests
npm run test:coverage         # Run tests with coverage

# Code Quality
npm run lint                  # Lint code
npm run format               # Format code
npm run type-check           # Type checking
```

### Adding Features

1. Frontend: Add Svelte components in `src/components/`
2. Backend: Implement Rust functions in `src-tauri/src/`
3. CLI: Extend Python CLI in `src/speech_to_text/`

## Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Code Style

- TypeScript: Use ESLint and Prettier configurations
- Rust: Follow `rustfmt` standards
- Python: Follow PEP 8 guidelines

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI Whisper for the excellent speech recognition model
- Tauri Team for the amazing cross-platform framework
- Svelte Team for the reactive UI framework
- Rust Community for the powerful systems programming language

---

Built with Tauri, Svelte, and Rust