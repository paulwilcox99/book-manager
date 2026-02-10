import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, List, Any


class Database:
    def __init__(self, db_path: str = "books.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database with schema."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create books table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT NOT NULL,
                read_status TEXT CHECK(read_status IN ('read', 'to_read')) NOT NULL,
                rating INTEGER CHECK(rating >= 1 AND rating <= 10),
                date_added TEXT NOT NULL,
                personal_notes TEXT,

                publication_date TEXT,
                isbn TEXT,
                fiction_nonfiction TEXT,
                synopsis TEXT,
                themes TEXT,
                main_characters TEXT,
                quotes TEXT,
                awards TEXT,
                llm_categories TEXT,
                user_categories TEXT,

                source_image_path TEXT,
                last_updated TEXT NOT NULL,

                UNIQUE(title, authors)
            )
        """)

        # Create processed_images table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT UNIQUE NOT NULL,
                processed_date TEXT NOT NULL,
                books_extracted INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()

    def add_book(self, book_data: Dict[str, Any]) -> int:
        """Add a new book to the database."""
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()
        book_data['date_added'] = now
        book_data['last_updated'] = now

        # Convert lists to JSON strings
        for field in ['authors', 'themes', 'main_characters', 'quotes', 'awards', 'llm_categories', 'user_categories']:
            if field in book_data and isinstance(book_data[field], list):
                book_data[field] = json.dumps(book_data[field])

        columns = ', '.join(book_data.keys())
        placeholders = ', '.join(['?' for _ in book_data])

        cursor.execute(
            f"INSERT INTO books ({columns}) VALUES ({placeholders})",
            list(book_data.values())
        )

        book_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return book_id

    def update_book(self, book_id: int, updates: Dict[str, Any]):
        """Update an existing book."""
        conn = self.get_connection()
        cursor = conn.cursor()

        updates['last_updated'] = datetime.now().isoformat()

        # Convert lists to JSON strings
        for field in ['authors', 'themes', 'main_characters', 'quotes', 'awards', 'llm_categories', 'user_categories']:
            if field in updates and isinstance(updates[field], list):
                updates[field] = json.dumps(updates[field])

        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])

        cursor.execute(
            f"UPDATE books SET {set_clause} WHERE id = ?",
            list(updates.values()) + [book_id]
        )

        conn.commit()
        conn.close()

    def get_book(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Get a book by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        row = cursor.fetchone()

        conn.close()

        if row:
            return self._row_to_dict(row)
        return None

    def get_book_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """Get a book by title (exact match)."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM books WHERE title = ?", (title,))
        row = cursor.fetchone()

        conn.close()

        if row:
            return self._row_to_dict(row)
        return None

    def search_books(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search books with various filters."""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM books WHERE 1=1"
        params = []

        if 'title' in filters:
            query += " AND title LIKE ?"
            params.append(f"%{filters['title']}%")

        if 'author' in filters:
            query += " AND authors LIKE ?"
            params.append(f"%{filters['author']}%")

        if 'read_status' in filters:
            query += " AND read_status = ?"
            params.append(filters['read_status'])

        if 'rating_min' in filters:
            query += " AND rating >= ?"
            params.append(filters['rating_min'])

        if 'rating_max' in filters:
            query += " AND rating <= ?"
            params.append(filters['rating_max'])

        if 'category' in filters:
            query += " AND llm_categories LIKE ?"
            params.append(f"%{filters['category']}%")

        if 'user_category' in filters:
            query += " AND user_categories LIKE ?"
            params.append(f"%{filters['user_category']}%")

        if 'sort_by' in filters:
            sort_field = filters['sort_by']
            query += f" ORDER BY {sort_field}"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        conn.close()

        return [self._row_to_dict(row) for row in rows]

    def mark_image_processed(self, image_path: str, books_extracted: int):
        """Mark an image as processed."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT OR REPLACE INTO processed_images (image_path, processed_date, books_extracted) VALUES (?, ?, ?)",
            (image_path, datetime.now().isoformat(), books_extracted)
        )

        conn.commit()
        conn.close()

    def is_image_processed(self, image_path: str) -> bool:
        """Check if an image has been processed."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM processed_images WHERE image_path = ?", (image_path,))
        result = cursor.fetchone()

        conn.close()

        return result is not None

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a database row to a dictionary with JSON fields parsed."""
        book = dict(row)

        # Parse JSON fields
        for field in ['authors', 'themes', 'main_characters', 'quotes', 'awards', 'llm_categories', 'user_categories']:
            if book.get(field):
                try:
                    book[field] = json.loads(book[field])
                except json.JSONDecodeError:
                    book[field] = []

        return book
