#!/usr/bin/env python3
"""Test script to verify the book tracker setup without requiring API keys."""

import sys
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")

    try:
        import click
        print("✓ click imported")
    except ImportError as e:
        print(f"✗ Failed to import click: {e}")
        return False

    try:
        import yaml
        print("✓ yaml imported")
    except ImportError as e:
        print(f"✗ Failed to import yaml: {e}")
        return False

    try:
        from PIL import Image
        print("✓ PIL (Pillow) imported")
    except ImportError as e:
        print(f"✗ Failed to import PIL: {e}")
        return False

    try:
        import openai
        print("✓ openai imported")
    except ImportError as e:
        print(f"✗ Failed to import openai: {e}")
        return False

    try:
        import anthropic
        print("✓ anthropic imported")
    except ImportError as e:
        print(f"✗ Failed to import anthropic: {e}")
        return False

    try:
        import google.generativeai
        print("✓ google.generativeai imported")
    except ImportError as e:
        print(f"✗ Failed to import google.generativeai: {e}")
        return False

    return True


def test_local_modules():
    """Test that local modules can be imported."""
    print("\nTesting local modules...")

    try:
        import database
        print("✓ database module imported")
    except ImportError as e:
        print(f"✗ Failed to import database: {e}")
        return False

    try:
        import llm_providers
        print("✓ llm_providers module imported")
    except ImportError as e:
        print(f"✗ Failed to import llm_providers: {e}")
        return False

    try:
        import image_processor
        print("✓ image_processor module imported")
    except ImportError as e:
        print(f"✗ Failed to import image_processor: {e}")
        return False

    try:
        import book_manager
        print("✓ book_manager module imported")
    except ImportError as e:
        print(f"✗ Failed to import book_manager: {e}")
        return False

    return True


def test_config():
    """Test that config.yaml exists and can be parsed."""
    print("\nTesting configuration...")

    config_path = Path("config.yaml")
    if not config_path.exists():
        print("✗ config.yaml not found")
        return False

    print("✓ config.yaml exists")

    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        print("✓ config.yaml is valid YAML")

        # Check structure
        if 'llm' in config and 'database' in config and 'settings' in config:
            print("✓ config.yaml has required sections")
        else:
            print("✗ config.yaml missing required sections")
            return False

    except Exception as e:
        print(f"✗ Failed to parse config.yaml: {e}")
        return False

    return True


def test_directories():
    """Test that required directories exist."""
    print("\nTesting directories...")

    books_read = Path("books_read")
    books_to_read = Path("books_to_read")

    if books_read.exists():
        print(f"✓ books_read directory exists")
        images = list(books_read.glob("*.jpg")) + list(books_read.glob("*.jpeg")) + list(books_read.glob("*.png"))
        print(f"  Found {len(images)} image(s)")
    else:
        print("✗ books_read directory not found")
        return False

    if books_to_read.exists():
        print(f"✓ books_to_read directory exists")
        images = list(books_to_read.glob("*.jpg")) + list(books_to_read.glob("*.jpeg")) + list(books_to_read.glob("*.png"))
        print(f"  Found {len(images)} image(s)")
    else:
        print("✗ books_to_read directory not found")
        return False

    return True


def test_database_creation():
    """Test that database can be created."""
    print("\nTesting database...")

    try:
        from database import Database
        db = Database("test_books.db")
        print("✓ Database created successfully")

        # Clean up test database
        Path("test_books.db").unlink(missing_ok=True)
        print("✓ Database test cleanup complete")

        return True
    except Exception as e:
        print(f"✗ Failed to create database: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Book Tracker Setup Verification")
    print("=" * 60)

    results = []

    results.append(("Dependencies", test_imports()))
    results.append(("Local Modules", test_local_modules()))
    results.append(("Configuration", test_config()))
    results.append(("Directories", test_directories()))
    results.append(("Database", test_database_creation()))

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✓ All tests passed!")
        print("\nNext steps:")
        print("1. Edit config.yaml and add your API key")
        print("2. Run: python3 book_tracker.py --help")
        print("3. Try: python3 book_tracker.py categories list")
        return 0
    else:
        print("\n✗ Some tests failed. Please install missing dependencies:")
        print("   pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
