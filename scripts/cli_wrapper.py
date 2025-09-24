#!/usr/bin/env python3
"""
CLI wrapper for speech-to-text to fix import issues with PyInstaller.

This wrapper handles the imports properly for standalone executables.
"""

import sys
import os
from pathlib import Path

# Add the source directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Now import the main CLI function
try:
    from speech_to_text.cli import main
except ImportError as e:
    print(f"Error importing CLI module: {e}", file=sys.stderr)
    print("Available modules:", os.listdir(src_dir / "speech_to_text") if (src_dir / "speech_to_text").exists() else "Source directory not found", file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    if sys.argv[0].endswith('.exe'):
        sys.argv[0] = sys.argv[0][:-4]
    sys.exit(main())