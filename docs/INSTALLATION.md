# Installation Guide

This guide provides detailed installation instructions for the Speech-to-Text application on macOS.

Important: After initial setup, this application works completely offline. Internet is only required for downloading the initial AI models.

## System Requirements

### Minimum Requirements
- **Operating System**: macOS 10.15 (Catalina) or later
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM (8GB recommended for larger models)
- **Storage**: 5GB free space (for models and temporary files)
- **Internet**: Required only for initial model download (then works offline)

### Recommended Requirements
- **Operating System**: macOS 12 (Monterey) or later
- **Python**: 3.10 or higher
- **Memory**: 8GB RAM or more
- **Storage**: 10GB free space
- **Processor**: Apple Silicon (M1/M2) or Intel with AVX support

## Pre-Installation Setup

### 1. Install Python

#### Option A: Using Homebrew (Recommended)
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Verify installation
python3 --version
```

#### Option B: Using Official Python Installer
1. Download Python from [python.org](https://www.python.org/downloads/macos/)
2. Install the downloaded package
3. Verify installation:
```bash
python3 --version
```

#### Option C: Using pyenv (For Multiple Python Versions)
```bash
# Install pyenv
brew install pyenv

# Install Python 3.11
pyenv install 3.11.0
pyenv global 3.11.0

# Add to shell profile
echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc
```

### 2. Install FFmpeg

FFmpeg is required for audio processing and format conversion.

#### Option A: Using Homebrew (Recommended)
```bash
# Install FFmpeg
brew install ffmpeg

# Verify installation
ffmpeg -version
```

#### Option B: Using MacPorts
```bash
# Install MacPorts first (if not installed)
# Download from: https://www.macports.org/install.php

# Install FFmpeg
sudo port install ffmpeg

# Verify installation
ffmpeg -version
```

#### Option C: Manual Installation
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract and add to PATH
3. Verify installation

### 3. Install Git (Optional)
If you plan to install from source:
```bash
# Using Homebrew
brew install git

# Or download from: https://git-scm.com/download/mac
```

## Installation Methods

### Method 1: Quick Setup Script (Recommended)

This is the fastest way to get started:

```bash
# Clone the repository
git clone <repository-url>
cd speech-to-text

# Run the setup script
./setup_env.sh

# Activate the virtual environment
source venv/bin/activate

# Verify installation
speech-to-text --help
```

The setup script will:
- Create a Python virtual environment
- Install all dependencies
- Set up the package in development mode
- Download the base Whisper model

### Method 2: Manual Installation

#### Step 1: Clone Repository
```bash
git clone <repository-url>
cd speech-to-text
```

#### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

#### Step 3: Install Dependencies
```bash
# Install all dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

#### Step 4: Verify Installation
```bash
# Check if command is available
speech-to-text --help

# Run system check
speech-to-text doctor
```

### Method 3: Using Makefile

If you prefer using make commands:

```bash
# Clone repository
git clone <repository-url>
cd speech-to-text

# Setup everything
make setup

# Activate virtual environment
source venv/bin/activate

# Verify installation
make test
```

Available make commands:
- `make setup` - Complete setup including virtual environment
- `make install` - Install dependencies only
- `make test` - Run test suite
- `make clean` - Clean build artifacts
- `make format` - Format code
- `make lint` - Check code style

### Method 4: System-wide Installation (Not Recommended)

**Warning**: System-wide installation can cause conflicts with other Python packages.

```bash
# Install directly to system Python
pip3 install -r requirements.txt
pip3 install .

# Or install from source
python3 setup.py install
```

## Post-Installation Setup

### 1. Download Whisper Models

Models are downloaded automatically on first use, but you can pre-download them:

```bash
# Download base model (recommended)
python -c "import whisper; whisper.load_model('base')"

# Download other models if needed
python -c "import whisper; whisper.load_model('tiny')"
python -c "import whisper; whisper.load_model('small')"
python -c "import whisper; whisper.load_model('medium')"
python -c "import whisper; whisper.load_model('large')"
```

Model sizes and download times:
- `tiny`: ~39MB (fastest download)
- `base`: ~74MB (recommended)
- `small`: ~244MB
- `medium`: ~769MB
- `large`: ~1550MB (slowest download)

### 2. Create Configuration File

```bash
# Create default configuration
speech-to-text init-config

# Or create custom configuration
cat > speech-to-text.json << EOF
{
  "language": "ko",
  "model_size": "base",
  "output_dir": "./transcripts",
  "include_metadata": true,
  "quiet": false
}
EOF
```

