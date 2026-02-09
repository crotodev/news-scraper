"""
Test runner for the news scraper test suite.

Run all tests with:
    python -m pytest tests/

Or with unittest:
    python -m unittest discover tests/

Run specific test file:
    python -m unittest tests/test_spiders.py

Run with coverage:
    coverage run -m pytest tests/
    coverage report
"""

import os
import sys

# Add parent directory to path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if __name__ == "__main__":
    import unittest

    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
