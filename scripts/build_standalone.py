#!/usr/bin/env python3
"""
Build standalone executable for speech-to-text CLI using PyInstaller.

This script creates a self-contained executable that includes all dependencies,
eliminating the need for virtual environments or Python installations.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔧 {description}")
    print(f"   Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"   Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print(f"   Stdout: {e.stdout}")
        if e.stderr:
            print(f"   Stderr: {e.stderr}")
        return False

def main():
    """Main build function."""
    print("🚀 Building standalone speech-to-text executable")

    # Get project root
    project_root = Path(__file__).parent
    src_dir = project_root / "src"
    cli_module = src_dir / "speech_to_text" / "cli.py"

    if not cli_module.exists():
        print(f"❌ CLI module not found at: {cli_module}")
        sys.exit(1)

    # Create build directory
    build_dir = project_root / "build_standalone"
    build_dir.mkdir(exist_ok=True)

    # Change to project directory
    os.chdir(project_root)

    # Create virtual environment if it doesn't exist
    venv_dir = project_root / "venv_build"
    if not venv_dir.exists():
        if not run_command(["python3", "-m", "venv", str(venv_dir)], "Creating virtual environment"):
            sys.exit(1)

    # Activate virtual environment and install dependencies
    if sys.platform.startswith('win'):
        pip_cmd = str(venv_dir / "Scripts" / "pip")
        python_cmd = str(venv_dir / "Scripts" / "python")
    else:
        pip_cmd = str(venv_dir / "bin" / "pip")
        python_cmd = str(venv_dir / "bin" / "python")

    # Install project dependencies and PyInstaller
    if not run_command([pip_cmd, "install", "-e", "."], "Installing project dependencies"):
        print("⚠️  Failed to install project dependencies, continuing...")

    if not run_command([pip_cmd, "install", "pyinstaller"], "Installing PyInstaller"):
        sys.exit(1)

    # Create PyInstaller spec file for better control
    cli_path = str(project_root / "cli_wrapper.py")
    src_path = str(project_root / "src" / "speech_to_text")

    # Find Python version dynamically
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    site_packages = venv_dir / "lib" / f"python{python_version}" / "site-packages"
    whisper_assets_path = str(site_packages / "whisper" / "assets")

    print(f"🔍 Looking for Whisper assets at: {whisper_assets_path}")
    if not Path(whisper_assets_path).exists():
        print(f"⚠️  Whisper assets not found, trying alternative paths...")
        # Try finding whisper assets in different locations
        import whisper
        whisper_module_path = Path(whisper.__file__).parent
        whisper_assets_path = str(whisper_module_path / "assets")
        print(f"🔍 Alternative Whisper assets path: {whisper_assets_path}")
    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Add src to path so imports work
sys.path.insert(0, str(Path.cwd() / "src"))

block_cipher = None

a = Analysis(
    ['{cli_path}'],
    pathex=[str(Path.cwd()), str(Path.cwd() / "src")],
    binaries=[],
    datas=[
        ('{src_path}', 'speech_to_text'),
        # Include Whisper assets
        ('{whisper_assets_path}', 'whisper/assets'),
        # Include additional torch/transformers data if available
    ],
    hiddenimports=[
        'speech_to_text',
        'speech_to_text.cli',
        'speech_to_text.audio',
        'speech_to_text.transcriber',
        'speech_to_text.exporter',
        'speech_to_text.file_manager',
        'speech_to_text.config',
        'speech_to_text.exceptions',
        'whisper',
        'whisper.model',
        'whisper.audio',
        'whisper.decoding',
        'whisper.timing',
        'whisper.tokenizer',
        'torch',
        'torch.nn',
        'torch.nn.functional',
        'torchaudio',
        'torchaudio.functional',
        'torchaudio.transforms',
        'transformers',
        'tiktoken',
        'tiktoken.core',
        'regex',
        'ftfy',
        'numba',
        'numba.core',
        'llvmlite',
        'numpy',
        'ffmpeg',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filter out problematic binaries if needed
a.binaries = [x for x in a.binaries if not x[0].startswith('libopenblas')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='speech-to-text',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to avoid compression issues
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""

    spec_file = build_dir / "speech-to-text.spec"
    with open(spec_file, 'w') as f:
        f.write(spec_content.strip())

    print(f"📝 Created spec file: {spec_file}")

    # Build with PyInstaller
    if sys.platform.startswith('win'):
        pyinstaller_cmd = str(venv_dir / "Scripts" / "pyinstaller")
    else:
        pyinstaller_cmd = str(venv_dir / "bin" / "pyinstaller")

    build_cmd = [
        pyinstaller_cmd,
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]

    if not run_command(build_cmd, "Building standalone executable with PyInstaller"):
        print("❌ Build failed")
        sys.exit(1)

    # Find the built executable
    dist_dir = project_root / "dist"
    executable = dist_dir / "speech-to-text"

    if not executable.exists():
        # Try with .exe extension (Windows)
        executable = dist_dir / "speech-to-text.exe"

    if executable.exists():
        print(f"✅ Standalone executable built successfully: {executable}")

        # Make it executable on Unix systems
        if not sys.platform.startswith('win'):
            os.chmod(executable, 0o755)

        # Test the executable
        test_cmd = [str(executable), "--version"]
        if run_command(test_cmd, "Testing standalone executable"):
            print("✅ Executable test successful!")
        else:
            print("⚠️  Executable test failed, but build completed")

        # Copy to tauri directory for bundling
        tauri_dir = project_root / "tauri-svelte5-app" / "src-tauri"
        if tauri_dir.exists():
            # Determine target filename based on platform
            import platform
            arch = platform.machine().lower()
            system = platform.system().lower()

            if system == "darwin":
                if arch in ["arm64", "aarch64"]:
                    target_name = "speech-to-text-aarch64-apple-darwin"
                else:
                    target_name = "speech-to-text-x86_64-apple-darwin"
            elif system == "linux":
                if arch in ["arm64", "aarch64"]:
                    target_name = "speech-to-text-aarch64-unknown-linux-gnu"
                else:
                    target_name = "speech-to-text-x86_64-unknown-linux-gnu"
            elif system == "windows":
                if arch in ["arm64", "aarch64"]:
                    target_name = "speech-to-text-aarch64-pc-windows-msvc.exe"
                else:
                    target_name = "speech-to-text-x86_64-pc-windows-msvc.exe"
            else:
                target_name = "speech-to-text"

            target_path = tauri_dir / target_name
            try:
                shutil.copy2(executable, target_path)
                os.chmod(target_path, 0o755)
                print(f"✅ Copied to Tauri directory: {target_path}")
            except Exception as e:
                print(f"⚠️  Failed to copy to Tauri directory: {e}")

    else:
        print("❌ Executable not found after build")
        sys.exit(1)

if __name__ == "__main__":
    main()