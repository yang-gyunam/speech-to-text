#!/usr/bin/env python3
"""
Performance benchmark script for speech-to-text processing.

This script provides comprehensive benchmarks for various performance aspects
including model loading, memory usage, and processing speed.
"""

import gc
import os
import sys
import time
import psutil
import tempfile
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from contextlib import contextmanager

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from speech_to_text.transcriber import SpeechTranscriber, ModelCache
from speech_to_text.main_app import SpeechToTextApp, TempFileManager


@dataclass
class BenchmarkResult:
    """Result of a benchmark test."""
    name: str
    duration: float
    memory_before: float
    memory_after: float
    memory_peak: float
    success: bool
    error_message: str = ""
    additional_metrics: Dict[str, Any] = None


class PerformanceBenchmark:
    """Performance benchmark suite for speech-to-text processing."""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.process = psutil.Process()
    
    @contextmanager
    def measure_performance(self, test_name: str):
        """Context manager to measure performance metrics."""
        # Force garbage collection before measurement
        gc.collect()
        
        # Get initial memory usage
        memory_before = self.process.memory_info().rss / 1024 / 1024  # MB
        peak_memory = memory_before
        
        start_time = time.time()
        success = True
        error_message = ""
        additional_metrics = {}
        
        try:
            yield additional_metrics
        except Exception as e:
            success = False
            error_message = str(e)
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            # Get final memory usage
            memory_after = self.process.memory_info().rss / 1024 / 1024  # MB
            peak_memory = max(peak_memory, memory_after)
            
            result = BenchmarkResult(
                name=test_name,
                duration=duration,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_peak=peak_memory,
                success=success,
                error_message=error_message,
                additional_metrics=additional_metrics
            )
            
            self.results.append(result)
            print(f"✓ {test_name}: {duration:.3f}s, "
                  f"Memory: {memory_before:.1f}MB → {memory_after:.1f}MB "
                  f"(Peak: {peak_memory:.1f}MB)")
            
            if not success:
                print(f"  ✗ Error: {error_message}")
    
    def benchmark_model_cache(self):
        """Benchmark model caching performance."""
        print("\n=== Model Cache Benchmarks ===")
        
        # Clear any existing cache
        cache = ModelCache()
        cache.clear_cache()
        
        # Benchmark: First model load (no cache)
        with self.measure_performance("Model Load - First Time (Base)"):
            try:
                transcriber = SpeechTranscriber(model_size="base", use_cache=True)
                # Simulate model usage
                _ = transcriber.model
            except Exception as e:
                print(f"Skipping model load test (Whisper not available): {e}")
                return
        
        # Benchmark: Second model load (from cache)
        with self.measure_performance("Model Load - From Cache (Base)") as metrics:
            transcriber2 = SpeechTranscriber(model_size="base", use_cache=True)
            cache_info = transcriber2.get_cache_info()
            metrics["cache_size"] = cache_info.get("cache_size", 0)
            metrics["cached_models"] = len(cache_info.get("cached_models", []))
        
        # Benchmark: Different model load
        with self.measure_performance("Model Load - Different Model (Small)"):
            transcriber3 = SpeechTranscriber(model_size="small", use_cache=True)
            _ = transcriber3.model
        
        # Benchmark: Cache clearing
        with self.measure_performance("Cache Clear") as metrics:
            cache_info_before = cache.get_cache_info()
            cache.clear_cache()
            cache_info_after = cache.get_cache_info()
            metrics["models_cleared"] = cache_info_before.get("cache_size", 0)
            metrics["final_cache_size"] = cache_info_after.get("cache_size", 0)
    
    def benchmark_temp_file_management(self):
        """Benchmark temporary file management."""
        print("\n=== Temporary File Management Benchmarks ===")
        
        # Benchmark: Creating temporary files
        with self.measure_performance("Create 100 Temp Files") as metrics:
            temp_manager = TempFileManager()
            temp_files = []
            
            for i in range(100):
                temp_file = temp_manager.create_temp_file(
                    suffix=f"_{i}.tmp",
                    prefix="benchmark_"
                )
                temp_files.append(temp_file)
            
            metrics["files_created"] = len(temp_files)
            metrics["temp_count"] = temp_manager.get_temp_count()
            
            # Verify files exist
            existing_files = sum(1 for f in temp_files if os.path.exists(f))
            metrics["files_existing"] = existing_files
        
        # Benchmark: Cleaning up temporary files
        with self.measure_performance("Cleanup 100 Temp Files") as metrics:
            files_before = temp_manager.get_temp_count()
            temp_manager.cleanup()
            files_after = temp_manager.get_temp_count()
            
            metrics["files_before"] = files_before
            metrics["files_after"] = files_after
            metrics["files_cleaned"] = files_before - files_after
            
            # Verify files are removed
            remaining_files = sum(1 for f in temp_files if os.path.exists(f))
            metrics["files_remaining"] = remaining_files
    
    def benchmark_memory_optimization(self):
        """Benchmark memory optimization features."""
        print("\n=== Memory Optimization Benchmarks ===")
        
        # Create test data
        test_data = b"fake audio data" * 1000  # Simulate larger file
        test_file = "benchmark_audio.wav"
        
        try:
            with open(test_file, 'wb') as f:
                f.write(test_data)
            
            # Benchmark: App with memory optimization disabled
            with self.measure_performance("App Creation - No Memory Optimization") as metrics:
                app1 = SpeechToTextApp(
                    model_size="base",
                    optimize_memory=False,
                    use_model_cache=False
                )
                stats = app1.get_performance_stats()
                metrics.update(stats)
                app1.close()
            
            # Benchmark: App with memory optimization enabled
            with self.measure_performance("App Creation - With Memory Optimization") as metrics:
                app2 = SpeechToTextApp(
                    model_size="base",
                    optimize_memory=True,
                    use_model_cache=True
                )
                stats = app2.get_performance_stats()
                metrics.update(stats)
                app2.close()
            
            # Benchmark: Memory optimized context manager
            with self.measure_performance("Memory Optimized Context Manager"):
                app3 = SpeechToTextApp(optimize_memory=True)
                with app3.memory_optimized_processing():
                    # Simulate some processing
                    time.sleep(0.1)
                app3.close()
            
            # Benchmark: Cache clearing
            with self.measure_performance("Cache Clearing") as metrics:
                app4 = SpeechToTextApp(use_model_cache=True)
                stats_before = app4.get_performance_stats()
                app4.clear_caches()
                stats_after = app4.get_performance_stats()
                
                metrics["cache_size_before"] = stats_before.get("cache_size", 0)
                metrics["cache_size_after"] = stats_after.get("cache_size", 0)
                app4.close()
        
        finally:
            # Clean up test file
            if os.path.exists(test_file):
                os.unlink(test_file)
    
    def benchmark_garbage_collection(self):
        """Benchmark garbage collection impact."""
        print("\n=== Garbage Collection Benchmarks ===")
        
        # Benchmark: Manual garbage collection
        with self.measure_performance("Manual Garbage Collection") as metrics:
            # Create some objects to collect
            large_objects = []
            for i in range(1000):
                large_objects.append([0] * 1000)
            
            metrics["objects_created"] = len(large_objects)
            
            # Clear references
            large_objects.clear()
            
            # Force garbage collection
            collected = gc.collect()
            metrics["objects_collected"] = collected
        
        # Benchmark: Transcriber with periodic GC
        with self.measure_performance("Transcriber with Periodic GC"):
            try:
                transcriber = SpeechTranscriber(model_size="base", use_cache=True)
                
                # Simulate batch processing with GC
                for i in range(10):
                    # Simulate some processing
                    time.sleep(0.01)
                    
                    # Periodic GC
                    if i % 3 == 0:
                        gc.collect()
                
            except Exception as e:
                print(f"Skipping transcriber GC test: {e}")
    
    def run_all_benchmarks(self):
        """Run all performance benchmarks."""
        print("Starting Performance Benchmarks...")
        print(f"Python version: {sys.version}")
        print(f"Process ID: {os.getpid()}")
        print(f"Initial memory usage: {self.process.memory_info().rss / 1024 / 1024:.1f} MB")
        
        try:
            self.benchmark_model_cache()
        except Exception as e:
            print(f"Model cache benchmarks failed: {e}")
        
        try:
            self.benchmark_temp_file_management()
        except Exception as e:
            print(f"Temp file benchmarks failed: {e}")
        
        try:
            self.benchmark_memory_optimization()
        except Exception as e:
            print(f"Memory optimization benchmarks failed: {e}")
        
        try:
            self.benchmark_garbage_collection()
        except Exception as e:
            print(f"Garbage collection benchmarks failed: {e}")
        
        self.print_summary()
    
    def print_summary(self):
        """Print benchmark summary."""
        print("\n" + "="*60)
        print("BENCHMARK SUMMARY")
        print("="*60)
        
        if not self.results:
            print("No benchmark results available.")
            return
        
        successful_tests = [r for r in self.results if r.success]
        failed_tests = [r for r in self.results if not r.success]
        
        print(f"Total tests: {len(self.results)}")
        print(f"Successful: {len(successful_tests)}")
        print(f"Failed: {len(failed_tests)}")
        
        if successful_tests:
            print(f"\nPerformance Summary:")
            print(f"{'Test Name':<40} {'Duration':<10} {'Memory Δ':<12}")
            print("-" * 62)
            
            for result in successful_tests:
                memory_delta = result.memory_after - result.memory_before
                memory_delta_str = f"{memory_delta:+.1f} MB"
                print(f"{result.name:<40} {result.duration:<10.3f} {memory_delta_str:<12}")
            
            # Calculate statistics
            durations = [r.duration for r in successful_tests]
            memory_deltas = [r.memory_after - r.memory_before for r in successful_tests]
            
            print(f"\nStatistics:")
            print(f"Average duration: {sum(durations) / len(durations):.3f}s")
            print(f"Total duration: {sum(durations):.3f}s")
            print(f"Average memory delta: {sum(memory_deltas) / len(memory_deltas):+.1f} MB")
            print(f"Max memory delta: {max(memory_deltas):+.1f} MB")
            print(f"Min memory delta: {min(memory_deltas):+.1f} MB")
        
        if failed_tests:
            print(f"\nFailed Tests:")
            for result in failed_tests:
                print(f"✗ {result.name}: {result.error_message}")
        
        print(f"\nFinal memory usage: {self.process.memory_info().rss / 1024 / 1024:.1f} MB")


def main():
    """Main function to run benchmarks."""
    benchmark = PerformanceBenchmark()
    benchmark.run_all_benchmarks()


if __name__ == "__main__":
    main()