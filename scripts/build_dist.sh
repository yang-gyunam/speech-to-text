#!/bin/bash
# Build script for creating distribution packages

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if we're in a virtual environment
check_venv() {
    if [[ -z "$VIRTUAL_ENV" ]]; then
        print_warning "Not in a virtual environment. Activating venv..."
        if [[ -d "venv" ]]; then
            source venv/bin/activate
        else
            print_error "Virtual environment not found. Run setup_env.sh first."
            exit 1
        fi
    fi
}

# Clean previous builds
clean_build() {
    print_status "Cleaning previous builds..."
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info/
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
}

# Install build dependencies
install_build_deps() {
    print_status "Installing build dependencies..."
    pip install --upgrade pip
    pip install --upgrade build twine wheel setuptools
}

# Run tests before building
run_tests() {
    print_status "Running tests..."
    if command -v pytest >/dev/null 2>&1; then
        pytest tests/ -v
    else
        print_warning "pytest not found, skipping tests"
    fi
}

# Run code quality checks
run_quality_checks() {
    print_status "Running code quality checks..."
    
    # Format check
    if command -v black >/dev/null 2>&1; then
        print_status "Checking code formatting..."
        black --check src/ tests/ || {
            print_warning "Code formatting issues found. Run 'black src/ tests/' to fix."
        }
    fi
    
    # Lint check
    if command -v flake8 >/dev/null 2>&1; then
        print_status "Running linter..."
        flake8 src/ tests/ || {
            print_warning "Linting issues found."
        }
    fi
    
    # Type check
    if command -v mypy >/dev/null 2>&1; then
        print_status "Running type checker..."
        mypy src/ || {
            print_warning "Type checking issues found."
        }
    fi
}

# Build source distribution
build_sdist() {
    print_status "Building source distribution..."
    python -m build --sdist
}

# Build wheel distribution
build_wheel() {
    print_status "Building wheel distribution..."
    python -m build --wheel
}

# Verify distributions
verify_dist() {
    print_status "Verifying distributions..."
    
    # Check if files were created
    if [[ ! -d "dist" ]] || [[ -z "$(ls -A dist/)" ]]; then
        print_error "No distribution files found"
        exit 1
    fi
    
    # List created files
    print_status "Created distribution files:"
    ls -la dist/
    
    # Check with twine
    if command -v twine >/dev/null 2>&1; then
        print_status "Checking distributions with twine..."
        twine check dist/*
    fi
}

# Test installation from wheel
test_wheel_install() {
    print_status "Testing wheel installation..."
    
    # Create temporary virtual environment
    TEMP_VENV=$(mktemp -d)/test_venv
    python -m venv "$TEMP_VENV"
    source "$TEMP_VENV/bin/activate"
    
    # Install from wheel
    WHEEL_FILE=$(ls dist/*.whl | head -n 1)
    pip install "$WHEEL_FILE"
    
    # Test import
    python -c "import speech_to_text; print('Import successful')"
    
    # Test CLI
    speech-to-text --help >/dev/null
    
    # Cleanup
    deactivate
    rm -rf "$TEMP_VENV"
    
    print_success "Wheel installation test passed"
}

# Create release archive
create_release_archive() {
    print_status "Creating release archive..."
    
    VERSION=$(python -c "import speech_to_text; print(speech_to_text.__version__)" 2>/dev/null || echo "0.1.0")
    ARCHIVE_NAME="speech-to-text-${VERSION}-release"
    
    # Create release directory
    mkdir -p "release/$ARCHIVE_NAME"
    
    # Copy distribution files
    cp -r dist/ "release/$ARCHIVE_NAME/"
    
    # Copy documentation
    cp README.md "release/$ARCHIVE_NAME/"
    cp INSTALLATION.md "release/$ARCHIVE_NAME/"
    cp EXAMPLES.md "release/$ARCHIVE_NAME/"
    cp TROUBLESHOOTING.md "release/$ARCHIVE_NAME/"
    cp CHANGELOG.md "release/$ARCHIVE_NAME/"
    cp LICENSE "release/$ARCHIVE_NAME/"
    
    # Copy installation script
    cp install.sh "release/$ARCHIVE_NAME/"
    chmod +x "release/$ARCHIVE_NAME/install.sh"
    
    # Create archive
    cd release/
    tar -czf "${ARCHIVE_NAME}.tar.gz" "$ARCHIVE_NAME"
    zip -r "${ARCHIVE_NAME}.zip" "$ARCHIVE_NAME"
    cd ..
    
    print_success "Release archive created: release/${ARCHIVE_NAME}.tar.gz"
    print_success "Release archive created: release/${ARCHIVE_NAME}.zip"
}

# Generate checksums
generate_checksums() {
    print_status "Generating checksums..."
    
    cd dist/
    shasum -a 256 * > SHA256SUMS
    cd ..
    
    if [[ -d "release" ]]; then
        cd release/
        shasum -a 256 *.tar.gz *.zip > SHA256SUMS
        cd ..
    fi
    
    print_success "Checksums generated"
}

# Main build process
main() {
    echo "Speech-to-Text Build Script"
    echo "=========================="
    echo ""
    
    # Pre-build checks
    check_venv
    
    # Build process
    clean_build
    install_build_deps
    
    # Quality checks (optional, can be skipped with --skip-checks)
    if [[ "$1" != "--skip-checks" ]]; then
        run_tests
        run_quality_checks
    fi
    
    # Build distributions
    build_sdist
    build_wheel
    
    # Verify and test
    verify_dist
    test_wheel_install
    
    # Create release packages
    create_release_archive
    generate_checksums
    
    # Summary
    echo ""
    print_success "Build completed successfully!"
    echo ""
    echo "Distribution files:"
    ls -la dist/
    echo ""
    echo "Release files:"
    ls -la release/ 2>/dev/null || echo "No release files created"
    echo ""
    echo "Next steps:"
    echo "1. Test the wheel: pip install dist/*.whl"
    echo "2. Upload to PyPI: twine upload dist/*"
    echo "3. Create GitHub release with release/*.tar.gz"
    echo ""
}

# Handle command line arguments
case "$1" in
    "--help"|"-h")
        echo "Usage: $0 [--skip-checks]"
        echo ""
        echo "Options:"
        echo "  --skip-checks    Skip tests and quality checks"
        echo "  --help, -h       Show this help message"
        exit 0
        ;;
esac

# Run main function
main "$@"