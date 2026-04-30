# Book Tracker

A CLI application for tracking your reading list with AI-powered metadata extraction and enrichment.

## Features

- 📸 **Image-based book entry**: Take photos of book covers or spines and automatically extract book information
- 📝 **Manual entry**: Add books manually with title and author
- 🤖 **AI-powered enrichment**: Automatically gather detailed metadata using OpenAI, Anthropic Claude, or Google Gemini
- 🔍 **Flexible search**: Search and filter by title, author, category, rating, and more
- 📊 **Export**: Export your book database to CSV or JSON
- 🏷️ **Dual categorization**: Both open-ended LLM categories and user-defined categories
- ⭐ **Smart refresh**: Only fetch missing metadata fields, or force re-fetch all fields

## Installation

1. Clone or download this repository

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure your API key — copy the example and edit it:
```bash
cp .env.example .env
# Edit .env and replace the placeholder with your actual API key
```

5. Create directories for your book images:
```bash
mkdir books_read books_to_read
```

6. Run the test scan to verify everything is working:
```bash
python test_scan.py
```
This copies sample images from `test_data/` through the full scan pipeline (image recognition → metadata enrichment → database storage) using a temporary database, then cleans up. If it completes successfully you're ready to start adding your own books.

## Usage

### Scan Images

Place images of book covers/spines in the appropriate directories:
- `books_read/` - Books you've already read
- `books_to_read/` - Books on your reading list

Then scan them:
```bash
python book_tracker.py scan
python book_tracker.py scan --directory books_read
python book_tracker.py scan --directory books_to_read
```

### Manual Entry

Add a book manually:
```bash
python book_tracker.py add --title "1984" --author "George Orwell" --read --rating 9
python book_tracker.py add --title "The Great Gatsby" --author "F. Scott Fitzgerald" --notes "Classic American literature"
```

### Search and List

Search for books:
```bash
# Search by title
python book_tracker.py search --title "gatsby"

# Search by author
python book_tracker.py search --author "orwell"

# Search by category
python book_tracker.py search --category "dystopian"
python book_tracker.py search --user-category "classical literature"

# Filter by read status
python book_tracker.py search --read
python book_tracker.py search --to-read

# Filter by rating
python book_tracker.py search --rating-min 8
```

List all books:
```bash
python book_tracker.py list
python book_tracker.py list --read
python book_tracker.py list --sort-by rating
```

### View Book Details

Show detailed information about a book:
```bash
python book_tracker.py show 1
python book_tracker.py show "1984"
```

### Update Books

Update book information:
```bash
python book_tracker.py update 1 --rating 10
python book_tracker.py update 1 --notes "Re-read in 2024"
python book_tracker.py update 1 --read
```

### Enrich Metadata

Enrich a book with AI-generated metadata:
```bash
# Fetch only missing fields
python book_tracker.py enrich 1

# Re-fetch all fields (overwrites existing data)
python book_tracker.py enrich 1 --force

# By title
python book_tracker.py enrich "1984"
```

### Manage Categories

Manage your predefined user categories:
```bash
# List categories
python book_tracker.py categories list

# Add a category
python book_tracker.py categories add "science fiction"

# Remove a category
python book_tracker.py categories remove "technical"
```

### Export Data

Export your book database:
```bash
python book_tracker.py export --format csv --output books.csv
python book_tracker.py export --format json --output books.json
```

## Configuration

Edit `config.yaml` to customize:

- **LLM Provider**: Choose between OpenAI, Anthropic, or Google
- **API Keys**: Configure your API keys for each provider
- **Models**: Specify which model to use for each provider
- **Auto-enrichment**: Enable/disable automatic metadata enrichment
- **User Categories**: Define your custom category list for classification

## Database Schema

The application uses SQLite to store book information with the following fields:

**Core Fields:**
- ID, Title, Authors, Read Status, Rating, Date Added, Personal Notes

**Enhanced Metadata (from LLM):**
- Publication Date, ISBN, Fiction/Non-fiction, Synopsis
- Themes, Main Characters, Quotes, Awards
- LLM Categories (open-ended)
- User Categories (matched against predefined list)

**Metadata:**
- Source Image Path, Last Updated

## How It Works

1. **Image Scanning**: Place book images in `books_read/` or `books_to_read/`
2. **LLM Extraction**: The LLM analyzes images and extracts title/author information
3. **Auto-enrichment**: If enabled, the application automatically fetches detailed metadata
4. **Category Matching**: Books are matched against your predefined categories
5. **Database Storage**: All information is stored in a local SQLite database
6. **Smart Updates**: Use the `enrich` command to update missing fields without overwriting existing data

## Tips

- Use high-quality images with clear, readable text for best results
- The `--force` flag on `enrich` will overwrite existing data - use with caution
- User categories are matched semantically by the LLM, so related terms will work
- Export to CSV for spreadsheet analysis or JSON for programmatic access
- Set `auto_enrich: false` in config to disable automatic metadata fetching

## Troubleshooting

**"API key not configured" error:**
- Edit `config.yaml` and replace the placeholder with your actual API key

**Images not being processed:**
- Check that images are in the correct directories
- Verify image format is .jpg, .jpeg, or .png
- Run `scan` command to process new images

**Book not found in enrichment:**
- Try the `--force` flag to re-fetch all information
- Verify the book title and author are correct in the database

## Cost Considerations

This application makes API calls to LLM providers which may incur costs:
- 1 API call per image for book extraction
- 1 API call per book for metadata enrichment
- 1 API call per book for user category matching

With auto-enrichment enabled, expect 3 API calls per new book added from images.

## Security

- API keys are stored in `config.yaml` - set file permissions to 600
- The database contains only book information, no sensitive personal data
- All data is stored locally on your machine

## License

This project is provided as-is for personal use.
# book-manager
