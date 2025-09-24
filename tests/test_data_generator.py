#!/usr/bin/env python3
"""
Test data generator for speech-to-text testing.

This module provides utilities to generate test audio files in various formats
that simulate iPhone recordings and other audio sources for comprehensive testing.
"""

import os
import sys
import wave
import struct
import random
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@dataclass
class AudioTestData:
    """Test audio data configuration."""
    filename: str
    format: str
    duration: float  # seconds
    sample_rate: int
    channels: int
    content_type: str  # 'korean', 'english', 'mixed', 'silence', 'noise'
    expected_text: Optional[str] = None


class TestDataGenerator:
    """Generator for test audio data in various formats."""
    
    def __init__(self, output_dir: str = None):
        """
        Initialize the test data generator.
        
        Args:
            output_dir: Directory to save generated test files
        """
        self.output_dir = output_dir or tempfile.mkdtemp(prefix="test_audio_")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # iPhone recording characteristics
        self.iphone_configs = {
            'voice_memo_high': {
                'format': 'm4a',
                'sample_rate': 44100,
                'channels': 1,
                'bitrate': 64000
            },
            'voice_memo_standard': {
                'format': 'm4a',
                'sample_rate': 22050,
                'channels': 1,
                'bitrate': 32000
            },
            'video_audio': {
                'format': 'aac',
                'sample_rate': 48000,
                'channels': 2,
                'bitrate': 128000
            }
        }
        
        # Test scenarios
        self.test_scenarios = [
            AudioTestData(
                filename="korean_greeting.wav",
                format="wav",
                duration=3.0,
                sample_rate=44100,
                channels=1,
                content_type="korean",
                expected_text="안녕하세요"
            ),
            AudioTestData(
                filename="korean_long_sentence.wav",
                format="wav",
                duration=8.0,
                sample_rate=44100,
                channels=1,
                content_type="korean",
                expected_text="오늘 회의에서 프로젝트 진행 상황을 보고드리겠습니다"
            ),
            AudioTestData(
                filename="mixed_language.wav",
                format="wav",
                duration=5.0,
                sample_rate=44100,
                channels=1,
                content_type="mixed",
                expected_text="Hello 안녕하세요 Thank you 감사합니다"
            ),
            AudioTestData(
                filename="english_phrase.wav",
                format="wav",
                duration=4.0,
                sample_rate=44100,
                channels=1,
                content_type="english",
                expected_text="This is a test recording"
            ),
            AudioTestData(
                filename="silence.wav",
                format="wav",
                duration=2.0,
                sample_rate=44100,
                channels=1,
                content_type="silence",
                expected_text=""
            ),
            AudioTestData(
                filename="noisy_korean.wav",
                format="wav",
                duration=6.0,
                sample_rate=44100,
                channels=1,
                content_type="korean",
                expected_text="배경 소음이 있는 한국어 음성입니다"
            )
        ]
    
    def generate_sine_wave(self, frequency: float, duration: float, 
                          sample_rate: int, amplitude: float = 0.3) -> List[float]:
        """
        Generate a sine wave for testing.
        
        Args:
            frequency: Frequency in Hz
            duration: Duration in seconds
            sample_rate: Sample rate in Hz
            amplitude: Amplitude (0.0 to 1.0)
            
        Returns:
            List of audio samples
        """
        import math
        
        samples = []
        for i in range(int(duration * sample_rate)):
            t = i / sample_rate
            sample = amplitude * math.sin(2 * math.pi * frequency * t)
            samples.append(sample)
        
        return samples
    
    def generate_white_noise(self, duration: float, sample_rate: int, 
                           amplitude: float = 0.1) -> List[float]:
        """
        Generate white noise for testing.
        
        Args:
            duration: Duration in seconds
            sample_rate: Sample rate in Hz
            amplitude: Amplitude (0.0 to 1.0)
            
        Returns:
            List of audio samples
        """
        samples = []
        for _ in range(int(duration * sample_rate)):
            sample = amplitude * (random.random() * 2 - 1)  # Random between -amplitude and +amplitude
            samples.append(sample)
        
        return samples
    
    def generate_speech_like_signal(self, duration: float, sample_rate: int,
                                  content_type: str = "korean") -> List[float]:
        """
        Generate a speech-like signal for testing.
        
        This creates a complex waveform that simulates speech characteristics
        without being actual speech.
        
        Args:
            duration: Duration in seconds
            sample_rate: Sample rate in Hz
            content_type: Type of content to simulate
            
        Returns:
            List of audio samples
        """
        import math
        
        samples = []
        
        # Speech-like frequency ranges
        if content_type == "korean":
            # Korean speech characteristics
            base_frequencies = [200, 400, 800, 1600]  # Formant-like frequencies
            modulation_rate = 5  # Hz
        elif content_type == "english":
            # English speech characteristics
            base_frequencies = [250, 500, 1000, 2000]
            modulation_rate = 4
        else:
            # Mixed or default
            base_frequencies = [225, 450, 900, 1800]
            modulation_rate = 4.5
        
        for i in range(int(duration * sample_rate)):
            t = i / sample_rate
            
            # Create complex waveform with multiple frequencies
            sample = 0
            for freq in base_frequencies:
                # Add frequency component with amplitude modulation
                amplitude = 0.1 * (1 + 0.5 * math.sin(2 * math.pi * modulation_rate * t))
                sample += amplitude * math.sin(2 * math.pi * freq * t)
            
            # Add some noise for realism
            sample += 0.02 * (random.random() * 2 - 1)
            
            # Apply envelope to simulate speech pauses
            envelope = 1.0
            if content_type != "silence":
                # Create speech-like envelope with pauses
                envelope_freq = 0.5  # Slow modulation for speech pauses
                envelope = 0.5 + 0.5 * math.sin(2 * math.pi * envelope_freq * t)
                if envelope < 0.3:
                    envelope = 0.1  # Quiet periods
            else:
                envelope = 0.01  # Very quiet for silence
            
            sample *= envelope
            
            # Clamp to prevent clipping
            sample = max(-1.0, min(1.0, sample))
            samples.append(sample)
        
        return samples
    
    def create_wav_file(self, filename: str, samples: List[float], 
                       sample_rate: int, channels: int = 1) -> str:
        """
        Create a WAV file from audio samples.
        
        Args:
            filename: Output filename
            samples: Audio samples
            sample_rate: Sample rate in Hz
            channels: Number of channels
            
        Returns:
            Path to created file
        """
        filepath = os.path.join(self.output_dir, filename)
        
        with wave.open(filepath, 'w') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Convert float samples to 16-bit integers
            for sample in samples:
                # Convert to 16-bit signed integer
                int_sample = int(sample * 32767)
                int_sample = max(-32768, min(32767, int_sample))
                
                # Write for each channel
                for _ in range(channels):
                    wav_file.writeframes(struct.pack('<h', int_sample))
        
        return filepath
    
    def generate_test_files(self) -> Dict[str, str]:
        """
        Generate all test audio files.
        
        Returns:
            Dictionary mapping test scenario names to file paths
        """
        generated_files = {}
        
        print(f"Generating test audio files in: {self.output_dir}")
        
        for scenario in self.test_scenarios:
            print(f"Generating: {scenario.filename}")
            
            if scenario.content_type == "silence":
                # Generate silence (very low amplitude noise)
                samples = self.generate_white_noise(
                    scenario.duration, 
                    scenario.sample_rate, 
                    amplitude=0.001
                )
            elif scenario.content_type == "noise":
                # Generate white noise
                samples = self.generate_white_noise(
                    scenario.duration, 
                    scenario.sample_rate, 
                    amplitude=0.2
                )
            else:
                # Generate speech-like signal
                samples = self.generate_speech_like_signal(
                    scenario.duration,
                    scenario.sample_rate,
                    scenario.content_type
                )
            
            # Create WAV file
            filepath = self.create_wav_file(
                scenario.filename,
                samples,
                scenario.sample_rate,
                scenario.channels
            )
            
            generated_files[scenario.filename] = filepath
        
        # Generate iPhone-specific format files
        self._generate_iphone_format_files(generated_files)
        
        return generated_files
    
    def _generate_iphone_format_files(self, generated_files: Dict[str, str]) -> None:
        """
        Generate iPhone-specific format files.
        
        Note: This creates placeholder files with correct extensions.
        In a real implementation, you would use audio conversion libraries.
        """
        # Create placeholder files for different iPhone formats
        iphone_formats = ['.m4a', '.aac']
        
        for format_ext in iphone_formats:
            for i, (base_name, _) in enumerate(list(generated_files.items())[:3]):  # First 3 files
                if base_name.endswith('.wav'):
                    iphone_name = base_name.replace('.wav', format_ext)
                    iphone_path = os.path.join(self.output_dir, iphone_name)
                    
                    # Create placeholder file with some content
                    with open(iphone_path, 'wb') as f:
                        # Write some fake audio data that represents the format
                        if format_ext == '.m4a':
                            f.write(b'fake m4a audio data' * 1000)
                        elif format_ext == '.aac':
                            f.write(b'fake aac audio data' * 800)
                    
                    generated_files[iphone_name] = iphone_path
                    print(f"Generated iPhone format: {iphone_name}")
    
    def generate_large_files(self, count: int = 3) -> Dict[str, str]:
        """
        Generate large audio files for performance testing.
        
        Args:
            count: Number of large files to generate
            
        Returns:
            Dictionary mapping file names to paths
        """
        large_files = {}
        
        print(f"Generating {count} large test files...")
        
        for i in range(count):
            filename = f"large_test_file_{i+1}.wav"
            print(f"Generating large file: {filename}")
            
            # Generate 2-minute speech-like audio
            samples = self.generate_speech_like_signal(
                duration=120.0,  # 2 minutes
                sample_rate=44100,
                content_type="korean"
            )
            
            filepath = self.create_wav_file(
                filename,
                samples,
                sample_rate=44100,
                channels=1
            )
            
            large_files[filename] = filepath
            
            # Print file size
            file_size = os.path.getsize(filepath) / (1024 * 1024)  # MB
            print(f"  Created: {filename} ({file_size:.1f} MB)")
        
        return large_files
    
    def create_test_manifest(self, generated_files: Dict[str, str]) -> str:
        """
        Create a manifest file describing all generated test files.
        
        Args:
            generated_files: Dictionary of generated files
            
        Returns:
            Path to manifest file
        """
        manifest_path = os.path.join(self.output_dir, "test_manifest.txt")
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write("# Test Audio Files Manifest\n")
            f.write(f"# Generated in: {self.output_dir}\n")
            f.write("# Format: filename | format | duration | content_type | expected_text\n\n")
            
            for scenario in self.test_scenarios:
                if scenario.filename in generated_files:
                    f.write(f"{scenario.filename} | {scenario.format} | "
                           f"{scenario.duration}s | {scenario.content_type} | "
                           f"{scenario.expected_text or 'N/A'}\n")
            
            # Add iPhone format files
            for filename in generated_files:
                if filename.endswith(('.m4a', '.aac')) and filename not in [s.filename for s in self.test_scenarios]:
                    f.write(f"{filename} | iPhone format | simulated | speech-like | N/A\n")
        
        print(f"Created test manifest: {manifest_path}")
        return manifest_path
    
    def cleanup(self) -> None:
        """Clean up generated test files."""
        import shutil
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
            print(f"Cleaned up test files in: {self.output_dir}")


