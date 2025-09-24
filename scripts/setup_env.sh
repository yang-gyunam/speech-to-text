#!/bin/bash

# Setup script for Speech-to-Text application
echo "Setting up Speech-to-Text application environment..."

# Check if Python 3.8+ is available
python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
echo "Python version: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setup complete!"
echo "To activate the environment in the future, run:"
echo "source venv/bin/activate"