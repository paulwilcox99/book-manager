# Book Tracker - Setup Guide

## Quick Start

Follow these steps to get the Book Tracker application running:

### 1. Install Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

Or with pip3:

```bash
pip3 install -r requirements.txt
```

### 2. Configure API Key

Edit `config.yaml` and add your API key for your chosen provider:

**For OpenAI (default):**
```yaml
llm:
  provider: "openai"
  openai_api_key: "sk-your-actual-api-key-here"
```

**For Anthropic Claude:**
```yaml
llm:
  provider: "anthropic"
  anthropic_api_key: "sk-ant-your-actual-api-key-here"
```

**For Google Gemini:**
```yaml
llm:
  provider: "google"
  google_api_key: "your-actual-api-key-here"
```

### 3. Verify Installation

Run the test script to verify everything is set up correctly:

```bash
python3 test_setup.py
```

You should see all tests pass with "✓ PASS" status.

### 4. Test the CLI

Verify the CLI is working:

```bash
python3 book_tracker.py --help
```

You should see the list of available commands.

### 5. Try Basic Commands

List current categories:
```bash
python3 book_tracker.py categories list
```

Add a test book manually:
```bash
python3 book_tracker.py add --title "Test Book" --author "Test Author"
```

List all books:
```bash
python3 book_tracker.py list
```

### 6. Scan Your Images

If you have book images in `books_read/` or `books_to_read/`:

```bash
python3 book_tracker.py scan
```

## Troubleshooting

### "No module named 'openai'" (or similar)

You need to install the dependencies:
```bash
pip3 install -r requirements.txt
```

### "API key not configured" error

Edit `config.yaml` and replace the placeholder with your actual API key:
```yaml
openai_api_key: "your-openai-api-key-here"
```

### "python: command not found"

Use `python3` instead:
```bash
python3 book_tracker.py --help
```

### Images not being detected

1. Check that images are in the correct directories:
   - `books_read/` for read books
   - `books_to_read/` for books you want to read

2. Check image format (must be .jpg, .jpeg, or .png)

3. Verify directories exist:
   ```bash
   ls books_read/
   ls books_to_read/
   ```

### Permission denied

Make the script executable:
```bash
chmod +x book_tracker.py
```

## Getting API Keys

### OpenAI
1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Create a new API key
4. Copy the key (starts with "sk-")

### Anthropic Claude
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy the key (starts with "sk-ant-")

### Google Gemini
1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Create a new API key
4. Copy the key

## Cost Estimates

Each provider has different pricing. Here's what to expect:

**Per book from image:**
- 1 API call to extract book info from image
- 1 API call to enrich with metadata
- 1 API call to match user categories
- **Total: 3 API calls per book**

**OpenAI GPT-4o** (example):
- ~$0.15 per image extraction (vision)
- ~$0.02 per enrichment call (text)
- ~$0.01 per category matching
- **Total: ~$0.18 per book**

Check your provider's current pricing for accurate costs.

## Next Steps

Once setup is complete:

1. **Read the README.md** for full usage documentation
2. **Add your books** using scan or manual entry
3. **Explore search features** to find books
4. **Export your data** for backup or analysis

## Optional: Create an Alias

Add to your `.bashrc` or `.zshrc`:

```bash
alias books='python3 /home/paul/code/books/book_tracker.py'
```

Then you can use:
```bash
books list
books scan
books search --title "gatsby"
```

## Support

If you encounter issues:
1. Check that all dependencies are installed
2. Verify your API key is correctly configured
3. Run `python3 test_setup.py` to diagnose problems
4. Check the error messages for specific guidance
