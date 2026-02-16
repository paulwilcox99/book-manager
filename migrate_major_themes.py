#!/usr/bin/env python3
"""
Migration script to assign major themes to all existing books.
Run once to populate the major_theme field based on existing themes.
"""

import sqlite3
import json
from theme_categories import get_major_theme

DB_FILE = "books.db"

def migrate():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all books with themes
    cursor.execute("SELECT id, title, themes FROM books WHERE themes IS NOT NULL AND themes != '[]'")
    books = cursor.fetchall()
    
    updated = 0
    skipped = 0
    
    for book in books:
        try:
            themes_list = json.loads(book['themes'])
            major_theme = get_major_theme(themes_list)
            
            if major_theme:
                cursor.execute(
                    "UPDATE books SET major_theme = ? WHERE id = ?",
                    (major_theme, book['id'])
                )
                updated += 1
                print(f"✓ {book['title'][:50]:<50} → {major_theme}")
            else:
                skipped += 1
                print(f"✗ {book['title'][:50]:<50} → No matching major theme")
        except json.JSONDecodeError:
            skipped += 1
            print(f"✗ {book['title'][:50]:<50} → Invalid themes JSON")
    
    conn.commit()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"Migration complete!")
    print(f"  Updated: {updated} books")
    print(f"  Skipped: {skipped} books")

if __name__ == "__main__":
    migrate()
