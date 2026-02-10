# 📚 Book Tracker - START HERE

Welcome to your Book Tracker application! This guide will get you up and running in 5 minutes.

## What This Does

Track your reading list by taking photos of book covers. The app uses AI to:
- Extract book titles and authors from images
- Fetch detailed metadata (synopsis, themes, awards, etc.)
- Organize books with categories
- Let you search, rate, and export your collection

## Quick Setup (3 Steps)

### Step 1: Install Dependencies

```bash
cd /home/paul/code/books
pip3 install -r requirements.txt
```

### Step 2: Add Your API Key

Edit `config.yaml` and replace the placeholder with your API key:

```bash
nano config.yaml  # or use your favorite editor
```

Find this line:
```yaml
openai_api_key: "your-openai-api-key-here"
```

Replace with your actual key:
```yaml
openai_api_key: "sk-proj-..."
```

**Don't have an API key?** Get one at: https://platform.openai.com/api-keys

### Step 3: Verify Setup

```bash
python3 test_setup.py
```

You should see all tests pass! ✓

## Try It Out

### You Already Have Images!

You have 2 images ready to process:
- 1 image in `books_read/`
- 1 image in `books_to_read/`

Scan them now:
```bash
python3 book_tracker.py scan
```

### Or Add a Test Book Manually

```bash
python3 book_tracker.py add --title "1984" --author "George Orwell" --read --rating 9
```

### See Your Books

```bash
python3 book_tracker.py list
```

### Get Detailed Info

```bash
python3 book_tracker.py show 1
```

## What's Next?

### 📖 Learn More
- **QUICKSTART.md** - Common commands and workflows
- **README.md** - Complete documentation
- **SETUP.md** - Detailed setup help

### 🚀 Start Using
1. Add more book images to `books_read/` or `books_to_read/`
2. Run `python3 book_tracker.py scan` to process them
3. Search and filter your collection
4. Export to CSV/JSON for backup

### 🎯 Common Commands

```bash
# Process images
python3 book_tracker.py scan

# Search books
python3 book_tracker.py search --author "Orwell"

# List all books
python3 book_tracker.py list

# Add manually
python3 book_tracker.py add --title "Book Title" --author "Author Name"

# Export
python3 book_tracker.py export --format csv --output books.csv

# Get help
python3 book_tracker.py --help
```

## File Structure

```
/home/paul/code/books/
├── book_tracker.py         ← Main application
├── books_read/             ← Images of books you've read
├── books_to_read/          ← Images of books to read
├── config.yaml             ← Your settings (edit this!)
├── books.db                ← Database (created automatically)
└── *.md                    ← Documentation files
```

## Need Help?

1. **Installation issues?** → Read `SETUP.md`
2. **How do I...?** → Read `QUICKSTART.md`
3. **Detailed docs?** → Read `README.md`
4. **Setup test fails?** → Run `python3 test_setup.py` and check output

## Provider Options

The app supports 3 AI providers (configured in `config.yaml`):

- **OpenAI** (GPT-4o) - Default, best vision quality
- **Anthropic** (Claude 3.5 Sonnet) - Great for text analysis
- **Google** (Gemini 2.0 Flash) - Fast and cost-effective

You can switch providers by changing the `provider` field in `config.yaml`.

## Cost Estimate

Each book scanned from an image makes 3 API calls:
1. Extract title/author from image (~$0.15)
2. Fetch metadata (~$0.02)
3. Match categories (~$0.01)

**Total: ~$0.18 per book** (OpenAI pricing)

Manual entry only needs 2 API calls (~$0.03 per book).

## Tips

✅ **DO:**
- Use clear, well-lit photos
- Keep API keys private (don't commit config.yaml to git)
- Export your database regularly for backup
- Rate books as you add them

❌ **DON'T:**
- Share your API keys
- Delete books.db (it's your data!)
- Use blurry or low-quality images
- Forget to scan after adding new images

## You're Ready! 🎉

Start by running:
```bash
python3 book_tracker.py scan
```

Then explore your collection:
```bash
python3 book_tracker.py list
```

Happy tracking! 📚
