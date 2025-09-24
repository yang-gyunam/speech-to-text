# Frequently Asked Questions (FAQ)

## General Questions

### What is Speech to Text?
Speech to Text is a desktop application that converts audio recordings into text using OpenAI's Whisper AI model. It provides a user-friendly graphical interface for the speech-to-text conversion process.

### What audio formats are supported?
The application supports the following audio formats:
- M4A (iPhone recordings)
- WAV (uncompressed audio)
- MP3 (compressed audio)
- AAC (Advanced Audio Coding)
- FLAC (lossless compression)

### Is my data sent to the cloud?
No, all processing happens locally on your Mac. Your audio files and transcriptions never leave your device, ensuring complete privacy and security.

### How accurate is the transcription?
Accuracy depends on several factors:
- **Audio quality**: Clear recordings with minimal background noise work best
- **Model size**: Larger models (medium, large) provide better accuracy
- **Language**: The system works best with Korean and English
- **Speaker clarity**: Clear pronunciation improves results

Typical accuracy ranges from 85-95% for good quality recordings.

## Installation and Setup

### Why can't I open the app after downloading?
This is due to macOS security features. Follow these steps:
1. Go to System Preferences → Security & Privacy
2. Click "Open Anyway" next to the blocked app message
3. Or right-click the app and select "Open"

### Do I need to install Python or other dependencies?
No, the application includes all necessary dependencies. It's a self-contained app that doesn't require additional installations.

### Can I use this on older Macs?
The minimum requirement is macOS 12.0 (Monterey). Older systems are not supported due to framework requirements.

### How much disk space do I need?
- Application: ~200MB
- Whisper models: 39MB (tiny) to 2.9GB (large)
- Working space: 1-2GB recommended for processing

## Usage Questions

### How long does transcription take?
Processing time varies by:
- **File length**: Roughly 1:4 ratio (1 minute audio = 4 minutes processing)
- **Model size**: Larger models take longer but are more accurate
- **Mac type**: Apple Silicon Macs are 2-3x faster than Intel Macs
- **System load**: Other running applications can slow processing

### Can I process multiple files at once?
Yes! The application supports batch processing:
1. Drag multiple files to the upload area
2. Click "Start Batch Processing"
3. Monitor progress for each file individually

### What's the difference between model sizes?
- **Tiny**: Fastest (39MB), basic accuracy, good for quick drafts
- **Base**: Balanced (142MB), recommended for most users
- **Small**: Better accuracy (488MB), moderate speed
- **Medium**: High accuracy (1.5GB), slower processing
- **Large**: Best accuracy (2.9GB), slowest processing

### Can I edit the transcribed text?
Yes, the application includes a built-in text editor where you can:
- Edit transcriptions directly
- Copy text to clipboard
- Export to various formats (TXT, DOCX, PDF)
- Save changes automatically

### How do I change the language?
1. Click the Settings icon
2. Select your preferred language from the dropdown
3. Click "Save" to apply changes
4. The setting applies to all future transcriptions

## Technical Questions

### Why is processing slow on my Mac?
Several factors can affect speed:
- **Model size**: Try using "Base" instead of "Large"
- **Available memory**: Close other applications
- **File size**: Very large files take proportionally longer
- **Mac age**: Older Intel Macs are significantly slower

### The app uses a lot of memory. Is this normal?
Yes, speech recognition is memory-intensive:
- **Tiny model**: ~1GB RAM
- **Base model**: ~2GB RAM
- **Large model**: ~4-6GB RAM
- Plus additional memory for audio processing

### Can I use custom Whisper models?
Currently, only the standard Whisper models are supported. Custom model support may be added in future versions.

### Does the app work offline?
Yes, completely offline. Once installed, no internet connection is required for transcription.

## File and Export Questions

### Where are my transcriptions saved?
By default, transcriptions are saved to:
- Same folder as the original audio file
- Or the output directory specified in Settings
- Files are named: `[original-name].txt`

