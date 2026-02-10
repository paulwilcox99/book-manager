#!/usr/bin/env python3
"""
Generate a static website from the books database.
Only regenerates if the database has changed since last run.
"""

import os
import sys
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from html import escape

# Configuration
DB_PATH = "books.db"
OUTPUT_DIR = "site"
STATE_FILE = ".site_state.json"


def get_db_hash(db_path):
    """Get hash of database file to detect changes."""
    with open(db_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def load_state():
    """Load previous generation state."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_state(state):
    """Save generation state."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)


def parse_json_field(value):
    """Parse a JSON field, returning empty list if invalid."""
    if not value:
        return []
    try:
        result = json.loads(value)
        if isinstance(result, list):
            return result
        return [result]
    except:
        return [value] if value else []


def slugify(text):
    """Convert text to URL-safe slug."""
    if not text:
        return "unknown"
    return "".join(c if c.isalnum() else "-" for c in text.lower()).strip("-")[:50]


def get_all_books(db_path):
    """Fetch all books from database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books ORDER BY title")
    books = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Parse JSON fields
    for book in books:
        book['authors_list'] = parse_json_field(book['authors'])
        book['themes_list'] = parse_json_field(book['themes'])
        book['user_categories_list'] = parse_json_field(book['user_categories'])
        book['llm_categories_list'] = parse_json_field(book['llm_categories'])
        book['quotes_list'] = parse_json_field(book['quotes'])
        book['main_characters_list'] = parse_json_field(book['main_characters'])
    
    return books


# HTML Templates
def html_header(title, breadcrumbs=None):
    """Generate HTML header."""
    bc_html = ""
    if breadcrumbs:
        bc_parts = ['<a href="index.html">Home</a>']
        for name, link in breadcrumbs:
            if link:
                bc_parts.append(f'<a href="{link}">{escape(name)}</a>')
            else:
                bc_parts.append(escape(name))
        bc_html = f'<nav class="breadcrumbs">{" → ".join(bc_parts)}</nav>'
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)} - Book Collection</title>
    <style>
        :root {{
            --bg: #faf8f5;
            --bg-card: #ffffff;
            --text: #2c2c2c;
            --text-muted: #666666;
            --accent: #8b2942;
            --accent-hover: #6b1d32;
            --link: #1a4a6e;
            --link-hover: #0d2d44;
            --border: #d4cfc7;
            --border-light: #e8e4dd;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: Georgia, 'Times New Roman', serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.8;
            padding: 2.5rem;
            max-width: 960px;
            margin: 0 auto;
        }}
        a {{ color: var(--link); text-decoration: underline; text-decoration-color: var(--border); text-underline-offset: 2px; }}
        a:hover {{ color: var(--link-hover); text-decoration-color: var(--link-hover); }}
        h1 {{ 
            color: var(--text); 
            margin-bottom: 1.5rem; 
            font-size: 2.2rem; 
            font-weight: normal;
            letter-spacing: -0.02em;
            border-bottom: 2px solid var(--accent);
            padding-bottom: 0.75rem;
        }}
        h2 {{ 
            color: var(--text); 
            margin: 2rem 0 1rem; 
            font-size: 1.4rem; 
            font-weight: normal;
            border-bottom: 1px solid var(--border); 
            padding-bottom: 0.5rem; 
        }}
        h3 {{ color: var(--text); margin: 1.25rem 0 0.75rem; font-size: 1.1rem; font-weight: 600; }}
        .breadcrumbs {{ margin-bottom: 2rem; color: var(--text-muted); font-size: 0.9rem; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
        .breadcrumbs a {{ color: var(--link); }}
        .card {{
            background: var(--bg-card);
            padding: 2rem;
            margin-bottom: 1.5rem;
            border: 1px solid var(--border-light);
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}
        .book-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.5rem;
        }}
        .book-card {{
            background: var(--bg-card);
            padding: 1.25rem;
            border: 1px solid var(--border-light);
            transition: border-color 0.2s, box-shadow 0.2s;
        }}
        .book-card:hover {{ border-color: var(--accent); box-shadow: 0 2px 8px rgba(139,41,66,0.08); }}
        .book-card h3 {{ margin: 0 0 0.5rem; font-size: 1rem; font-weight: 600; }}
        .book-card h3 a {{ text-decoration: none; }}
        .book-card h3 a:hover {{ text-decoration: underline; }}
        .book-card .author {{ color: var(--text-muted); font-size: 0.95rem; font-style: italic; }}
        .book-card .meta {{ font-size: 0.85rem; color: var(--text-muted); margin-top: 0.75rem; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
        .rating {{ color: var(--accent); }}
        .status {{ 
            display: inline-block; 
            padding: 0.15rem 0.5rem; 
            font-size: 0.7rem; 
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-weight: 500;
        }}
        .status.read {{ background: #e8f5e9; color: #2e7d32; border: 1px solid #c8e6c9; }}
        .status.to_read {{ background: #fff8e1; color: #f57f17; border: 1px solid #ffecb3; }}
        .tag {{
            display: inline-block;
            background: var(--bg);
            color: var(--text-muted);
            padding: 0.2rem 0.6rem;
            font-size: 0.85rem;
            margin: 0.25rem;
            border: 1px solid var(--border);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            text-decoration: none;
        }}
        .tag:hover {{ background: var(--accent); color: white; border-color: var(--accent); text-decoration: none; }}
        .quote {{
            border-left: 3px solid var(--accent);
            padding-left: 1.25rem;
            margin: 1.5rem 0;
            font-style: italic;
            color: var(--text-muted);
        }}
        .nav-sections {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2.5rem;
        }}
        .nav-section {{
            background: var(--bg-card);
            padding: 1.5rem;
            border: 1px solid var(--border-light);
        }}
        .nav-section h3 {{ margin-bottom: 1rem; color: var(--accent); font-size: 1rem; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
        .nav-section ul {{ list-style: none; }}
        .nav-section li {{ margin: 0.4rem 0; font-size: 0.95rem; }}
        .nav-section a {{ text-decoration: none; }}
        .nav-section a:hover {{ text-decoration: underline; }}
        .stats {{ display: flex; gap: 3rem; margin-bottom: 2.5rem; flex-wrap: wrap; padding: 1.5rem 0; border-bottom: 1px solid var(--border-light); }}
        .stat {{ text-align: center; }}
        .stat-value {{ font-size: 2.5rem; color: var(--accent); font-weight: normal; font-family: Georgia, serif; }}
        .stat-label {{ font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
        dl {{ margin: 1.25rem 0; }}
        dt {{ color: var(--text-muted); font-size: 0.85rem; margin-top: 1rem; text-transform: uppercase; letter-spacing: 0.03em; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
        dd {{ margin-left: 0; margin-top: 0.25rem; }}
        .synopsis {{ line-height: 1.9; text-align: justify; }}
    </style>
</head>
<body>
{bc_html}
<h1>{escape(title)}</h1>
'''


def html_footer():
    """Generate HTML footer."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f'''
<footer style="margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid var(--border); color: var(--text-muted); font-size: 0.8rem; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; text-align: center;">
    Generated on {timestamp}
</footer>
</body>
</html>
'''


def generate_book_page(book, output_dir):
    """Generate individual book page."""
    slug = f"book-{book['id']}-{slugify(book['title'])}"
    filepath = os.path.join(output_dir, "books", f"{slug}.html")
    
    authors = ", ".join(book['authors_list']) if book['authors_list'] else book['authors']
    
    html = html_header(book['title'], [("Books", "books.html"), (book['title'], None)])
    
    html += '<div class="card">'
    html += f'<p class="author">by {escape(authors)}</p>'
    
    # Status and rating
    html += '<p style="margin: 1rem 0;">'
    status_class = book['read_status']
    status_text = "Read" if status_class == "read" else "To Read"
    html += f'<span class="status {status_class}">{status_text}</span>'
    if book['rating']:
        html += f' <span class="rating">{"★" * book["rating"]}{"☆" * (10 - book["rating"])}</span> {book["rating"]}/10'
    html += '</p>'
    
    html += '<dl>'
    
    if book['publication_date']:
        html += f'<dt>Published</dt><dd>{escape(str(book["publication_date"]))}</dd>'
    
    if book['isbn']:
        html += f'<dt>ISBN</dt><dd>{escape(book["isbn"])}</dd>'
    
    if book['fiction_nonfiction']:
        html += f'<dt>Type</dt><dd>{escape(book["fiction_nonfiction"])}</dd>'
    
    html += '</dl>'
    
    if book['synopsis']:
        html += f'<h2>Synopsis</h2><p class="synopsis">{escape(book["synopsis"])}</p>'
    
    if book['themes_list']:
        html += '<h2>Themes</h2><p>'
        for theme in book['themes_list']:
            theme_slug = slugify(theme)
            html += f'<a href="../themes/{theme_slug}.html" class="tag">{escape(theme)}</a>'
        html += '</p>'
    
    if book['main_characters_list']:
        html += '<h2>Main Characters</h2><p>'
        html += ", ".join(escape(c) for c in book['main_characters_list'])
        html += '</p>'
    
    if book['quotes_list']:
        html += '<h2>Quotes</h2>'
        for quote in book['quotes_list']:
            html += f'<blockquote class="quote">{escape(quote)}</blockquote>'
    
    if book['awards']:
        html += f'<h2>Awards</h2><p>{escape(book["awards"])}</p>'
    
    if book['user_categories_list']:
        html += '<h2>Categories</h2><p>'
        for cat in book['user_categories_list']:
            cat_slug = slugify(cat)
            html += f'<a href="../categories/{cat_slug}.html" class="tag">{escape(cat)}</a>'
        html += '</p>'
    
    if book['personal_notes']:
        html += f'<h2>Personal Notes</h2><p>{escape(book["personal_notes"])}</p>'
    
    html += f'<p style="margin-top: 1rem; font-size: 0.8rem; color: var(--text-muted);">Added: {book["date_added"][:10]}</p>'
    
    html += '</div>'
    html += html_footer()
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        f.write(html)
    
    return slug


def generate_list_page(title, items, output_path, breadcrumbs, intro=""):
    """Generate a list page (authors, themes, categories index)."""
    html = html_header(title, breadcrumbs)
    
    if intro:
        html += f'<p style="margin-bottom: 1.5rem; color: var(--text-muted);">{intro}</p>'
    
    html += '<ul style="list-style: none; columns: 2; column-gap: 2rem;">'
    for name, link, count in sorted(items, key=lambda x: x[0].lower()):
        html += f'<li style="margin: 0.5rem 0;"><a href="{link}">{escape(name)}</a> <span style="color: var(--text-muted);">({count})</span></li>'
    html += '</ul>'
    
    html += html_footer()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(html)


def generate_group_page(title, books, output_path, breadcrumbs):
    """Generate a page showing a group of books."""
    html = html_header(title, breadcrumbs)
    
    html += f'<p style="margin-bottom: 1.5rem; color: var(--text-muted);">{len(books)} book(s)</p>'
    
    html += '<div class="book-grid">'
    for book in sorted(books, key=lambda b: b['title'].lower()):
        slug = f"book-{book['id']}-{slugify(book['title'])}"
        authors = ", ".join(book['authors_list']) if book['authors_list'] else book['authors']
        
        html += f'''<div class="book-card">
            <h3><a href="../books/{slug}.html">{escape(book['title'])}</a></h3>
            <p class="author">{escape(authors)}</p>
            <p class="meta">'''
        
        status_class = book['read_status']
        status_text = "Read" if status_class == "read" else "To Read"
        html += f'<span class="status {status_class}">{status_text}</span>'
        
        if book['rating']:
            html += f' <span class="rating">{"★" * book["rating"]}</span>'
        
        html += '</p></div>'
    html += '</div>'
    
    html += html_footer()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(html)


def generate_books_index(books, output_dir):
    """Generate all books index page."""
    html = html_header("All Books", [("All Books", None)])
    
    read_count = sum(1 for b in books if b['read_status'] == 'read')
    to_read_count = len(books) - read_count
    
    html += f'''<div class="stats">
        <div class="stat"><div class="stat-value">{len(books)}</div><div class="stat-label">Total Books</div></div>
        <div class="stat"><div class="stat-value">{read_count}</div><div class="stat-label">Read</div></div>
        <div class="stat"><div class="stat-value">{to_read_count}</div><div class="stat-label">To Read</div></div>
    </div>'''
    
    html += '<div class="book-grid">'
    for book in sorted(books, key=lambda b: b['title'].lower()):
        slug = f"book-{book['id']}-{slugify(book['title'])}"
        authors = ", ".join(book['authors_list']) if book['authors_list'] else book['authors']
        
        html += f'''<div class="book-card">
            <h3><a href="books/{slug}.html">{escape(book['title'])}</a></h3>
            <p class="author">{escape(authors)}</p>
            <p class="meta">'''
        
        status_class = book['read_status']
        status_text = "Read" if status_class == "read" else "To Read"
        html += f'<span class="status {status_class}">{status_text}</span>'
        
        if book['rating']:
            html += f' <span class="rating">{"★" * book["rating"]}</span>'
        
        html += '</p></div>'
    html += '</div>'
    
    html += html_footer()
    
    with open(os.path.join(output_dir, "books.html"), 'w') as f:
        f.write(html)


def generate_index(books, authors_count, themes_count, categories_count, output_dir):
    """Generate main index page."""
    html = html_header("Book Collection")
    
    read_count = sum(1 for b in books if b['read_status'] == 'read')
    to_read_count = len(books) - read_count
    rated_books = [b for b in books if b['rating']]
    avg_rating = sum(b['rating'] for b in rated_books) / len(rated_books) if rated_books else 0
    
    html += f'''<div class="stats">
        <div class="stat"><div class="stat-value">{len(books)}</div><div class="stat-label">Total Books</div></div>
        <div class="stat"><div class="stat-value">{read_count}</div><div class="stat-label">Read</div></div>
        <div class="stat"><div class="stat-value">{to_read_count}</div><div class="stat-label">To Read</div></div>
        <div class="stat"><div class="stat-value">{avg_rating:.1f}</div><div class="stat-label">Avg Rating</div></div>
    </div>'''
    
    html += '<div class="nav-sections">'
    
    html += f'''<div class="nav-section">
        <h3>📚 Browse</h3>
        <ul>
            <li><a href="books.html">All Books ({len(books)})</a></li>
            <li><a href="authors.html">By Author ({authors_count})</a></li>
            <li><a href="themes.html">By Theme ({themes_count})</a></li>
            <li><a href="categories.html">By Category ({categories_count})</a></li>
        </ul>
    </div>'''
    
    # Recently added
    recent = sorted(books, key=lambda b: b['date_added'], reverse=True)[:5]
    html += '<div class="nav-section"><h3>🕐 Recently Added</h3><ul>'
    for book in recent:
        slug = f"book-{book['id']}-{slugify(book['title'])}"
        html += f'<li><a href="books/{slug}.html">{escape(book["title"])}</a></li>'
    html += '</ul></div>'
    
    # Top rated
    top_rated = sorted([b for b in books if b['rating']], key=lambda b: b['rating'], reverse=True)[:5]
    if top_rated:
        html += '<div class="nav-section"><h3>⭐ Top Rated</h3><ul>'
        for book in top_rated:
            slug = f"book-{book['id']}-{slugify(book['title'])}"
            html += f'<li><a href="books/{slug}.html">{escape(book["title"])}</a> ({book["rating"]}/10)</li>'
        html += '</ul></div>'
    
    # To read
    to_read = [b for b in books if b['read_status'] == 'to_read']
    if to_read:
        html += '<div class="nav-section"><h3>📖 To Read</h3><ul>'
        for book in to_read[:5]:
            slug = f"book-{book['id']}-{slugify(book['title'])}"
            html += f'<li><a href="books/{slug}.html">{escape(book["title"])}</a></li>'
        html += '</ul></div>'
    
    html += '</div>'
    html += html_footer()
    
    with open(os.path.join(output_dir, "index.html"), 'w') as f:
        f.write(html)


def generate_site(force=False):
    """Generate the complete static site."""
    # Check if regeneration needed
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return False
    
    current_hash = get_db_hash(DB_PATH)
    state = load_state()
    
    if not force and state.get('db_hash') == current_hash:
        print("Database unchanged. Use --force to regenerate anyway.")
        return True
    
    print("Generating site...")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "books"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "authors"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "themes"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "categories"), exist_ok=True)
    
    # Get all books
    books = get_all_books(DB_PATH)
    print(f"Found {len(books)} books")
    
    # Generate individual book pages
    for book in books:
        generate_book_page(book, OUTPUT_DIR)
    print(f"Generated {len(books)} book pages")
    
    # Build indexes
    authors_index = defaultdict(list)
    themes_index = defaultdict(list)
    categories_index = defaultdict(list)
    
    for book in books:
        for author in book['authors_list']:
            if author:
                authors_index[author].append(book)
        for theme in book['themes_list']:
            if theme:
                themes_index[theme].append(book)
        for cat in book['user_categories_list']:
            if cat:
                categories_index[cat].append(book)
    
    # Generate author pages
    author_items = []
    for author, author_books in authors_index.items():
        slug = slugify(author)
        filepath = os.path.join(OUTPUT_DIR, "authors", f"{slug}.html")
        generate_group_page(author, author_books, filepath, [("Authors", "authors.html"), (author, None)])
        author_items.append((author, f"authors/{slug}.html", len(author_books)))
    
    generate_list_page("Authors", author_items, 
                      os.path.join(OUTPUT_DIR, "authors.html"),
                      [("Authors", None)],
                      f"{len(authors_index)} authors in your collection")
    print(f"Generated {len(authors_index)} author pages")
    
    # Generate theme pages
    theme_items = []
    for theme, theme_books in themes_index.items():
        slug = slugify(theme)
        filepath = os.path.join(OUTPUT_DIR, "themes", f"{slug}.html")
        generate_group_page(theme, theme_books, filepath, [("Themes", "themes.html"), (theme, None)])
        theme_items.append((theme, f"themes/{slug}.html", len(theme_books)))
    
    generate_list_page("Themes", theme_items,
                      os.path.join(OUTPUT_DIR, "themes.html"),
                      [("Themes", None)],
                      f"{len(themes_index)} themes across your books")
    print(f"Generated {len(themes_index)} theme pages")
    
    # Generate category pages
    category_items = []
    for cat, cat_books in categories_index.items():
        slug = slugify(cat)
        filepath = os.path.join(OUTPUT_DIR, "categories", f"{slug}.html")
        generate_group_page(cat, cat_books, filepath, [("Categories", "categories.html"), (cat, None)])
        category_items.append((cat, f"categories/{slug}.html", len(cat_books)))
    
    generate_list_page("Categories", category_items,
                      os.path.join(OUTPUT_DIR, "categories.html"),
                      [("Categories", None)],
                      f"{len(categories_index)} categories")
    print(f"Generated {len(categories_index)} category pages")
    
    # Generate all books page
    generate_books_index(books, OUTPUT_DIR)
    
    # Generate main index
    generate_index(books, len(authors_index), len(themes_index), len(categories_index), OUTPUT_DIR)
    
    # Save state
    save_state({'db_hash': current_hash, 'generated_at': datetime.now().isoformat()})
    
    print(f"\n✓ Site generated in '{OUTPUT_DIR}/'")
    print(f"  Open {OUTPUT_DIR}/index.html to view")
    
    return True


if __name__ == "__main__":
    force = "--force" in sys.argv
    success = generate_site(force=force)
    sys.exit(0 if success else 1)
