# Features Documentation

Complete reference for all Speech to Text application features and capabilities.

## Core Features

### Audio File Processing

#### Supported Formats
- **M4A**: iPhone voice memos, high quality
- **WAV**: Uncompressed audio, best quality
- **MP3**: Compressed audio, widely compatible
- **AAC**: Advanced Audio Coding, efficient compression
- **FLAC**: Lossless compression, audiophile quality

#### File Size Limits
- **Maximum file size**: 2GB per file
- **Recommended size**: Under 500MB for optimal performance
- **Batch processing**: Up to 50 files simultaneously
- **Total batch size**: Limited by available disk space

#### Audio Quality Requirements
- **Sample rate**: 8kHz to 48kHz (16kHz+ recommended)
- **Bit depth**: 16-bit or 24-bit
- **Channels**: Mono or stereo (mono preferred for speech)
- **Duration**: No strict limit, but longer files take proportionally more time

### Whisper AI Models

#### Model Comparison
| Model  | Size   | Speed | Accuracy | Use Case |
|--------|--------|-------|----------|----------|
| Tiny   | 39MB   | Very Fast | Basic | Quick drafts, testing |
| Base   | 142MB  | Fast | Good | General use (recommended) |
| Small  | 488MB  | Medium | Better | Better accuracy needs |
| Medium | 1.5GB  | Slow | High | High accuracy requirements |
| Large  | 2.9GB  | Very Slow | Excellent | Maximum accuracy |

#### Model Selection Guidelines
- **Tiny**: Testing, very fast turnaround needed
- **Base**: Most users, balanced performance
- **Small**: When accuracy matters more than speed
- **Medium**: Professional transcription needs
- **Large**: Critical accuracy, time not a factor

### Language Support

#### Primary Languages (Optimized)
- **Korean (한국어)**: Native optimization, best accuracy
- **English**: Full feature support, excellent accuracy
- **Japanese (日本語)**: Good support for similar phonetics
- **Chinese (中文)**: Mandarin and Cantonese variants

#### Additional Languages (99+ Supported)
The application supports all languages that OpenAI Whisper supports, including:
- European languages (Spanish, French, German, Italian, etc.)
- Asian languages (Thai, Vietnamese, Hindi, etc.)
- Middle Eastern languages (Arabic, Hebrew, Persian, etc.)
- African languages (Swahili, Yoruba, etc.)

#### Language Detection
- **Auto-detect**: Automatically identifies the primary language
- **Manual selection**: Override for better accuracy
- **Mixed language**: Handles code-switching reasonably well
- **Confidence scoring**: Indicates detection certainty

## User Interface Features

### Main Interface

#### Upload View
- **Drag and Drop Zone**: Primary file input method
- **File Browser**: Traditional file selection dialog
- **Format Validation**: Real-time format checking
- **File Preview**: Shows file information before processing
- **Batch Selection**: Multi-file selection and management

#### Processing View
- **Real-time Progress**: Live progress bar updates
- **Stage Indicators**: Shows current processing phase
- **Time Estimation**: Remaining time calculations
- **Processing Log**: Detailed status messages
- **Cancel Function**: Stop processing at any time

#### Results View
- **Text Editor**: Built-in editor with syntax highlighting
- **Metadata Panel**: Processing statistics and file information
- **Export Options**: Multiple format export capabilities
- **Sharing Tools**: Quick sharing and copying functions

### Navigation and Controls

#### Keyboard Shortcuts
| Action | Shortcut | Description |
|--------|----------|-------------|
| Open Files | `Cmd+O` | Open file selection dialog |
| Start Processing | `Cmd+R` | Begin transcription |
| Cancel Processing | `Cmd+.` | Stop current processing |
| Save Results | `Cmd+S` | Save transcription |
| Export | `Cmd+E` | Export to chosen format |
| Settings | `Cmd+,` | Open settings panel |
| Help | `Cmd+?` | Show help documentation |
| New Session | `Cmd+N` | Start new transcription |
| Copy Text | `Cmd+C` | Copy transcribed text |
| Select All | `Cmd+A` | Select all text |
| Find | `Cmd+F` | Search within text |

#### Mouse and Trackpad
- **Drag and Drop**: Primary file input method
- **Right-click Menus**: Context-sensitive options
- **Scroll Gestures**: Navigate through long transcriptions
- **Pinch to Zoom**: Adjust text size (future feature)

### Accessibility Features

#### Screen Reader Support
- **VoiceOver Compatible**: Full navigation with VoiceOver
- **Descriptive Labels**: All UI elements properly labeled
- **Keyboard Navigation**: Complete keyboard-only operation
- **Focus Indicators**: Clear visual focus indicators

