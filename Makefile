.PHONY: install test lint format type-check clean setup build dist upload release install-user uninstall

# Setup virtual environment and install dependencies
setup:
	python3 -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	. venv/bin/activate && pip install -e .

# Install package in development mode
install:
	pip install -e .

# Install for current user (production install)
install-user:
	pip install --user .

# Uninstall package
uninstall:
	pip uninstall speech-to-text

# Run tests
test:
	pytest

# Run tests with coverage
test-cov:
	pytest --cov=src --cov-report=html --cov-report=term-missing

# Lint code
lint:
	flake8 src/ tests/

# Format code
format:
	black src/ tests/

# Type checking
type-check:
	mypy src/

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf release/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Install build dependencies
build-deps:
	pip install --upgrade build twine wheel setuptools

# Build source distribution
build-sdist: clean build-deps
	python -m build --sdist

# Build wheel distribution
build-wheel: clean build-deps
	python -m build --wheel

# Build both distributions
build: clean build-deps
	python -m build

# Verify distributions
verify-dist:
	twine check dist/*

# Build and verify
dist: build verify-dist
	@echo "Distribution files created:"
	@ls -la dist/

# Upload to PyPI (requires authentication)
upload: dist
	twine upload dist/*

# Upload to Test PyPI
upload-test: dist
	twine upload --repository testpypi dist/*

# Create release package
release: dist
	./build_dist.sh

# Quick build without checks
quick-build:
	./build_dist.sh --skip-checks

# Install from wheel (for testing)
install-wheel: build-wheel
	pip install --force-reinstall dist/*.whl

# Test installation in clean environment
test-install:
	@echo "Testing installation in temporary environment..."
	@python3 -m venv /tmp/test_speech_to_text
	@. /tmp/test_speech_to_text/bin/activate && pip install dist/*.whl
	@. /tmp/test_speech_to_text/bin/activate && speech-to-text --help
	@. /tmp/test_speech_to_text/bin/activate && speech-to-text doctor
	@rm -rf /tmp/test_speech_to_text
	@echo "Installation test passed!"

# Run all quality checks
check: lint type-check test

# Full quality check and build
full-check: check dist test-install

# Development workflow
dev: setup test

# Production workflow
prod: full-check release

# Help
help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  setup         - Create virtual environment and install dependencies"
	@echo "  install       - Install package in development mode"
	@echo "  dev           - Setup and test (development workflow)"
	@echo "  test          - Run tests"
	@echo "  test-cov      - Run tests with coverage"
	@echo "  lint          - Run linting"
	@echo "  format        - Format code"
	@echo "  type-check    - Run type checking"
	@echo "  check         - Run all quality checks"
	@echo "  clean         - Clean build artifacts"
	@echo ""
	@echo "Building and Distribution:"
	@echo "  build-deps    - Install build dependencies"
	@echo "  build-sdist   - Build source distribution"
	@echo "  build-wheel   - Build wheel distribution"
	@echo "  build         - Build both distributions"
	@echo "  dist          - Build and verify distributions"
	@echo "  verify-dist   - Verify distribution files"
	@echo "  release       - Create complete release package"
	@echo "  quick-build   - Build without running checks"
	@echo ""
	@echo "Installation and Testing:"
	@echo "  install-user  - Install for current user"
	@echo "  install-wheel - Install from built wheel"
	@echo "  test-install  - Test installation in clean environment"
	@echo "  uninstall     - Uninstall package"
	@echo ""
	@echo "Publishing:"
	@echo "  upload        - Upload to PyPI"
	@echo "  upload-test   - Upload to Test PyPI"
	@echo ""
	@echo "Workflows:"
	@echo "  full-check    - Complete quality check and build"
	@echo "  prod          - Full production workflow (check + release)"