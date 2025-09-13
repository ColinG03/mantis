#!/usr/bin/env python3
"""
Test runner for Gemini analyzer tests.

This script provides an easy way to run the Gemini analyzer tests with different configurations.
"""
import subprocess
import sys
import os
from pathlib import Path


def run_tests(test_pattern=None, verbose=False, coverage=False, performance=False):
    """
    Run the Gemini analyzer tests.
    
    Args:
        test_pattern: Optional pattern to filter tests (e.g., "test_init" or "TestGeminiAnalyzer")
        verbose: Enable verbose output
        coverage: Run with coverage reporting
        performance: Include performance tests (slower)
    """
    # Change to the project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Base pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add test files
    test_files = ["src/tests/test_gemini_analyzer.py"]
    if performance:
        test_files.append("src/tests/test_gemini_performance.py")
    
    cmd.extend(test_files)
    
    # Add options
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=src/inspector/utils/gemini_analyzer",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
    
    if test_pattern:
        cmd.extend(["-k", test_pattern])
    
    # Add some useful pytest options
    cmd.extend([
        "--tb=short",  # Shorter traceback format
        "-ra",         # Show summary of all tests
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    print("-" * 60)
    
    # Run the tests
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def main():
    """Main entry point for the test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Gemini analyzer tests")
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose output"
    )
    parser.add_argument(
        "-c", "--coverage",
        action="store_true",
        help="Run with coverage reporting"
    )
    parser.add_argument(
        "-p", "--performance",
        action="store_true", 
        help="Include performance tests (slower)"
    )
    parser.add_argument(
        "-k", "--pattern",
        help="Run only tests matching the given pattern"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick test run (unit tests only, no performance tests)"
    )
    
    args = parser.parse_args()
    
    # Quick mode overrides performance
    if args.quick:
        performance = False
    else:
        performance = args.performance
    
    return_code = run_tests(
        test_pattern=args.pattern,
        verbose=args.verbose,
        coverage=args.coverage,
        performance=performance
    )
    
    if return_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with return code {return_code}")
    
    return return_code


if __name__ == "__main__":
    sys.exit(main())