#### Visual Accessibility
- **High Contrast Mode**: Enhanced visibility options
- **Large Text Support**: Respects system text size settings
- **Color Blind Friendly**: Accessible color schemes
- **Reduced Motion**: Respects motion sensitivity settings

#### Motor Accessibility
- **Large Click Targets**: Minimum 44pt touch targets
- **Keyboard Alternatives**: All mouse actions have keyboard equivalents
- **Sticky Keys Support**: Compatible with accessibility tools
- **Voice Control**: Works with macOS Voice Control

## Settings and Configuration

### Processing Settings

#### Language Configuration
- **Primary Language**: Main language for transcription
- **Secondary Language**: Fallback for mixed content
- **Auto-detection**: Enable/disable automatic language detection
- **Language Confidence**: Minimum confidence threshold

#### Model Configuration
- **Default Model**: Model used for new transcriptions
- **Auto-download**: Automatically download required models
- **Model Storage**: Location for storing Whisper models
- **Model Updates**: Check for model updates

#### Performance Settings
- **Concurrent Jobs**: Number of simultaneous processing tasks
- **Memory Limit**: Maximum RAM usage for processing
- **CPU Priority**: Processing priority level
- **Background Processing**: Continue when app is minimized

### Output Settings

#### File Naming
- **Naming Pattern**: Template for output file names
- **Date Stamps**: Include processing date/time
- **Original Names**: Preserve source file names
- **Custom Prefix/Suffix**: Add consistent naming elements
- **Conflict Resolution**: How to handle duplicate names

#### Export Formats
- **Default Format**: Primary export format
- **Quality Settings**: Compression and quality options
- **Metadata Inclusion**: Include processing metadata
- **Batch Export**: Settings for bulk export operations

#### Storage Locations
- **Output Directory**: Default save location
- **Backup Directory**: Automatic backup location
- **Temporary Files**: Processing cache location
- **Model Storage**: Whisper model storage location

### Interface Settings

#### Appearance
- **Theme**: Light, Dark, or System
- **Accent Color**: Primary interface color
- **Font Size**: Text display size
- **Window Behavior**: Default window size and position

#### Behavior
- **Auto-start Processing**: Begin immediately after file selection
- **Confirmation Dialogs**: Show/hide confirmation prompts
- **Progress Notifications**: System notification settings
- **Sound Effects**: Audio feedback for operations

## Export and Sharing Features

### Export Formats

#### Text Formats
- **Plain Text (.txt)**
  - Simple, universal format
  - Preserves line breaks and basic formatting
  - Smallest file size
  - Compatible with all text editors

- **Rich Text Format (.rtf)**
  - Preserves formatting and styling
  - Compatible with most word processors
  - Moderate file size
  - Maintains text appearance

- **Markdown (.md)**
  - Structured text format
  - Great for documentation
  - Version control friendly
  - Web-compatible

#### Document Formats
- **Microsoft Word (.docx)**
  - Professional document format
  - Full formatting support
  - Widely accepted standard
  - Collaborative editing support

- **PDF Document (.pdf)**
  - Universal viewing format
  - Preserves exact layout
  - Print-ready format
  - Security and protection options

- **HTML (.html)**
  - Web-compatible format
  - Hyperlink support
  - Embeddable in websites
  - Responsive design options

#### Structured Data Formats
- **JSON (.json)**
  - Machine-readable format
  - Includes metadata and timestamps
  - Developer-friendly
  - API integration ready

- **CSV (.csv)**
  - Spreadsheet compatible
  - Tabular data format
  - Easy data analysis
  - Database import ready

- **XML (.xml)**
  - Structured markup format
  - Schema validation support
  - Enterprise integration
  - Transformation capabilities

### Sharing Options

#### Quick Actions
- **Copy to Clipboard**: Instant text copying
- **Share Menu**: Native macOS sharing
- **Email Integration**: Send via Mail app
- **Messages**: Share via Messages app
- **AirDrop**: Wireless sharing to nearby devices

#### File Management
- **Reveal in Finder**: Locate files quickly
- **Open With**: Choose specific applications
- **Quick Look**: Preview without opening
- **Spotlight Integration**: Search transcription content

#### Cloud Integration (Future)
- **iCloud Drive**: Automatic cloud sync
- **Dropbox**: Direct upload capability
- **Google Drive**: Cloud storage integration
- **OneDrive**: Microsoft cloud integration

## Batch Processing Features

### Batch Operations

#### File Management
- **Multi-select**: Choose multiple files at once
- **Drag and Drop**: Add multiple files simultaneously
- **File Ordering**: Reorder processing queue
- **Remove Files**: Remove files from batch before processing

#### Processing Control
- **Batch Start**: Process all files with one click
- **Individual Progress**: Track each file separately
- **Pause/Resume**: Control batch processing flow
- **Priority Queue**: Reorder files during processing