### 3. Set Up Environment Variables (Optional)

Add to your shell profile (`~/.zshrc` or `~/.bash_profile`):

```bash
# Speech-to-Text default settings
export SPEECH_TO_TEXT_LANGUAGE=ko
export SPEECH_TO_TEXT_MODEL_SIZE=base
export SPEECH_TO_TEXT_OUTPUT_DIR=./transcripts

# Add to PATH if needed
export PATH="$HOME/.local/bin:$PATH"
```

Reload your shell:
```bash
source ~/.zshrc
```

## Verification

### 1. System Check
```bash
speech-to-text doctor
```

Expected output:
```
Speech-to-Text System Check
========================================
✓ Python version: 3.11.0
✓ OpenAI Whisper: Available
✓ pydub: Available
✓ PyYAML: Available
✓ FFmpeg: Available
✓ Configuration: Valid
✓ Output directory: Writable
```

### 2. Test with Sample File

Create a test audio file or use an existing one:

```bash
# Test with a small file
speech-to-text --model-size tiny test-recording.m4a

# Check supported formats
speech-to-text formats

# Get file information
speech-to-text info test-recording.m4a
```

### 3. Run Test Suite

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=speech_to_text

# Run specific test
pytest tests/test_transcriber.py -v
```

## Troubleshooting Installation

### Common Issues

#### 1. Python Version Error
```bash
# Check Python version
python3 --version

# If too old, install newer version
brew install python@3.11
```

#### 2. Permission Errors
```bash
# Fix permissions for pip
pip install --user -r requirements.txt

# Or use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. FFmpeg Not Found
```bash
# Install FFmpeg
brew install ffmpeg

# Add to PATH if needed
export PATH="/usr/local/bin:$PATH"
```

#### 4. Whisper Installation Fails
```bash
# Clear pip cache
pip cache purge

# Install with no cache
pip install --no-cache-dir openai-whisper

# For Apple Silicon Macs
pip install openai-whisper --no-deps
pip install torch torchvision torchaudio
```

#### 5. Virtual Environment Issues
```bash
# Remove and recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Getting Help

If you encounter issues:

1. Run the system check: `speech-to-text doctor`
2. Check the troubleshooting guide: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. Look at the logs in the `logs/` directory
4. Create an issue with your system information

## Updating

### Update from Git Repository
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Reinstall package
pip install -e .
```

### Update Dependencies Only
```bash
# Update all packages
pip install -r requirements.txt --upgrade

# Update specific package
pip install --upgrade openai-whisper
```

## Uninstallation

### Remove Virtual Environment Installation
```bash
# Deactivate virtual environment
deactivate

# Remove project directory
rm -rf /path/to/speech-to-text
```

### Remove System Installation
```bash
# Uninstall package
pip uninstall speech-to-text

# Remove dependencies (optional)
pip uninstall openai-whisper pydub click pyyaml ffmpeg-python

# Remove models (optional)
rm -rf ~/.cache/whisper
```

### Clean Up Configuration
```bash
# Remove configuration files
rm -f speech-to-text.json
rm -f ~/.speech-to-text.json

# Remove environment variables from shell profile
# Edit ~/.zshrc and remove SPEECH_TO_TEXT_* variables
```

## Development Installation

For developers who want to contribute:

```bash
# Clone with development setup
git clone <repository-url>
cd speech-to-text

# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Install additional development tools
pip install black flake8 mypy pytest-cov

# Set up pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

## Docker Installation (Alternative)

If you prefer using Docker:

```bash
# Build Docker image
docker build -t speech-to-text .

# Run with Docker
docker run -v $(pwd)/recordings:/app/recordings -v $(pwd)/output:/app/output speech-to-text recording.m4a
```

Note: Docker setup is not officially supported but may work for some use cases.

## Next Steps

After successful installation:

1. Read the [README.md](README.md) for basic usage
2. Check [EXAMPLES.md](EXAMPLES.md) for detailed examples
3. Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
4. Test with your own audio files
5. Create configuration files for your common use cases

## Support

- **Documentation**: Check all `.md` files in the project
- **System Check**: Run `speech-to-text doctor`
- **Examples**: Run `speech-to-text examples`
- **Issues**: Create an issue on the project repository
- **Discussions**: Use the project's discussion forum