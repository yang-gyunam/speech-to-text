# Deployment Guide

This guide explains how to deploy and distribute the Speech-to-Text application.

Important: This is an offline application - users only need internet for initial model download during setup.

## Distribution Files

The build process creates several distribution formats:

### Python Package Distribution
- **Wheel**: `speech_to_text-0.1.0-py3-none-any.whl` - Binary distribution for pip
- **Source**: `speech_to_text-0.1.0.tar.gz` - Source distribution for pip

### Release Package
- **Complete Release**: `speech-to-text-0.1.0-release.tar.gz` - Complete package with documentation and installer
- **ZIP Release**: `speech-to-text-0.1.0-release.zip` - Same as above in ZIP format

## Building for Distribution

### Quick Build
```bash
# Build distribution packages
make dist

# Build complete release package
make release
```

### Manual Build Process
```bash
# 1. Clean previous builds
make clean

# 2. Install build dependencies
make build-deps

# 3. Build distributions
make build

# 4. Verify distributions
make verify-dist

# 5. Test installation
make test-install

# 6. Create release package
./build_dist.sh
```

## Installation Methods

### Method 1: From Wheel (Recommended for Users)
```bash
# Install from wheel
pip install speech_to_text-0.1.0-py3-none-any.whl

# Or install with dependencies
pip install speech_to_text-0.1.0-py3-none-any.whl[dev]
```

### Method 2: From Source Distribution
```bash
# Install from source
pip install speech_to_text-0.1.0.tar.gz
```

### Method 3: Using Installation Script
```bash
# Extract release package
tar -xzf speech-to-text-0.1.0-release.tar.gz
cd speech-to-text-0.1.0-release

# Run installer
./install.sh
```

### Method 4: From PyPI (When Published)
```bash
# Install from PyPI
pip install speech-to-text

# Install with development dependencies
pip install speech-to-text[dev]
```

## Publishing to PyPI

