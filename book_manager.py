import re
from typing import Dict, Any, List, Optional, Tuple
from database import Database
from llm_providers import LLMProvider


class BookManager:
    def __init__(self, db: Database, llm_provider: LLMProvider, config: Dict[str, Any]):
        self.db = db
        self.llm_provider = llm_provider
        self.config = config

    def normalize_string(self, s: str) -> str:
        """Normalize string for comparison (lowercase, remove punctuation, trim)."""
        s = s.lower().strip()
        s = re.sub(r'[^\w\s]', '', s)
        s = re.sub(r'\s+', ' ', s)
        return s

    def find_duplicate(self, title: str, authors: List[str]) -> Optional[Dict[str, Any]]:
        """Check if book already exists using fuzzy matching."""
        normalized_title = self.normalize_string(title)
        normalized_authors = sorted([self.normalize_string(a) for a in authors])

        all_books = self.db.search_books({})

        for book in all_books:
            book_title = self.normalize_string(book['title'])
            book_authors = sorted([self.normalize_string(a) for a in book['authors']])

            if book_title == normalized_title and book_authors == normalized_authors:
                return book

        return None

    def add_book(self, book_data: Dict[str, Any], source: str = 'manual', auto_enrich: bool = None) -> Tuple[int, str]:
        """
        Add a new book to the database.
        Returns (book_id, status) where status is 'added', 'updated', or 'skipped'.
        """
        # Check for duplicates
        duplicate = self.find_duplicate(book_data['title'], book_data['authors'])

        if duplicate:
            return duplicate['id'], 'duplicate'

        # Add the book
        book_id = self.db.add_book(book_data)

        # Auto-enrich if enabled
        should_enrich = auto_enrich if auto_enrich is not None else self.config['settings'].get('auto_enrich', True)

        if should_enrich:
            try:
                self.enrich_book(book_id, force=False)
            except Exception as e:
                print(f"Warning: Failed to enrich book: {e}")

        return book_id, 'added'

    def enrich_book(self, book_id: int, force: bool = False) -> Dict[str, Any]:
        """
        Enrich a book with LLM metadata.
        If force=False, only fetch fields that are empty/null.
        If force=True, re-fetch all fields.
        """
        book = self.db.get_book(book_id)
        if not book:
            raise ValueError(f"Book with ID {book_id} not found")

        # Determine which fields need enrichment
        enrichable_fields = [
            'publication_date', 'isbn', 'fiction_nonfiction', 'synopsis',
            'themes', 'main_characters', 'quotes', 'awards', 'llm_categories'
        ]

        if force:
            missing_fields = None  # Fetch all fields
        else:
            missing_fields = []
            for field in enrichable_fields:
                value = book.get(field)
                if value is None or value == '' or (isinstance(value, list) and len(value) == 0):
                    missing_fields.append(field)

            if not missing_fields:
                return book  # Nothing to enrich

        # Call LLM for enrichment
        print(f"Enriching book: {book['title']} by {', '.join(book['authors'])}")
        enriched_data = self.llm_provider.enrich_book_info(
            book['title'],
            book['authors'],
            missing_fields=missing_fields
        )

        # Update only the fields that were fetched
        updates = {}
        for field, value in enriched_data.items():
            if force or field in (missing_fields or enrichable_fields):
                updates[field] = value

        # Match against user categories if we have synopsis
        synopsis = updates.get('synopsis') or book.get('synopsis')
        if synopsis and self.config['settings'].get('user_categories'):
            print("Matching user categories...")
            user_cats = self.llm_provider.match_user_categories(
                book['title'],
                book['authors'],
                synopsis,
                self.config['settings']['user_categories']
            )
            updates['user_categories'] = user_cats

        # Update the database
        if updates:
            self.db.update_book(book_id, updates)

        # Return updated book
        return self.db.get_book(book_id)

    def update_book(self, book_id: int, updates: Dict[str, Any]):
        """Update an existing book."""
        self.db.update_book(book_id, updates)

    def get_book(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Get a book by ID."""
        return self.db.get_book(book_id)

    def get_book_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """Get a book by title."""
        return self.db.get_book_by_title(title)

    def search_books(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search books with filters."""
        return self.db.search_books(filters)

    def format_book_display(self, book: Dict[str, Any], detailed: bool = False) -> str:
        """Format book information for display."""
        output = []
        output.append(f"ID: {book['id']}")
        output.append(f"Title: {book['title']}")
        output.append(f"Authors: {', '.join(book['authors'])}")
        output.append(f"Status: {book['read_status']}")

        if book.get('rating'):
            output.append(f"Rating: {book['rating']}/10")

        if detailed:
            if book.get('publication_date'):
                output.append(f"Publication Date: {book['publication_date']}")

            if book.get('isbn'):
                output.append(f"ISBN: {book['isbn']}")

            if book.get('fiction_nonfiction'):
                output.append(f"Type: {book['fiction_nonfiction']}")

            if book.get('synopsis'):
                output.append(f"Synopsis: {book['synopsis']}")

            if book.get('themes') and len(book['themes']) > 0:
                output.append(f"Themes: {', '.join(book['themes'])}")

            if book.get('main_characters') and len(book['main_characters']) > 0:
                output.append(f"Main Characters: {', '.join(book['main_characters'])}")

            if book.get('quotes') and len(book['quotes']) > 0:
                output.append("Quotes:")
                for quote in book['quotes']:
                    output.append(f"  - {quote}")

            if book.get('awards') and len(book['awards']) > 0:
                output.append(f"Awards: {', '.join(book['awards'])}")

            if book.get('llm_categories') and len(book['llm_categories']) > 0:
                output.append(f"Categories: {', '.join(book['llm_categories'])}")

            if book.get('user_categories') and len(book['user_categories']) > 0:
                output.append(f"User Categories: {', '.join(book['user_categories'])}")

            if book.get('personal_notes'):
                output.append(f"Notes: {book['personal_notes']}")

            if book.get('source_image_path'):
                output.append(f"Source Image: {book['source_image_path']}")

            output.append(f"Date Added: {book['date_added']}")

        return "\n".join(output)