#### Results Management
- **Batch Results**: View all transcriptions together
- **Individual Access**: Open specific transcriptions
- **Bulk Export**: Export all results at once
- **Summary Statistics**: Processing time and accuracy metrics

### Queue Management

#### Processing Queue
- **FIFO Processing**: First-in, first-out by default
- **Priority Levels**: High, normal, low priority
- **Queue Reordering**: Drag to reorder queue
- **Queue Persistence**: Maintains queue across app restarts

#### Resource Management
- **Concurrent Limits**: Control simultaneous processing
- **Memory Monitoring**: Prevent system overload
- **Thermal Management**: Prevent overheating
- **Background Processing**: Continue when minimized

## Advanced Features

### Processing Profiles

#### Custom Profiles
- **Profile Creation**: Save custom setting combinations
- **Profile Switching**: Quick setting changes
- **Profile Sharing**: Export/import profiles
- **Default Profiles**: Pre-configured optimal settings

#### Profile Settings
- **Language Combinations**: Multi-language profiles
- **Model Preferences**: Different models for different content
- **Output Preferences**: Format and location settings
- **Processing Options**: Speed vs. quality preferences

### History and Tracking

#### Processing History
- **Recent Files**: Quick access to recent transcriptions
- **Processing Log**: Detailed processing history
- **Statistics Tracking**: Usage and performance metrics
- **Search History**: Find previous transcriptions

#### File Tracking
- **Source Tracking**: Link transcriptions to original files
- **Version History**: Track edits and changes
- **Backup Management**: Automatic backup creation
- **Recovery Options**: Restore from backups

### Integration Features

#### System Integration
- **File Associations**: Set as default for audio files
- **Context Menus**: Right-click integration in Finder
- **Quick Actions**: Finder Quick Actions support
- **Spotlight Integration**: Search transcription content

#### Workflow Integration
- **Automator Support**: Create custom workflows
- **AppleScript**: Scriptable automation
- **URL Schemes**: Deep linking support
- **CLI Integration**: Command-line interface access

## Privacy and Security Features

### Data Protection

#### Local Processing
- **No Cloud Dependency**: All processing happens locally
- **No Data Transmission**: Files never leave your device
- **Offline Operation**: Works without internet connection
- **Privacy by Design**: Built-in privacy protection

#### File Security
- **Secure Temporary Files**: Encrypted temporary storage
- **Automatic Cleanup**: Removes temporary files after processing
- **Permission Management**: Minimal required permissions
- **Sandboxed Operation**: Isolated from system files

### User Control

#### Data Management
- **Data Retention**: Control how long data is kept
- **Manual Cleanup**: Clear caches and temporary files
- **Export Control**: Choose what data to export
- **Deletion Confirmation**: Confirm before deleting data

#### Privacy Settings
- **Analytics Opt-out**: Disable usage analytics
- **Crash Reporting**: Control crash report submission
- **Update Checking**: Control automatic update checks
- **Telemetry Control**: Disable all telemetry

## Performance and Monitoring

### Performance Metrics

#### Processing Statistics
- **Processing Speed**: Words per minute transcribed
- **Accuracy Estimates**: Confidence scoring
- **Resource Usage**: CPU, memory, and disk usage
- **Thermal Monitoring**: Temperature tracking

#### System Monitoring
- **Memory Usage**: Real-time memory consumption
- **CPU Utilization**: Processing load monitoring
- **Disk I/O**: Read/write performance
- **Network Usage**: Minimal (updates only)

### Optimization Features

#### Automatic Optimization
- **Model Selection**: Suggest optimal model for hardware
- **Resource Management**: Automatic resource allocation
- **Thermal Throttling**: Prevent overheating
- **Memory Management**: Efficient memory usage

#### Manual Optimization
- **Performance Profiles**: Speed vs. quality presets
- **Resource Limits**: Set maximum resource usage
- **Processing Scheduling**: Schedule processing for off-hours
- **Cache Management**: Control cache size and location

## Future Features (Roadmap)

### Planned Features
- **Real-time Transcription**: Live audio transcription
- **Speaker Diarization**: Identify different speakers
- **Custom Vocabulary**: Add specialized terms
- **Cloud Sync**: Optional cloud synchronization
- **Mobile Companion**: iOS app integration
- **API Access**: Developer API for integration

### Under Consideration
- **Video File Support**: Extract audio from video
- **Translation Features**: Translate transcriptions
- **Voice Commands**: Control app with voice
- **Collaboration Tools**: Share and collaborate on transcriptions
- **Advanced Editing**: Rich text editing features
- **Plugin System**: Third-party extensions

---

This features documentation is continuously updated as new capabilities are added to the application. For the latest feature information, check the release notes and changelog.