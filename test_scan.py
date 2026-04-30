#!/usr/bin/env python3
"""
Copies test images from test_data/ into books_read/ and books_to_read/,
runs the scan against a throw-away database, then cleans up.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
TEST_DATA_DIR = SCRIPT_DIR / "test_data"
TEST_DB = SCRIPT_DIR / "test_scan.db"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def copy_test_images():
    copied = []
    for subdir in ("books_read", "books_to_read"):
        src = TEST_DATA_DIR / subdir
        dst = SCRIPT_DIR / subdir
        if not src.exists():
            print(f"  No test_data/{subdir}/ found, skipping")
            continue
        dst.mkdir(exist_ok=True)
        for img in src.iterdir():
            if img.suffix.lower() in IMAGE_EXTENSIONS:
                dest_path = dst / img.name
                shutil.copy2(img, dest_path)
                copied.append(dest_path)
                print(f"  {img.name} -> {subdir}/")
    return copied


def cleanup(copied):
    for path in copied:
        path.unlink(missing_ok=True)
    TEST_DB.unlink(missing_ok=True)
    print(f"\nCleanup: removed {len(copied)} test image(s) and test database")


def main():
    print("=" * 60)
    print("Book Tracker - Scan Test")
    print("=" * 60)

    if not TEST_DATA_DIR.exists():
        print(f"Error: test_data/ directory not found")
        print("Create test_data/books_read/ and test_data/books_to_read/ with sample images.")
        return 1

    print("\nCopying test images...")
    copied = copy_test_images()

    if not copied:
        print("No images found in test_data/. Add .jpg/.jpeg/.png files to test.")
        return 1

    print(f"  {len(copied)} image(s) staged")

    print("\nRunning scan...\n")
    env = os.environ.copy()
    env["DATABASE_PATH"] = str(TEST_DB)

    result = subprocess.run(
        [sys.executable, "book_tracker.py", "scan"],
        env=env,
        cwd=SCRIPT_DIR,
    )

    cleanup(copied)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
