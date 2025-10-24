#!/usr/bin/env python3
"""
Wrapper script to run CrewAI tests without deprecation warnings
"""

import warnings
import sys
import os

# Completely suppress all warnings
warnings.filterwarnings("ignore")

# Set environment variable to suppress warnings
os.environ["PYTHONWARNINGS"] = "ignore"

# Redirect stderr to suppress warnings
import contextlib
import io

class SuppressWarnings:
    def __enter__(self):
        self._original_stderr = sys.stderr
        sys.stderr = io.StringIO()
        return self
    
    def __exit__(self, *args):
        sys.stderr = self._original_stderr

# Run the test with suppressed warnings
if __name__ == "__main__":
    with SuppressWarnings():
        # Import and run the test
        from test_crewai_ollama_working import main
        main()
