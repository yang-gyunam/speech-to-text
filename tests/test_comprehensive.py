#!/usr/bin/env python3
"""
Comprehensive test suite runner for speech-to-text processing.

This module provides a comprehensive test runner that includes all test categories:
- Unit tests
- Integration tests
- End-to-end tests
- Performance tests
- Korean language accuracy tests
- iPhone format compatibility tests
"""

import os
import sys
import time
import unittest
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import test modules
try:
    from test_performance import (
        TestModelCache, TestTempFileManager, TestPerformanceOptimizations,
        TestSpeechToTextAppPerformance, TestPerformanceBenchmarks
    )
    from test_end_to_end import (
        TestEndToEndWorkflow, TestKoreanLanguageAccuracy,
        TestiPhoneRecordingFormats, TestPerformanceRegression
    )
except ImportError as e:
    print(f"Warning: Could not import all test modules: {e}")
    # Define empty test classes as fallback
    class TestModelCache(unittest.TestCase): pass
    class TestTempFileManager(unittest.TestCase): pass
    class TestPerformanceOptimizations(unittest.TestCase): pass
    class TestSpeechToTextAppPerformance(unittest.TestCase): pass
    class TestPerformanceBenchmarks(unittest.TestCase): pass
    class TestEndToEndWorkflow(unittest.TestCase): pass
    class TestKoreanLanguageAccuracy(unittest.TestCase): pass
    class TestiPhoneRecordingFormats(unittest.TestCase): pass
    class TestPerformanceRegression(unittest.TestCase): pass


@dataclass
class TestResult:
    """Result of a test suite run."""
    suite_name: str
    tests_run: int
    failures: int
    errors: int
    skipped: int
    duration: float
    success_rate: float


