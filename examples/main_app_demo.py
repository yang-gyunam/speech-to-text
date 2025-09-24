#!/usr/bin/env python3
"""
Demonstration script for the SpeechToTextApp main application.

This script shows how to use the main application class for both
single file and batch processing workflows.
"""

import tempfile
from pathlib import Path
from src.speech_to_text import SpeechToTextApp


def create_demo_files():
    """Create some demo audio files for testing."""
    temp_dir = tempfile.mkdtemp()
    demo_dir = Path(temp_dir) / "demo_audio"
    demo_dir.mkdir()
    
    # Create some fake audio files
    files = []
    for i in range(3):
        audio_file = demo_dir / f"demo_recording_{i}.m4a"
        audio_file.write_bytes(b"fake audio content for demo")
        files.append(str(audio_file))
    
    return str(demo_dir), files


def demo_single_file_processing():
    """Demonstrate single file processing."""
    print("=== Single File Processing Demo ===")
    
    # Create demo files
    demo_dir, files = create_demo_files()
    single_file = files[0]
    
    # Create output directory
    output_dir = Path(demo_dir).parent / "output"
    
    try:
        # Initialize the app
        with SpeechToTextApp(
            model_size="base",
            language="ko",
            output_dir=str(output_dir),
            include_metadata=True
        ) as app:
            
            print(f"Processing single file: {Path(single_file).name}")
            print(f"Output directory: {output_dir}")
            
            # This would normally process the file, but will fail with fake audio
            # In a real scenario, this would transcribe the audio
            try:
                result = app.process_single_file(single_file)
                print(f"✅ Success: {result.transcribed_text[:50]}...")
            except Exception as e:
                print(f"❌ Expected error with fake audio: {type(e).__name__}")
                
    except Exception as e:
        print(f"Demo error: {e}")
    
    print()


def demo_batch_processing():
    """Demonstrate batch processing."""
    print("=== Batch Processing Demo ===")
    
    # Create demo files
    demo_dir, files = create_demo_files()
    
    # Create output directory
    output_dir = Path(demo_dir).parent / "batch_output"
    
    try:
        # Initialize the app
        with SpeechToTextApp(
            model_size="base",
            language="ko",
            output_dir=str(output_dir),
            include_metadata=True
        ) as app:
            
            print(f"Processing directory: {demo_dir}")
            print(f"Found {len(files)} audio files")
            print(f"Output directory: {output_dir}")
            
            # Progress callback for demonstration
            def progress_callback(current, total, current_file):
                filename = Path(current_file).name
                print(f"  [{current+1}/{total}] Processing: {filename}")
            
            # This would normally process all files, but will fail with fake audio
            try:
                results = app.process_directory(
                    demo_dir,
                    recursive=True,
                    progress_callback=progress_callback
                )
                
                successful = len([r for r in results if not r.error_message])
                failed = len(results) - successful
                
                print(f"✅ Batch processing completed:")
                print(f"   - Successful: {successful}")
                print(f"   - Failed: {failed}")
                
            except Exception as e:
                print(f"❌ Expected error with fake audio: {type(e).__name__}")
                
    except Exception as e:
        print(f"Demo error: {e}")
    
    print()


def demo_app_features():
    """Demonstrate various app features."""
    print("=== App Features Demo ===")
    
    try:
        app = SpeechToTextApp()
        
        # Show supported formats
        formats = app.get_supported_formats()
        print(f"Supported audio formats: {', '.join(formats)}")
        
        # Show app configuration
        print(f"Default model size: {app.model_size}")
        print(f"Default language: {app.language}")
        print(f"Default output directory: {app.output_dir}")
        print(f"Include metadata: {app.include_metadata}")
        
        # Show lazy loading
        print(f"Components initialized: {app._audio_processor is not None}")
        
        # Access a component to trigger lazy loading
        _ = app.audio_processor
        print(f"After accessing audio_processor: {app._audio_processor is not None}")
        
    except Exception as e:
        print(f"Demo error: {e}")
    
    print()


def main():
    """Run all demonstrations."""
    print("SpeechToTextApp Main Application Demo")
    print("=" * 50)
    print()
    
    print("This demo shows how to use the main application class.")
    print("Note: Demos will show expected errors since we're using fake audio files.")
    print()
    
    # Run demonstrations
    demo_app_features()
    demo_single_file_processing()
    demo_batch_processing()
    
    print("Demo completed! 🎉")
    print()
    print("To use with real audio files:")
    print("1. Replace demo files with actual .m4a, .wav, .mp3, etc. files")
    print("2. Ensure OpenAI Whisper is properly installed")
    print("3. Use the same API as shown in the demos")


if __name__ == "__main__":
    main()