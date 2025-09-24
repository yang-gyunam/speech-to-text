#!/bin/bash
# Speech-to-Text Installation Script for macOS
# This script installs the Speech-to-Text application and its dependencies

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_MIN_VERSION="3.8"
INSTALL_DIR="$HOME/.local/speech-to-text"
BIN_DIR="$HOME/.local/bin"
VENV_DIR="$INSTALL_DIR/venv"

# Functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

version_compare() {
    # Compare version strings
    # Returns 0 if $1 >= $2, 1 otherwise
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

check_python_version() {
    if check_command python3; then
        PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
        if version_compare "$PYTHON_VERSION" "$PYTHON_MIN_VERSION"; then
            print_success "Python $PYTHON_VERSION found"
            return 0
        else
            print_error "Python $PYTHON_VERSION found, but $PYTHON_MIN_VERSION or higher is required"
            return 1
        fi
    else
        print_error "Python 3 not found"
        return 1
    fi
}

install_homebrew() {
    if ! check_command brew; then
        print_status "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH for Apple Silicon Macs
        if [[ $(uname -m) == "arm64" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    else
        print_success "Homebrew already installed"
    fi
}

install_python() {
    if ! check_python_version; then
        print_status "Installing Python..."
        if check_command brew; then
            brew install python@3.11
        else
            print_error "Please install Python $PYTHON_MIN_VERSION or higher manually"
            print_error "Visit: https://www.python.org/downloads/macos/"
            exit 1
        fi
    fi
}

install_ffmpeg() {
    if ! check_command ffmpeg; then
        print_status "Installing FFmpeg..."
        if check_command brew; then
            brew install ffmpeg
        else
            print_error "Please install FFmpeg manually"
            print_error "Visit: https://ffmpeg.org/download.html"
            exit 1
        fi
    else
        print_success "FFmpeg already installed"
    fi
}

create_directories() {
    print_status "Creating installation directories..."
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$BIN_DIR"
}

install_application() {
    print_status "Installing Speech-to-Text application..."
    
    # Create virtual environment
    print_status "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install the application
    if [[ -f "pyproject.toml" ]]; then
        # Install from source
        print_status "Installing from source..."
        pip install .
    else
        # Install from PyPI (when available)
        print_status "Installing from PyPI..."
        pip install speech-to-text
    fi
    
    # Create wrapper script
    print_status "Creating command-line wrapper..."
    cat > "$BIN_DIR/speech-to-text" << EOF
#!/bin/bash
# Speech-to-Text wrapper script
source "$VENV_DIR/bin/activate"
exec python -m speech_to_text "\$@"
EOF
    
    chmod +x "$BIN_DIR/speech-to-text"
}

setup_shell_integration() {
    print_status "Setting up shell integration..."
    
    # Detect shell
    SHELL_NAME=$(basename "$SHELL")
    case "$SHELL_NAME" in
        "zsh")
            SHELL_RC="$HOME/.zshrc"
            ;;
        "bash")
            SHELL_RC="$HOME/.bash_profile"
            ;;
        *)
            SHELL_RC="$HOME/.profile"
            ;;
    esac
    
    # Add to PATH if not already there
    if ! echo "$PATH" | grep -q "$BIN_DIR"; then
        echo "" >> "$SHELL_RC"
        echo "# Speech-to-Text" >> "$SHELL_RC"
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$SHELL_RC"
        print_success "Added $BIN_DIR to PATH in $SHELL_RC"
    fi
}

download_models() {
    print_status "Downloading Whisper models..."
    source "$VENV_DIR/bin/activate"
    
    # Download base model (most commonly used)
    python -c "import whisper; whisper.load_model('base')" || {
        print_warning "Failed to download base model. It will be downloaded on first use."
    }
}

run_tests() {
    print_status "Running system check..."
    source "$VENV_DIR/bin/activate"
    
    # Test installation
    if python -c "import speech_to_text; print('Import successful')"; then
        print_success "Package import successful"
    else
        print_error "Package import failed"
        return 1
    fi
    
    # Test command-line interface
    if "$BIN_DIR/speech-to-text" --help >/dev/null 2>&1; then
        print_success "Command-line interface working"
    else
        print_error "Command-line interface failed"
        return 1
    fi
    
    # Run doctor command
    "$BIN_DIR/speech-to-text" doctor
}

cleanup() {
    print_status "Cleaning up temporary files..."
    # Remove any temporary files if needed
}

main() {
    echo "Speech-to-Text Installation Script"
    echo "=================================="
    echo ""
    
    # Check if running on macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_warning "This script is designed for macOS. It may not work on other systems."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check for existing installation
    if [[ -d "$INSTALL_DIR" ]]; then
        print_warning "Existing installation found at $INSTALL_DIR"
        read -p "Remove existing installation and continue? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$INSTALL_DIR"
        else
            print_error "Installation cancelled"
            exit 1
        fi
    fi
    
    # Installation steps
    print_status "Starting installation..."
    
    # Install dependencies
    install_homebrew
    install_python
    install_ffmpeg
    
    # Install application
    create_directories
    install_application
    setup_shell_integration
    download_models
    
    # Test installation
    run_tests
    
    # Cleanup
    cleanup
    
    # Success message
    echo ""
    print_success "Installation completed successfully!"
    echo ""
    echo "To get started:"
    echo "1. Restart your terminal or run: source ~/.zshrc"
    echo "2. Test the installation: speech-to-text --help"
    echo "3. Run system check: speech-to-text doctor"
    echo "4. See examples: speech-to-text examples"
    echo ""
    echo "Documentation:"
    echo "- README: https://github.com/example/speech-to-text#readme"
    echo "- Installation guide: INSTALLATION.md"
    echo "- Examples: EXAMPLES.md"
    echo "- Troubleshooting: TROUBLESHOOTING.md"
    echo ""
    print_success "Happy transcribing!"
}

# Handle interruption
trap cleanup EXIT

# Run main function
main "$@"