class ComprehensiveTestRunner:
    """Comprehensive test runner for all test categories."""
    
    def __init__(self, verbose: bool = True):
        """
        Initialize the comprehensive test runner.
        
        Args:
            verbose: Whether to run tests in verbose mode
        """
        self.verbose = verbose
        self.results: List[TestResult] = []
        
        # Test suites to run
        self.test_suites = {
            "Model Cache Tests": [
                TestModelCache
            ],
            "Temp File Management Tests": [
                TestTempFileManager
            ],
            "Performance Optimization Tests": [
                TestPerformanceOptimizations,
                TestSpeechToTextAppPerformance
            ],
            "End-to-End Workflow Tests": [
                TestEndToEndWorkflow
            ],
            "Korean Language Tests": [
                TestKoreanLanguageAccuracy
            ],
            "iPhone Format Tests": [
                TestiPhoneRecordingFormats
            ],
            "Performance Regression Tests": [
                TestPerformanceRegression
            ],
            "Performance Benchmarks": [
                TestPerformanceBenchmarks
            ]
        }
    
    def run_test_suite(self, suite_name: str, test_classes: List[type]) -> TestResult:
        """
        Run a specific test suite.
        
        Args:
            suite_name: Name of the test suite
            test_classes: List of test classes to run
            
        Returns:
            TestResult with suite results
        """
        print(f"\n{'='*60}")
        print(f"Running {suite_name}")
        print(f"{'='*60}")
        
        # Create test suite
        suite = unittest.TestSuite()
        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        # Run tests
        start_time = time.time()
        
        if self.verbose:
            runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        else:
            runner = unittest.TextTestRunner(verbosity=1, stream=sys.stdout)
        
        result = runner.run(suite)
        
        duration = time.time() - start_time
        
        # Calculate success rate
        total_tests = result.testsRun
        failures_and_errors = len(result.failures) + len(result.errors)
        success_rate = ((total_tests - failures_and_errors) / total_tests * 100) if total_tests > 0 else 0
        
        test_result = TestResult(
            suite_name=suite_name,
            tests_run=result.testsRun,
            failures=len(result.failures),
            errors=len(result.errors),
            skipped=len(result.skipped),
            duration=duration,
            success_rate=success_rate
        )
        
        self.results.append(test_result)
        
        print(f"\n{suite_name} Results:")
        print(f"  Tests run: {test_result.tests_run}")
        print(f"  Failures: {test_result.failures}")
        print(f"  Errors: {test_result.errors}")
        print(f"  Skipped: {test_result.skipped}")
        print(f"  Duration: {test_result.duration:.2f}s")
        print(f"  Success rate: {test_result.success_rate:.1f}%")
        
        return test_result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all test suites.
        
        Returns:
            Dictionary with overall test results
        """
        print("Starting Comprehensive Test Suite")
        print(f"Python version: {sys.version}")
        print(f"Test runner: {self.__class__.__name__}")
        
        overall_start_time = time.time()
        
        # Run each test suite
        for suite_name, test_classes in self.test_suites.items():
            try:
                self.run_test_suite(suite_name, test_classes)
            except Exception as e:
                print(f"Error running {suite_name}: {e}")
                # Create a failed result
                failed_result = TestResult(
                    suite_name=suite_name,
                    tests_run=0,
                    failures=0,
                    errors=1,
                    skipped=0,
                    duration=0.0,
                    success_rate=0.0
                )
                self.results.append(failed_result)
        
        overall_duration = time.time() - overall_start_time
        
        # Generate summary
        summary = self._generate_summary(overall_duration)
        self._print_summary(summary)
        
        return summary
    
    def _generate_summary(self, overall_duration: float) -> Dict[str, Any]:
        """
        Generate test summary.
        
        Args:
            overall_duration: Total test duration
            
        Returns:
            Dictionary with summary information
        """
        total_tests = sum(r.tests_run for r in self.results)
        total_failures = sum(r.failures for r in self.results)
        total_errors = sum(r.errors for r in self.results)
        total_skipped = sum(r.skipped for r in self.results)
        
        overall_success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100) if total_tests > 0 else 0
        
        # Find best and worst performing suites
        best_suite = max(self.results, key=lambda r: r.success_rate) if self.results else None
        worst_suite = min(self.results, key=lambda r: r.success_rate) if self.results else None
        
        # Calculate performance metrics
        avg_duration = sum(r.duration for r in self.results) / len(self.results) if self.results else 0
        
        return {
            "overall_duration": overall_duration,
            "total_suites": len(self.results),
            "total_tests": total_tests,
            "total_failures": total_failures,
            "total_errors": total_errors,
            "total_skipped": total_skipped,
            "overall_success_rate": overall_success_rate,
            "best_suite": best_suite,
            "worst_suite": worst_suite,
            "average_suite_duration": avg_duration,
            "suite_results": self.results
        }
    
    def _print_summary(self, summary: Dict[str, Any]) -> None:
        """
        Print comprehensive test summary.
        
        Args:
            summary: Summary dictionary
        """
        print(f"\n{'='*80}")
        print("COMPREHENSIVE TEST SUMMARY")
        print(f"{'='*80}")
        
        print(f"Overall Duration: {summary['overall_duration']:.2f}s")
        print(f"Total Test Suites: {summary['total_suites']}")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Total Failures: {summary['total_failures']}")
        print(f"Total Errors: {summary['total_errors']}")
        print(f"Total Skipped: {summary['total_skipped']}")
        print(f"Overall Success Rate: {summary['overall_success_rate']:.1f}%")
        
        if summary['best_suite']:
            print(f"Best Performing Suite: {summary['best_suite'].suite_name} "
                  f"({summary['best_suite'].success_rate:.1f}%)")
        
        if summary['worst_suite']:
            print(f"Worst Performing Suite: {summary['worst_suite'].suite_name} "
                  f"({summary['worst_suite'].success_rate:.1f}%)")
        
        print(f"Average Suite Duration: {summary['average_suite_duration']:.2f}s")
        
        # Detailed suite results
        print(f"\nDetailed Suite Results:")
        print(f"{'Suite Name':<35} {'Tests':<6} {'Fail':<5} {'Err':<4} {'Skip':<5} {'Rate':<6} {'Time':<8}")
        print("-" * 80)
        
        for result in summary['suite_results']:
            print(f"{result.suite_name:<35} {result.tests_run:<6} {result.failures:<5} "
                  f"{result.errors:<4} {result.skipped:<5} {result.success_rate:<6.1f}% "
                  f"{result.duration:<8.2f}s")
        
        # Overall assessment
        print(f"\nOverall Assessment:")
        if summary['overall_success_rate'] >= 95:
            print("✅ EXCELLENT - All systems performing well")
        elif summary['overall_success_rate'] >= 85:
            print("✅ GOOD - Minor issues detected")
        elif summary['overall_success_rate'] >= 70:
            print("⚠️  WARNING - Significant issues detected")
        else:
            print("❌ CRITICAL - Major issues require attention")
        
        # Recommendations
        print(f"\nRecommendations:")
        if summary['total_failures'] > 0:
            print(f"- Address {summary['total_failures']} test failures")
        if summary['total_errors'] > 0:
            print(f"- Fix {summary['total_errors']} test errors")
        if summary['total_skipped'] > 0:
            print(f"- Review {summary['total_skipped']} skipped tests")
        
        # Performance insights
        slow_suites = [r for r in summary['suite_results'] if r.duration > summary['average_suite_duration'] * 2]
        if slow_suites:
            print(f"- Consider optimizing slow test suites: {', '.join(s.suite_name for s in slow_suites)}")
    
    def run_specific_categories(self, categories: List[str]) -> Dict[str, Any]:
        """
        Run specific test categories.
        
        Args:
            categories: List of category names to run
            
        Returns:
            Dictionary with test results
        """
        filtered_suites = {name: classes for name, classes in self.test_suites.items() 
                          if any(cat.lower() in name.lower() for cat in categories)}
        
        if not filtered_suites:
            print(f"No test suites found matching categories: {categories}")
            return {}
        
        # Temporarily replace test suites
        original_suites = self.test_suites
        self.test_suites = filtered_suites
        
        try:
            return self.run_all_tests()
        finally:
            self.test_suites = original_suites


def main():
    """Main function to run comprehensive tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run comprehensive test suite")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Run tests in verbose mode")
    parser.add_argument("--categories", nargs="+", 
                       help="Specific test categories to run")
    parser.add_argument("--quick", action="store_true",
                       help="Run quick tests only (skip performance benchmarks)")
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner(verbose=args.verbose)
    
    if args.quick:
        # Skip performance benchmarks for quick runs
        if "Performance Benchmarks" in runner.test_suites:
            del runner.test_suites["Performance Benchmarks"]
    
    try:
        if args.categories:
            summary = runner.run_specific_categories(args.categories)
        else:
            summary = runner.run_all_tests()
        
        # Exit with appropriate code
        if summary.get('overall_success_rate', 0) >= 95:
            sys.exit(0)  # Success
        elif summary.get('total_errors', 0) > 0:
            sys.exit(2)  # Errors
        else:
            sys.exit(1)  # Failures
    
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error running comprehensive tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()