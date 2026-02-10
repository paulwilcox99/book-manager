# Book Tracker - Quick Start Guide

## Installation (One-Time Setup)

```bash
# Install dependencies
pip3 install -r requirements.txt

# Configure API key (edit config.yaml)
# Replace "your-openai-api-key-here" with your actual key

# Verify setup
python3 test_setup.py
```

## Common Commands

### Scan Images
```bash
# Scan all directories for new book images
python3 book_tracker.py scan

# Scan specific directory only
python3 book_tracker.py scan --directory books_read
python3 book_tracker.py scan --directory books_to_read
```

### Add Books Manually
```bash
# Add a book you've read
python3 book_tracker.py add --title "1984" --author "George Orwell" --read --rating 9

# Add a book to read
python3 book_tracker.py add --title "The Great Gatsby" --author "F. Scott Fitzgerald"

# Add with notes
python3 book_tracker.py add --title "Sapiens" --author "Yuval Noah Harari" --notes "Recommended by friend"
```

### Search & List
```bash
# List all books
python3 book_tracker.py list

# List only read books
python3 book_tracker.py list --read

# List sorted by rating
python3 book_tracker.py list --sort-by rating

# Search by title
python3 book_tracker.py search --title "gatsby"

# Search by author
python3 book_tracker.py search --author "orwell"

# Search read books with high ratings
python3 book_tracker.py search --read --rating-min 8

# Search by category
python3 book_tracker.py search --user-category "classical literature"
```

### View & Update
```bash
# Show detailed info (by ID or title)
python3 book_tracker.py show 1
python3 book_tracker.py show "1984"

# Update rating
python3 book_tracker.py update 1 --rating 10

# Mark as read
python3 book_tracker.py update 1 --read

# Add notes
python3 book_tracker.py update 1 --notes "Amazing dystopian novel"
```

### Enrich Metadata
```bash
# Fetch missing metadata fields
python3 book_tracker.py enrich 1

# Re-fetch all fields (overwrites existing)
python3 book_tracker.py enrich 1 --force

# Enrich by title
python3 book_tracker.py enrich "1984"
```

### Manage Categories
```bash
# List predefined categories
python3 book_tracker.py categories list

# Add a new category
python3 book_tracker.py categories add "science fiction"

# Remove a category
python3 book_tracker.py categories remove "technical"
```

### Export Data
```bash
# Export to CSV
python3 book_tracker.py export --format csv --output my_books.csv

# Export to JSON
python3 book_tracker.py export --format json --output my_books.json
```

## Typical Workflow

### First Time
1. Put book images in `books_read/` or `books_to_read/`
2. Run `python3 book_tracker.py scan`
3. Rate your read books when prompted

### Adding New Books
**From Images:**
1. Add images to appropriate directory
2. Run `python3 book_tracker.py scan`

**Manually:**
1. Run `python3 book_tracker.py add` with details

### Finding Books
```bash
# Quick list
python3 book_tracker.py list

# Detailed search
python3 book_tracker.py search [filters]

# View specific book
python3 book_tracker.py show [id or title]
```

### Updating Books
```bash
python3 book_tracker.py update [id] [options]
python3 book_tracker.py enrich [id]  # Get more metadata
```

## Tips

- **Images**: Use clear photos of book covers or spines
- **Multiple authors**: Use `--author` multiple times: `--author "Author 1" --author "Author 2"`
- **Rating**: Rate only read books (1-10 scale)
- **Categories**: Define your own categories for better organization
- **Export regularly**: Backup your data with export command
- **Enrich existing books**: Use `enrich` without `--force` to only fetch missing data

## Keyboard Shortcuts

When prompted:
- `Ctrl+C` - Cancel operation
- `Enter` - Accept default value
- Type answer and `Enter` - Submit

## Quick Help

```bash
# Main help
python3 book_tracker.py --help

# Command help
python3 book_tracker.py [command] --help

# Examples:
python3 book_tracker.py scan --help
python3 book_tracker.py add --help
python3 book_tracker.py search --help
```

## Troubleshooting

**"API key not configured"**
→ Edit `config.yaml` and add your API key

**"No books found"**
→ Run `scan` or `add` commands first

**"Book already exists"**
→ Update existing book instead or check for duplicates

**"No module named..."**
→ Run `pip3 install -r requirements.txt`

## File Locations

- **Database**: `books.db` (created automatically)
- **Config**: `config.yaml` (edit this for settings)
- **Images**: `books_read/` and `books_to_read/`
- **Exports**: Wherever you specify with `--output`

## Getting Help

1. Read `README.md` for detailed documentation
2. Read `SETUP.md` for installation help
3. Run commands with `--help` flag
4. Check error messages for guidance
