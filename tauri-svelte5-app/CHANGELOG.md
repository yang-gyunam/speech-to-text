# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release preparation
- Comprehensive documentation
- Security policy

### Changed
- Updated project metadata for open source release
- Improved .gitignore for better file exclusion

### Fixed
- DMG background image generation issue

## [0.1.0] - 2024-09-22

### Added
- Initial desktop application for speech-to-text conversion
- Support for multiple audio formats (M4A, WAV, MP3, AAC, FLAC)
- Batch processing capabilities
- Real-time progress tracking
- Native macOS integration with drag & drop
- Dark/light theme support
- Export functionality (TXT, DOCX, PDF)
- Comprehensive test suite
- GitHub Actions CI/CD pipeline
- Detailed documentation

### Features
- **Audio Processing**: Local audio file transcription using AI models
- **User Interface**: Modern Svelte 5 + TypeScript interface
- **Performance**: Multi-threaded processing with Web Workers
- **Accessibility**: Full keyboard navigation and screen reader support
- **Internationalization**: Ready for multiple language support

### Technical
- Built with Tauri 2.0 + Rust backend
- Svelte 5 with TypeScript frontend
- Tailwind CSS for styling
- Comprehensive testing with Vitest
- Security-focused architecture with local processing

### Known Issues
- Large file processing may be slow on older hardware
- Some audio formats may require additional system codecs

---

## Release Notes Format

### Added
- New features

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security improvements