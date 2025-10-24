#!/usr/bin/env python3
"""
Test runner for ActTrader Python SDK
"""

import sys
import subprocess
import os


def run_tests():
    """Run the test suite"""
    print("Running ActTrader Python SDK tests...")
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("pytest not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"])
    
    # Run tests
    test_args = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--strict-markers"
    ]
    
    try:
        result = subprocess.run(test_args, cwd=os.path.dirname(__file__))
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