### Can I export to Microsoft Word?
Yes, the application supports multiple export formats:
- Plain text (.txt)
- Microsoft Word (.docx)
- PDF documents
- Rich text format (.rtf)
- Markdown (.md)

### What happens to the original audio files?
Original files are never modified or deleted. The application only reads them for processing.

### Can I batch export multiple transcriptions?
Yes, after batch processing:
1. Go to the Results view
2. Select multiple transcriptions
3. Choose "Batch Export" from the menu
4. Select your preferred format and location

## Troubleshooting

### The transcription is mostly incorrect. What's wrong?
Common causes and solutions:
- **Poor audio quality**: Use a better microphone or recording environment
- **Wrong language setting**: Ensure the correct language is selected
- **Background noise**: Try noise reduction before processing
- **Multiple speakers**: The system works best with single speakers

### The app crashes during processing. What should I do?
1. **Check available memory**: Close other applications
2. **Try smaller files**: Break large files into segments
3. **Use smaller model**: Switch from Large to Base model
4. **Restart the app**: Fresh start can resolve memory issues
5. **Report the bug**: Include crash logs and file details

### I can't find my transcription files. Where are they?
Check these locations:
1. Same folder as your original audio file
2. The output directory set in Settings
3. Your Downloads folder (default fallback)
4. Use Spotlight search for `.txt` files

### The app won't recognize my audio file. Why?
Possible reasons:
- **Unsupported format**: Convert to M4A, WAV, MP3, AAC, or FLAC
- **Corrupted file**: Try playing the file in another app first
- **File permissions**: Ensure the file isn't locked or protected
- **File size**: Very large files (>2GB) may not be supported

## Performance and Optimization

### How can I make transcription faster?
1. **Use Apple Silicon Mac**: M1/M2/M3 chips are much faster
2. **Choose smaller model**: Base model is good balance of speed/accuracy
3. **Close other apps**: Free up CPU and memory resources
4. **Process shorter segments**: Break long recordings into parts
5. **Ensure adequate cooling**: Prevent thermal throttling

### Can I process files while doing other work?
Yes, but performance may be affected:
- Processing runs in the background
- You can minimize the app and continue working
- Heavy tasks (video editing, gaming) will slow transcription
- Light tasks (web browsing, documents) have minimal impact

### Should I use the largest model for best results?
Not necessarily:
- **Large model**: Best for critical accuracy needs
- **Base model**: Sufficient for most users (recommended)
- **Small model**: Good compromise for older Macs
- Consider your time vs. accuracy needs

## Future Features

### Will there be mobile versions?
Currently, only macOS is supported. Mobile versions are not planned at this time.

### Can you add support for more languages?
The application supports all languages that Whisper supports (99+ languages). You can select any language in the settings.

### Will there be real-time transcription?
Live transcription features are being considered for future versions.

### Can I suggest new features?
Yes! Please:
1. Check existing feature requests on GitHub
2. Create a new issue with your suggestion
3. Provide detailed use cases and requirements

## Getting Help

### Where can I get more help?
1. **Built-in Help**: Press Cmd+? in the application
2. **User Guide**: Complete documentation in docs/USER_GUIDE.md
3. **GitHub Issues**: Report bugs and request features
4. **Community**: User discussions (future)

### How do I report a bug?
When reporting issues, please include:
1. **macOS version**: System Information → Software
2. **App version**: About menu in the application
3. **Steps to reproduce**: Detailed description
4. **Error messages**: Screenshots or text
5. **Sample files**: If relevant (remove sensitive content)

### Is there email support?
Currently, support is provided through GitHub Issues. Email support may be available in the future.

---

## Still Have Questions?

If your question isn't answered here:
1. Check the [User Guide](USER_GUIDE.md) for detailed instructions
2. Search [GitHub Issues](https://github.com/speechtotext/tauri-gui-app/issues) for similar questions
3. Create a new issue with your question

We're continuously updating this FAQ based on user feedback and common questions.