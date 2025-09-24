#!/usr/bin/env python3
"""
Simple usage example for the SpeechToTextApp.

This shows the most basic way to use the integrated application.
"""

from src.speech_to_text import SpeechToTextApp


def simple_single_file_example():
    """Simple single file processing example."""
    
    # Initialize the app with Korean language (default)
    app = SpeechToTextApp(
        model_size="base",      # Whisper model size
        language="ko",          # Korean language
        output_dir="./output"   # Output directory
    )
    
    try:
        # Process a single audio file
        result = app.process_single_file("recording.m4a")
        
        if result.error_message:
            print(f"❌ Transcription failed: {result.error_message}")
        else:
            print(f"✅ Transcription successful!")
            print(f"📝 Text: {result.transcribed_text}")
            print(f"🎯 Confidence: {result.confidence_score:.2f}")
            print(f"⏱️  Processing time: {result.processing_time:.1f}s")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        app.close()  # Clean up resources


def simple_batch_processing_example():
    """Simple batch processing example."""
    
    # Use context manager for automatic cleanup
    with SpeechToTextApp(language="ko", output_dir="./batch_output") as app:
        
        try:
            # Process all audio files in a directory
            results = app.process_directory("./audio_files", recursive=True)
            
            # Show summary
            successful = len([r for r in results if not r.error_message])
            failed = len(results) - successful
            
            print(f"📊 Batch processing completed:")
            print(f"   ✅ Successful: {successful}")
            print(f"   ❌ Failed: {failed}")
            print(f"   📁 Total files: {len(results)}")
            
            # Show individual results
            for result in results:
                filename = result.original_file.split('/')[-1]
                if result.error_message:
                    print(f"   ❌ {filename}: {result.error_message}")
                else:
                    print(f"   ✅ {filename}: {len(result.transcribed_text)} characters")
                    
        except Exception as e:
            print(f"Error: {e}")


def custom_configuration_example():
    """Example with custom configuration."""
    
    app = SpeechToTextApp(
        model_size="large",           # Use large model for better accuracy
        language="en",                # English language
        output_dir="/custom/output",  # Custom output directory
        include_metadata=False        # Don't include metadata in output
    )
    
    try:
        # Process with custom language override
        result = app.process_single_file("english_recording.wav", language="en")
        
        # Get audio file information
        audio_info = app.get_audio_info("english_recording.wav")
        print(f"📄 File info: {audio_info['duration']:.1f}s, {audio_info['format']}")
        
        # Preprocess audio if needed
        processed_file = app.preprocess_audio(
            "noisy_recording.wav", 
            normalize=True, 
            remove_silence=True
        )
        
        # Process the preprocessed file
        result = app.process_single_file(processed_file)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        app.close()


if __name__ == "__main__":
    print("Simple SpeechToTextApp Usage Examples")
    print("=" * 40)
    
    print("\n1. Single file processing:")
    simple_single_file_example()
    
    print("\n2. Batch processing:")
    simple_batch_processing_example()
    
    print("\n3. Custom configuration:")
    custom_configuration_example()
    
    print("\nDone! 🎉")