def main():
    """Main function to generate test data."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate test audio data")
    parser.add_argument("--output-dir", help="Output directory for test files")
    parser.add_argument("--large-files", type=int, default=0, 
                       help="Number of large files to generate")
    parser.add_argument("--cleanup", action="store_true", 
                       help="Clean up generated files")
    
    args = parser.parse_args()
    
    generator = TestDataGenerator(args.output_dir)
    
    if args.cleanup:
        generator.cleanup()
        return
    
    try:
        # Generate standard test files
        generated_files = generator.generate_test_files()
        
        # Generate large files if requested
        if args.large_files > 0:
            large_files = generator.generate_large_files(args.large_files)
            generated_files.update(large_files)
        
        # Create manifest
        manifest_path = generator.create_test_manifest(generated_files)
        
        print(f"\nGenerated {len(generated_files)} test files")
        print(f"Output directory: {generator.output_dir}")
        print(f"Manifest file: {manifest_path}")
        
        # Print summary
        print("\nGenerated files:")
        for filename, filepath in generated_files.items():
            file_size = os.path.getsize(filepath) / 1024  # KB
            print(f"  {filename} ({file_size:.1f} KB)")
    
    except KeyboardInterrupt:
        print("\nGeneration interrupted by user")
        generator.cleanup()
    except Exception as e:
        print(f"Error generating test data: {e}")
        generator.cleanup()
        raise


if __name__ == "__main__":
    main()