### Prerequisites
1. Create accounts on [PyPI](https://pypi.org) and [Test PyPI](https://test.pypi.org)
2. Configure authentication:
```bash
# Configure PyPI credentials
pip install keyring
keyring set https://upload.pypi.org/legacy/ __token__
# Enter your PyPI API token

# Configure Test PyPI credentials
keyring set https://test.pypi.org/legacy/ __token__
# Enter your Test PyPI API token
```

### Publishing Process

#### 1. Test on Test PyPI First
```bash
# Upload to Test PyPI
make upload-test

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ speech-to-text
```

#### 2. Publish to Production PyPI
```bash
# Upload to PyPI
make upload

# Verify installation
pip install speech-to-text
```

## GitHub Release

### Creating a Release

1. **Tag the Release**:
```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

2. **Create GitHub Release**:
   - Go to GitHub repository
   - Click "Releases" → "Create a new release"
   - Select tag `v0.1.0`
   - Upload release files:
     - `speech-to-text-0.1.0-release.tar.gz`
     - `speech-to-text-0.1.0-release.zip`
     - `speech_to_text-0.1.0-py3-none-any.whl`
     - `speech_to_text-0.1.0.tar.gz`

3. **Release Notes Template**:
```markdown
# Speech-to-Text v0.1.0

## Initial Release

This is the first stable release of Speech-to-Text, a macOS application for converting iPhone audio recordings to text using OpenAI Whisper.

### Features
- Support for multiple audio formats (.m4a, .wav, .mp3, .aac, .flac)
- Korean language optimization
- Batch processing capabilities
- Multiple Whisper model sizes
- Configuration file support
- Comprehensive CLI interface

### Installation

**Quick Install:**
```bash
pip install speech-to-text
```

**From Release Package:**
1. Download `speech-to-text-0.1.0-release.tar.gz`
2. Extract and run `./install.sh`

### 📚 Documentation
- [Installation Guide](INSTALLATION.md)
- [Usage Examples](EXAMPLES.md)
- [Troubleshooting](TROUBLESHOOTING.md)

### System Requirements
- macOS 10.15+
- Python 3.8+
- FFmpeg

### Files in this Release
- `speech_to_text-0.1.0-py3-none-any.whl` - Python wheel package
- `speech_to_text-0.1.0.tar.gz` - Python source distribution
- `speech-to-text-0.1.0-release.tar.gz` - Complete release with docs and installer
- `speech-to-text-0.1.0-release.zip` - Same as above in ZIP format
```

## Docker Deployment (Optional)

### Creating Docker Image
```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install package
COPY dist/speech_to_text-0.1.0-py3-none-any.whl .
RUN pip install speech_to_text-0.1.0-py3-none-any.whl

# Create volume for audio files
VOLUME ["/audio", "/output"]

# Set entrypoint
ENTRYPOINT ["speech-to-text"]
CMD ["--help"]
EOF

# Build image
docker build -t speech-to-text:0.1.0 .

# Tag for registry
docker tag speech-to-text:0.1.0 your-registry/speech-to-text:0.1.0
```

### Using Docker Image
```bash
# Run with audio files
docker run -v $(pwd)/audio:/audio -v $(pwd)/output:/output \
  speech-to-text:0.1.0 --batch /audio --output-dir /output
```

## Homebrew Formula (macOS)

### Creating Homebrew Formula
```ruby
# speech-to-text.rb
class SpeechToText < Formula
  desc "Convert iPhone audio recordings to text using OpenAI Whisper"
  homepage "https://github.com/example/speech-to-text"
  url "https://github.com/example/speech-to-text/archive/v0.1.0.tar.gz"
  sha256 "your-sha256-hash"
  license "MIT"

  depends_on "python@3.11"
  depends_on "ffmpeg"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/speech-to-text", "--help"
  end
end
```

## Distribution Checklist

### Pre-Release
- [ ] All tests pass (`make test`)
- [ ] Code quality checks pass (`make check`)
- [ ] Documentation is up to date
- [ ] Version numbers are updated
- [ ] CHANGELOG.md is updated

### Build Process
- [ ] Clean build environment (`make clean`)
- [ ] Build distributions (`make build`)
- [ ] Verify distributions (`make verify-dist`)
- [ ] Test installation (`make test-install`)
- [ ] Create release package (`make release`)

### Testing
- [ ] Test wheel installation in clean environment
- [ ] Test source installation
- [ ] Test installation script
- [ ] Verify all dependencies are included
- [ ] Test on clean macOS system

### Publishing
- [ ] Upload to Test PyPI (`make upload-test`)
- [ ] Test installation from Test PyPI
- [ ] Upload to production PyPI (`make upload`)
- [ ] Create GitHub release
- [ ] Update documentation links

### Post-Release
- [ ] Verify PyPI package page
- [ ] Test installation from PyPI
- [ ] Update project README with installation instructions
- [ ] Announce release

## Troubleshooting Deployment

### Common Build Issues

1. **Missing Dependencies**:
```bash
pip install --upgrade build twine wheel setuptools
```

2. **Permission Errors**:
```bash
# Use virtual environment
python -m venv venv
source venv/bin/activate
```

3. **Twine Upload Errors**:
```bash
# Check credentials
keyring get https://upload.pypi.org/legacy/ __token__

# Re-authenticate
keyring set https://upload.pypi.org/legacy/ __token__
```

### Verification Steps

1. **Check Package Contents**:
```bash
# Extract and inspect wheel
unzip -l dist/speech_to_text-0.1.0-py3-none-any.whl

# Extract and inspect source distribution
tar -tzf dist/speech_to_text-0.1.0.tar.gz
```

2. **Test Installation**:
```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate

# Install and test
pip install dist/speech_to_text-0.1.0-py3-none-any.whl
speech-to-text --help
speech-to-text doctor
```

3. **Verify Metadata**:
```bash
# Check package metadata
pip show speech-to-text

# Check entry points
pip show -f speech-to-text | grep console_scripts
```

## Security Considerations

### Package Security
- All dependencies are pinned to specific versions
- No known security vulnerabilities in dependencies
- Package is signed with GPG (optional)

### Distribution Security
- Use HTTPS for all uploads
- Verify checksums (SHA256SUMS files provided)
- Use API tokens instead of passwords for PyPI

### User Security
- Installation script validates system requirements
- No elevated privileges required for normal operation
- All temporary files are cleaned up automatically

## Support and Maintenance

### Version Management
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Update version in `pyproject.toml` and `__init__.py`
- Tag releases in git

### Dependency Updates
- Regularly update dependencies for security
- Test compatibility with new versions
- Update requirements.txt and pyproject.toml

### Documentation Maintenance
- Keep installation instructions current
- Update examples with new features
- Maintain troubleshooting guide

For questions about deployment, please create an issue on the project repository.