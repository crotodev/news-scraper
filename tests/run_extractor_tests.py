#!/usr/bin/env python3
"""
Test runner for extractor tests.

This script helps run extractor tests and reports which fixtures are missing.
"""

import sys
from pathlib import Path


def check_fixtures():
    """Check which HTML fixtures are present."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    required_fixtures = [
        "ap.html",
        "bbc.html",
        "cbs.html",
        "cnn.html",
        "foxnews.html",
        "guardian.html",
        "nbc.html",
        "nyt.html",
    ]

    print("Checking for HTML fixtures...")
    print(f"Fixtures directory: {fixtures_dir}")
    print()

    missing = []
    present = []

    for fixture in required_fixtures:
        fixture_path = fixtures_dir / fixture
        if fixture_path.exists():
            size = fixture_path.stat().st_size
            present.append(f"✅ {fixture} ({size:,} bytes)")
        else:
            missing.append(f"❌ {fixture}")

    if present:
        print("Present fixtures:")
        for item in present:
            print(f"  {item}")
        print()

    if missing:
        print("Missing fixtures:")
        for item in missing:
            print(f"  {item}")
        print()
        print("Tests will skip extractors with missing fixtures.")
        print("See tests/fixtures/README.md for instructions.")
        print()

    return len(missing)


def main():
    """Run extractor tests with fixture checking."""
    import pytest

    print("=" * 70)
    print("EXTRACTOR TEST RUNNER")
    print("=" * 70)
    print()

    missing_count = check_fixtures()

    print("=" * 70)
    print("Running tests...")
    print("=" * 70)
    print()

    # Run pytest on extractors directory
    test_dir = Path(__file__).parent / "extractors"

    # Build pytest args
    args = [
        str(test_dir),
        "-v",  # Verbose
        "--tb=short",  # Short traceback
    ]

    # Add any command line args passed to this script
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])

    exit_code = pytest.main(args)

    print()
    print("=" * 70)
    if missing_count > 0:
        print(f"Note: {missing_count} fixture(s) missing - some tests were skipped")
    print("=" * 70)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
