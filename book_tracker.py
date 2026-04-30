#!/usr/bin/env python3
import os
import click
import json
import csv
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv, set_key

from database import Database
from llm_providers import get_provider
from image_processor import ImageProcessor
from book_manager import BookManager


def load_config():
    """Load configuration from .env."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {env_path}")

    load_dotenv(env_path)

    image_extensions = [e.strip() for e in os.getenv('IMAGE_EXTENSIONS', '.jpg,.jpeg,.png').split(',')]
    user_categories_raw = os.getenv('USER_CATEGORIES', '')
    user_categories = [c.strip() for c in user_categories_raw.split(',') if c.strip()]

    return {
        'llm': {
            'provider': os.getenv('LLM_PROVIDER', 'openai'),
            'openai_api_key': os.getenv('OPENAI_API_KEY', 'your-openai-api-key-here'),
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY', 'your-anthropic-api-key-here'),
            'google_api_key': os.getenv('GOOGLE_API_KEY', 'your-google-api-key-here'),
            'model': {
                'openai': os.getenv('OPENAI_MODEL', 'gpt-4o'),
                'anthropic': os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022'),
                'google': os.getenv('GOOGLE_MODEL', 'gemini-2.0-flash-exp'),
            }
        },
        'database': {
            'path': os.getenv('DATABASE_PATH', 'books.db'),
        },
        'directories': {
            'books_read': os.getenv('DIR_BOOKS_READ', 'books_read'),
            'books_to_read': os.getenv('DIR_BOOKS_TO_READ', 'books_to_read'),
        },
        'settings': {
            'auto_enrich': os.getenv('AUTO_ENRICH', 'true').lower() == 'true',
            'image_extensions': image_extensions,
            'user_categories': user_categories,
        }
    }


def save_config(config):
    """Persist mutable config values back to .env."""
    env_path = str(Path(__file__).parent / ".env")
    user_categories = config['settings'].get('user_categories', [])
    set_key(env_path, 'USER_CATEGORIES', ','.join(user_categories))


def get_managers():
    """Initialize and return database, LLM provider, and book manager."""
    config = load_config()

    # Validate API key
    provider_name = config['llm']['provider']
    api_key_field = f"{provider_name}_api_key"

    if config['llm'][api_key_field] == f"your-{provider_name}-api-key-here":
        click.echo(f"Error: Please configure your {provider_name.upper()} API key in .env", err=True)
        raise click.Abort()

    db = Database(config['database']['path'])
    llm_provider = get_provider(config)
    book_manager = BookManager(db, llm_provider, config)

    return config, db, llm_provider, book_manager


@click.group()
def cli():
    """Book Tracker - Track your reading list with AI-powered metadata."""
    pass


@cli.command()
@click.option('--directory', type=click.Choice(['books_read', 'books_to_read', 'all']), default='all',
              help='Directory to scan for images')
@click.option('--no-prompt', is_flag=True, help='Skip interactive prompts, use defaults (useful for automated runs)')
def scan(directory, no_prompt):
    """Scan directories for book images and extract information."""
    config, db, llm_provider, book_manager = get_managers()
    image_processor = ImageProcessor(config, db)

    directories = []
    if directory == 'all':
        directories = [config['directories']['books_read'], config['directories']['books_to_read']]
    else:
        directories = [config['directories'][directory]]

    total_books_added = 0

    for dir_name in directories:
        click.echo(f"\nScanning directory: {dir_name}")
        unprocessed_images = image_processor.scan_directory(dir_name)

        if not unprocessed_images:
            click.echo(f"No new images found in {dir_name}")
            continue

        click.echo(f"Found {len(unprocessed_images)} unprocessed image(s)")

        for image_path in unprocessed_images:
            click.echo(f"\nProcessing: {Path(image_path).name}")

            try:
                # Extract books from image
                books = llm_provider.extract_books_from_image(image_path)

                if not books:
                    click.echo("  No books detected in image")
                    db.mark_image_processed(image_path, 0)
                    continue

                click.echo(f"  Detected {len(books)} book(s)")

                # Determine read status from directory
                read_status = image_processor.get_read_status_from_directory(image_path)

                books_added = 0
                for book_data in books:
                    title = book_data['title']
                    authors = book_data['authors']

                    click.echo(f"  - {title} by {', '.join(authors)}")

                    # Prepare book data
                    book_entry = {
                        'title': title,
                        'authors': authors,
                        'read_status': read_status,
                        'source_image_path': image_path
                    }

                    # Add book
                    book_id, status = book_manager.add_book(book_entry)

                    if status == 'duplicate':
                        click.echo(f"    Already in database (ID: {book_id})")
                    elif status == 'added':
                        click.echo(f"    Added to database (ID: {book_id})")
                        books_added += 1

                        # Prompt for rating if read
                        if read_status == 'read' and not no_prompt:
                            rating = click.prompt("    Rate this book (1-10)", type=int, default=0)
                            if rating > 0:
                                book_manager.update_book(book_id, {'rating': rating})

                total_books_added += books_added

                # Mark image as processed
                db.mark_image_processed(image_path, books_added)

            except Exception as e:
                click.echo(f"  Error processing image: {e}", err=True)
                continue

    click.echo(f"\n✓ Scan complete. Added {total_books_added} new book(s).")


@cli.command()
@click.option('--title', required=True, help='Book title')
@click.option('--author', 'authors', multiple=True, required=True, help='Author name(s)')
@click.option('--read', is_flag=True, help='Mark as already read')
@click.option('--rating', type=click.IntRange(1, 10), help='Rating (1-10)')
@click.option('--notes', help='Personal notes')
def add(title, authors, read, rating, notes):
    """Manually add a book to the database."""
    config, db, llm_provider, book_manager = get_managers()

    # Determine read status
    if not read:
        read = click.confirm("Have you read this book?", default=False)

    read_status = 'read' if read else 'to_read'

    # Prepare book data
    book_data = {
        'title': title,
        'authors': list(authors),
        'read_status': read_status
    }

    if rating:
        book_data['rating'] = rating
    elif read_status == 'read':
        rating_input = click.prompt("Rate this book (1-10, or 0 to skip)", type=int, default=0)
        if rating_input > 0:
            book_data['rating'] = rating_input

    if notes:
        book_data['personal_notes'] = notes

    # Add book
    try:
        book_id, status = book_manager.add_book(book_data)

        if status == 'duplicate':
            click.echo(f"Book already exists in database (ID: {book_id})")
            if click.confirm("Do you want to update it?"):
                updates = {}
                if rating:
                    updates['rating'] = rating
                if notes:
                    updates['personal_notes'] = notes
                if updates:
                    book_manager.update_book(book_id, updates)
                    click.echo("✓ Book updated")
        elif status == 'added':
            click.echo(f"✓ Book added successfully (ID: {book_id})")

    except Exception as e:
        click.echo(f"Error adding book: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--title', help='Filter by title (partial match)')
@click.option('--author', help='Filter by author (partial match)')
@click.option('--read', is_flag=True, help='Show only read books')
@click.option('--to-read', is_flag=True, help='Show only books to read')
@click.option('--category', help='Filter by LLM category')
@click.option('--user-category', help='Filter by user category')
@click.option('--rating-min', type=click.IntRange(1, 10), help='Minimum rating')
@click.option('--rating-max', type=click.IntRange(1, 10), help='Maximum rating')
def search(title, author, read, to_read, category, user_category, rating_min, rating_max):
    """Search for books with various filters."""
    config, db, llm_provider, book_manager = get_managers()

    filters = {}

    if title:
        filters['title'] = title
    if author:
        filters['author'] = author
    if read:
        filters['read_status'] = 'read'
    elif to_read:
        filters['read_status'] = 'to_read'
    if category:
        filters['category'] = category
    if user_category:
        filters['user_category'] = user_category
    if rating_min:
        filters['rating_min'] = rating_min
    if rating_max:
        filters['rating_max'] = rating_max

    books = book_manager.search_books(filters)

    if not books:
        click.echo("No books found matching the criteria.")
        return

    click.echo(f"\nFound {len(books)} book(s):\n")

    for book in books:
        click.echo(book_manager.format_book_display(book))
        click.echo()


@cli.command(name='list')
@click.option('--read', is_flag=True, help='Show only read books')
@click.option('--to-read', is_flag=True, help='Show only books to read')
@click.option('--sort-by', type=click.Choice(['title', 'author', 'rating', 'date_added']), default='date_added',
              help='Sort by field')
def list_books(read, to_read, sort_by):
    """List all books in the database."""
    config, db, llm_provider, book_manager = get_managers()

    filters = {}
    if read:
        filters['read_status'] = 'read'
    elif to_read:
        filters['read_status'] = 'to_read'

    # Map friendly names to database columns
    sort_map = {
        'title': 'title',
        'author': 'authors',
        'rating': 'rating',
        'date_added': 'date_added'
    }
    filters['sort_by'] = sort_map[sort_by]

    books = book_manager.search_books(filters)

    if not books:
        click.echo("No books in database.")
        return

    click.echo(f"\n{len(books)} book(s) in database:\n")

    for book in books:
        click.echo(book_manager.format_book_display(book))
        click.echo()


@cli.command()
@click.argument('book_identifier')
def show(book_identifier):
    """Show detailed information about a book (by ID or title)."""
    config, db, llm_provider, book_manager = get_managers()

    # Try to parse as ID first
    book = None
    try:
        book_id = int(book_identifier)
        book = book_manager.get_book(book_id)
    except ValueError:
        # Not an ID, try title
        book = book_manager.get_book_by_title(book_identifier)

    if not book:
        click.echo(f"Book not found: {book_identifier}", err=True)
        raise click.Abort()

    click.echo("\n" + book_manager.format_book_display(book, detailed=True) + "\n")


@cli.command()
@click.argument('book_id', type=int)
@click.option('--rating', type=click.IntRange(1, 10), help='Update rating')
@click.option('--notes', help='Update personal notes')
@click.option('--read', is_flag=True, help='Mark as read')
@click.option('--to-read', is_flag=True, help='Mark as to-read')
def update(book_id, rating, notes, read, to_read):
    """Update book information."""
    config, db, llm_provider, book_manager = get_managers()

    book = book_manager.get_book(book_id)
    if not book:
        click.echo(f"Book not found: {book_id}", err=True)
        raise click.Abort()

    updates = {}

    if rating:
        updates['rating'] = rating
    if notes:
        updates['personal_notes'] = notes
    if read:
        updates['read_status'] = 'read'
    elif to_read:
        updates['read_status'] = 'to_read'

    if not updates:
        click.echo("No updates specified.")
        return

    book_manager.update_book(book_id, updates)
    click.echo("✓ Book updated successfully")


@cli.command()
@click.argument('book_identifier')
@click.option('--force', is_flag=True, help='Re-fetch all fields, overwriting existing data')
def enrich(book_identifier, force):
    """Enrich a book with detailed metadata from LLM."""
    config, db, llm_provider, book_manager = get_managers()

    # Try to parse as ID first
    book = None
    try:
        book_id = int(book_identifier)
        book = book_manager.get_book(book_id)
    except ValueError:
        # Not an ID, try title
        book = book_manager.get_book_by_title(book_identifier)
        if book:
            book_id = book['id']

    if not book:
        click.echo(f"Book not found: {book_identifier}", err=True)
        raise click.Abort()

    try:
        if force:
            click.echo("Re-fetching all metadata fields...")
        else:
            click.echo("Fetching missing metadata fields...")

        updated_book = book_manager.enrich_book(book_id, force=force)
        click.echo("✓ Book enriched successfully\n")
        click.echo(book_manager.format_book_display(updated_book, detailed=True))

    except Exception as e:
        click.echo(f"Error enriching book: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--format', 'output_format', type=click.Choice(['csv', 'json']), required=True, help='Export format')
@click.option('--output', required=True, help='Output file path')
def export(output_format, output):
    """Export all books to CSV or JSON."""
    config, db, llm_provider, book_manager = get_managers()

    books = book_manager.search_books({})

    if not books:
        click.echo("No books to export.")
        return

    try:
        if output_format == 'json':
            with open(output, 'w') as f:
                json.dump(books, f, indent=2)
        elif output_format == 'csv':
            with open(output, 'w', newline='') as f:
                # Get all possible fields
                fieldnames = ['id', 'title', 'authors', 'read_status', 'rating', 'date_added',
                              'personal_notes', 'publication_date', 'isbn', 'fiction_nonfiction',
                              'synopsis', 'themes', 'main_characters', 'quotes', 'awards',
                              'llm_categories', 'user_categories', 'source_image_path', 'last_updated']

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for book in books:
                    # Convert lists to comma-separated strings for CSV
                    row = book.copy()
                    for field in ['authors', 'themes', 'main_characters', 'quotes', 'awards', 'llm_categories', 'user_categories']:
                        if isinstance(row.get(field), list):
                            row[field] = ', '.join(row[field])
                    writer.writerow(row)

        click.echo(f"✓ Exported {len(books)} book(s) to {output}")

    except Exception as e:
        click.echo(f"Error exporting books: {e}", err=True)
        raise click.Abort()


@cli.group()
def categories():
    """Manage predefined user categories."""
    pass


@categories.command(name='list')
def list_categories():
    """List all predefined user categories."""
    config = load_config()
    user_categories = config['settings'].get('user_categories', [])

    if not user_categories:
        click.echo("No user categories defined.")
        return

    click.echo("\nPredefined user categories:")
    for i, category in enumerate(user_categories, 1):
        click.echo(f"  {i}. {category}")
    click.echo()


@categories.command(name='add')
@click.argument('category')
def add_category(category):
    """Add a new predefined user category."""
    config = load_config()

    # Normalize category (lowercase, trim)
    category = category.lower().strip()

    if not category:
        click.echo("Category name cannot be empty.", err=True)
        raise click.Abort()

    user_categories = config['settings'].get('user_categories', [])

    if category in user_categories:
        click.echo(f"Category '{category}' already exists.")
        return

    user_categories.append(category)
    config['settings']['user_categories'] = user_categories

    save_config(config)

    click.echo(f"✓ Added category: {category}")


@categories.command(name='remove')
@click.argument('category')
def remove_category(category):
    """Remove a predefined user category."""
    config = load_config()

    category = category.lower().strip()
    user_categories = config['settings'].get('user_categories', [])

    if category not in user_categories:
        click.echo(f"Category '{category}' not found.")
        return

    user_categories.remove(category)
    config['settings']['user_categories'] = user_categories

    save_config(config)

    click.echo(f"✓ Removed category: {category}")


if __name__ == '__main__':
    cli()
