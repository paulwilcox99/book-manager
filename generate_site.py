#!/usr/bin/env python3
"""
Generate a single-page application for the books database.
Outputs: index.html + data.json
"""

import os
import json
import sqlite3
from datetime import datetime
from collections import defaultdict

DB_PATH = "books.db"
OUTPUT_DIR = "site"


def parse_json_field(value):
    if not value:
        return []
    try:
        result = json.loads(value)
        return result if isinstance(result, list) else [result]
    except:
        return [value] if value else []


def get_all_books(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books ORDER BY title")
    books = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    for book in books:
        book['authors_list'] = parse_json_field(book['authors'])
        book['themes_list'] = parse_json_field(book['themes'])
        book['user_categories_list'] = parse_json_field(book['user_categories'])
        book['llm_categories_list'] = parse_json_field(book['llm_categories'])
        book['quotes_list'] = parse_json_field(book['quotes'])
        book['main_characters_list'] = parse_json_field(book['main_characters'])
    
    return books


def generate_data_json(books):
    """Generate minimal JSON data for the frontend."""
    data = {
        'books': [],
        'stats': {
            'total': len(books),
            'read': sum(1 for b in books if b['read_status'] == 'read'),
            'to_read': sum(1 for b in books if b['read_status'] == 'to_read'),
        },
        'authors': defaultdict(list),
        'themes': defaultdict(list),
        'major_themes': defaultdict(list),
        'categories': defaultdict(list),
    }
    
    ratings = [b['rating'] for b in books if b['rating']]
    data['stats']['avg_rating'] = round(sum(ratings) / len(ratings), 1) if ratings else 0
    
    for book in books:
        book_data = {
            'id': book['id'],
            'title': book['title'],
            'authors': book['authors_list'],
            'read_status': book['read_status'],
            'rating': book['rating'],
            'date_added': book['date_added'][:10] if book['date_added'] else '',
            'publication_date': book['publication_date'] or '',
            'fiction': book['fiction_nonfiction'] or '',
            'synopsis': book['synopsis'] or '',
            'themes': book['themes_list'],
            'major_theme': book['major_theme'] or '',
            'characters': book['main_characters_list'],
            'quotes': book['quotes_list'],
            'awards': book['awards'] or '',
            'categories': book['user_categories_list'] + book['llm_categories_list'],
            'notes': book['personal_notes'] or '',
        }
        data['books'].append(book_data)
        
        for author in book['authors_list']:
            if book['id'] not in data['authors'][author]:
                data['authors'][author].append(book['id'])
        
        for theme in book['themes_list']:
            if book['id'] not in data['themes'][theme]:
                data['themes'][theme].append(book['id'])
        
        if book['major_theme']:
            if book['id'] not in data['major_themes'][book['major_theme']]:
                data['major_themes'][book['major_theme']].append(book['id'])
        
        for cat in book_data['categories']:
            if book['id'] not in data['categories'][cat]:
                data['categories'][cat].append(book['id'])
    
    # Convert defaultdicts to regular dicts for JSON
    data['authors'] = dict(data['authors'])
    data['themes'] = dict(data['themes'])
    data['major_themes'] = dict(data['major_themes'])
    data['categories'] = dict(data['categories'])
    
    return data


def generate_html():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Paul's Library</title>
    <style>
        :root {
            --bg: #ffffff;
            --bg-card: #f8f9fa;
            --text: #2c3e50;
            --text-muted: #7f8c8d;
            --accent: #8b2942;
            --accent-hover: #6b1d32;
            --border: #e0e0e0;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: Georgia, serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        .back-link {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 0.85rem;
            margin-bottom: 1.5rem;
        }
        .back-link a { color: var(--text-muted); text-decoration: none; }
        .back-link a:hover { color: var(--accent); }
        h1 { color: var(--accent); font-size: 2.5rem; font-weight: normal; text-align: center; margin-bottom: 0.5rem; }
        .subtitle { text-align: center; color: var(--text-muted); font-style: italic; margin-bottom: 2rem; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .stat {
            background: var(--bg-card);
            padding: 1.25rem;
            text-align: center;
            border: 2px solid var(--border);
            border-radius: 8px;
        }
        .stat-value { font-size: 2rem; color: var(--accent); }
        .stat-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; font-family: -apple-system, sans-serif; }
        .nav-tabs {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 2rem;
            border-bottom: 2px solid var(--border);
            padding-bottom: 1rem;
        }
        .nav-tab {
            padding: 0.5rem 1rem;
            background: var(--bg-card);
            border: 2px solid var(--border);
            border-radius: 6px;
            cursor: pointer;
            font-family: -apple-system, sans-serif;
            font-size: 0.9rem;
            transition: all 0.2s;
        }
        .nav-tab:hover, .nav-tab.active { background: var(--accent); color: white; border-color: var(--accent); }
        .search-box {
            width: 100%;
            padding: 0.75rem 1rem;
            font-size: 1rem;
            border: 2px solid var(--border);
            border-radius: 8px;
            margin-bottom: 1.5rem;
            font-family: Georgia, serif;
        }
        .search-box:focus { outline: none; border-color: var(--accent); }
        .filter-section { margin-bottom: 2rem; }
        .filter-title { font-size: 1.1rem; margin-bottom: 1rem; color: var(--text); }
        .filter-tags { display: flex; flex-wrap: wrap; gap: 0.5rem; }
        .filter-tag {
            padding: 0.4rem 0.8rem;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85rem;
            font-family: -apple-system, sans-serif;
            transition: all 0.2s;
        }
        .filter-tag:hover { border-color: var(--accent); color: var(--accent); }
        .filter-tag .count { color: var(--text-muted); margin-left: 0.3rem; }
        .book-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
        }
        .book-card {
            background: var(--bg-card);
            padding: 1.5rem;
            border: 2px solid var(--border);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .book-card:hover { border-color: var(--accent); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(139,41,66,0.1); }
        .book-card h3 { font-size: 1.05rem; font-weight: 600; margin-bottom: 0.5rem; font-family: -apple-system, sans-serif; }
        .book-card .author { color: var(--text-muted); font-style: italic; font-size: 0.95rem; }
        .book-card .meta { font-size: 0.85rem; color: var(--text-muted); margin-top: 0.75rem; font-family: -apple-system, sans-serif; }
        .book-card .rating { color: var(--accent); }
        .book-card .major-theme { 
            display: inline-block;
            background: var(--accent);
            color: white;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.7rem;
            margin-top: 0.5rem;
            font-family: -apple-system, sans-serif;
        }
        .status { 
            display: inline-block;
            padding: 0.2rem 0.5rem;
            font-size: 0.7rem;
            text-transform: uppercase;
            border-radius: 4px;
            font-family: -apple-system, sans-serif;
        }
        .status.read { background: #d4edda; color: #155724; }
        .status.to_read { background: #fff3cd; color: #856404; }
        
        /* Modal */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            overflow-y: auto;
            padding: 2rem;
        }
        .modal-overlay.active { display: block; }
        .modal {
            background: white;
            max-width: 700px;
            margin: 0 auto;
            border-radius: 12px;
            padding: 2rem;
            position: relative;
        }
        .modal-close {
            position: absolute;
            top: 1rem; right: 1rem;
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: var(--text-muted);
        }
        .modal-close:hover { color: var(--accent); }
        .modal h2 { color: var(--accent); margin-bottom: 0.5rem; font-weight: normal; }
        .modal .author { font-style: italic; color: var(--text-muted); margin-bottom: 1rem; font-size: 1.1rem; }
        .modal .meta-row { margin: 1rem 0; }
        .modal .label { font-weight: 600; color: var(--text-muted); font-size: 0.85rem; text-transform: uppercase; font-family: -apple-system, sans-serif; }
        .modal .themes { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem; }
        .modal .theme-tag {
            background: var(--bg-card);
            padding: 0.3rem 0.6rem;
            border-radius: 4px;
            font-size: 0.85rem;
            border: 1px solid var(--border);
        }
        .modal .synopsis { line-height: 1.8; margin: 1rem 0; }
        .modal .quotes { background: var(--bg-card); padding: 1rem; border-radius: 8px; margin: 1rem 0; font-style: italic; }
        
        .results-count { color: var(--text-muted); margin-bottom: 1rem; font-family: -apple-system, sans-serif; }
        footer { margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid var(--border); color: var(--text-muted); font-size: 0.85rem; text-align: center; font-family: -apple-system, sans-serif; }
    </style>
</head>
<body>
    <div class="back-link"><a href="https://pauls-collections.vercel.app">← All Collections</a></div>
    <h1>Paul's Library</h1>
    <p class="subtitle">A personal collection of books</p>
    
    <div class="stats" id="stats"></div>
    
    <div class="nav-tabs">
        <button class="nav-tab active" data-view="all">All Books</button>
        <button class="nav-tab" data-view="authors">Authors</button>
        <button class="nav-tab" data-view="themes">Themes</button>
        <button class="nav-tab" data-view="major-themes">Major Themes</button>
        <button class="nav-tab" data-view="categories">Categories</button>
    </div>
    
    <input type="text" class="search-box" id="search" placeholder="Search books, authors, themes...">
    
    <div id="filters" class="filter-section" style="display:none;"></div>
    <div class="results-count" id="results-count"></div>
    <div class="book-grid" id="books"></div>
    
    <div class="modal-overlay" id="modal">
        <div class="modal">
            <button class="modal-close" onclick="closeModal()">&times;</button>
            <div id="modal-content"></div>
        </div>
    </div>
    
    <footer>Generated <span id="timestamp"></span></footer>
    
    <script>
    let DATA = null;
    let currentView = 'all';
    let currentFilter = null;
    
    async function init() {
        const resp = await fetch('data.json');
        DATA = await resp.json();
        document.getElementById('timestamp').textContent = new Date().toLocaleDateString();
        renderStats();
        renderBooks(DATA.books);
        setupEventListeners();
    }
    
    function renderStats() {
        const s = DATA.stats;
        document.getElementById('stats').innerHTML = `
            <div class="stat"><div class="stat-value">${s.total}</div><div class="stat-label">Books</div></div>
            <div class="stat"><div class="stat-value">${s.read}</div><div class="stat-label">Read</div></div>
            <div class="stat"><div class="stat-value">${s.to_read}</div><div class="stat-label">To Read</div></div>
            <div class="stat"><div class="stat-value">${s.avg_rating}</div><div class="stat-label">Avg Rating</div></div>
            <div class="stat"><div class="stat-value">${Object.keys(DATA.authors).length}</div><div class="stat-label">Authors</div></div>
            <div class="stat"><div class="stat-value">${Object.keys(DATA.major_themes).length}</div><div class="stat-label">Major Themes</div></div>
        `;
    }
    
    function renderBooks(books) {
        document.getElementById('results-count').textContent = `${books.length} book${books.length !== 1 ? 's' : ''}`;
        document.getElementById('books').innerHTML = books.map(b => `
            <div class="book-card" onclick="showBook(${b.id})">
                <h3>${esc(b.title)}</h3>
                <div class="author">${esc(b.authors.join(', '))}</div>
                <div class="meta">
                    <span class="status ${b.read_status}">${b.read_status === 'read' ? 'Read' : 'To Read'}</span>
                    ${b.rating ? `<span class="rating"> ${'★'.repeat(b.rating)}${'☆'.repeat(10-b.rating)}</span>` : ''}
                </div>
                ${b.major_theme ? `<span class="major-theme">${esc(b.major_theme)}</span>` : ''}
            </div>
        `).join('');
    }
    
    function renderFilters(type) {
        let items = [];
        if (type === 'authors') items = Object.entries(DATA.authors).map(([k,v]) => [k, v.length]).sort((a,b) => b[1]-a[1]);
        else if (type === 'themes') items = Object.entries(DATA.themes).map(([k,v]) => [k, v.length]).sort((a,b) => b[1]-a[1]);
        else if (type === 'major-themes') items = Object.entries(DATA.major_themes).map(([k,v]) => [k, v.length]).sort((a,b) => b[1]-a[1]);
        else if (type === 'categories') items = Object.entries(DATA.categories).map(([k,v]) => [k, v.length]).sort((a,b) => b[1]-a[1]);
        
        if (items.length === 0) {
            document.getElementById('filters').style.display = 'none';
            return;
        }
        
        document.getElementById('filters').style.display = 'block';
        document.getElementById('filters').innerHTML = `
            <div class="filter-title">${type.replace('-', ' ').replace(/\\b\\w/g, l => l.toUpperCase())} (${items.length})</div>
            <div class="filter-tags">
                ${items.map(([name, count]) => `<span class="filter-tag" data-filter="${esc(name)}">${esc(name)}<span class="count">(${count})</span></span>`).join('')}
            </div>
        `;
    }
    
    function filterBooks(type, value) {
        let ids = [];
        if (type === 'authors') ids = DATA.authors[value] || [];
        else if (type === 'themes') ids = DATA.themes[value] || [];
        else if (type === 'major-themes') ids = DATA.major_themes[value] || [];
        else if (type === 'categories') ids = DATA.categories[value] || [];
        
        const books = DATA.books.filter(b => ids.includes(b.id));
        renderBooks(books);
    }
    
    function searchBooks(query) {
        const q = query.toLowerCase();
        const books = DATA.books.filter(b => 
            b.title.toLowerCase().includes(q) ||
            b.authors.some(a => a.toLowerCase().includes(q)) ||
            b.themes.some(t => t.toLowerCase().includes(q)) ||
            (b.major_theme && b.major_theme.toLowerCase().includes(q)) ||
            (b.synopsis && b.synopsis.toLowerCase().includes(q))
        );
        renderBooks(books);
    }
    
    function showBook(id) {
        const b = DATA.books.find(x => x.id === id);
        if (!b) return;
        
        document.getElementById('modal-content').innerHTML = `
            <h2>${esc(b.title)}</h2>
            <div class="author">${esc(b.authors.join(', '))}</div>
            <div class="meta-row">
                <span class="status ${b.read_status}">${b.read_status === 'read' ? 'Read' : 'To Read'}</span>
                ${b.rating ? `<span class="rating"> ${'★'.repeat(b.rating)}${'☆'.repeat(10-b.rating)} ${b.rating}/10</span>` : ''}
                ${b.fiction ? ` • ${esc(b.fiction)}` : ''}
                ${b.publication_date ? ` • ${esc(b.publication_date)}` : ''}
            </div>
            ${b.major_theme ? `<div class="meta-row"><span class="label">Major Theme:</span> ${esc(b.major_theme)}</div>` : ''}
            ${b.synopsis ? `<div class="meta-row"><span class="label">Synopsis</span><div class="synopsis">${esc(b.synopsis)}</div></div>` : ''}
            ${b.themes.length ? `<div class="meta-row"><span class="label">Themes</span><div class="themes">${b.themes.map(t => `<span class="theme-tag">${esc(t)}</span>`).join('')}</div></div>` : ''}
            ${b.characters.length ? `<div class="meta-row"><span class="label">Characters:</span> ${esc(b.characters.join(', '))}</div>` : ''}
            ${b.quotes.length ? `<div class="meta-row"><span class="label">Quotes</span><div class="quotes">${b.quotes.map(q => `<p>"${esc(q)}"</p>`).join('')}</div></div>` : ''}
            ${b.awards ? `<div class="meta-row"><span class="label">Awards:</span> ${esc(b.awards)}</div>` : ''}
            ${b.notes ? `<div class="meta-row"><span class="label">Notes:</span> ${esc(b.notes)}</div>` : ''}
            <div class="meta-row" style="color: var(--text-muted); font-size: 0.85rem;">Added: ${b.date_added}</div>
        `;
        document.getElementById('modal').classList.add('active');
    }
    
    function closeModal() {
        document.getElementById('modal').classList.remove('active');
    }
    
    function setupEventListeners() {
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                currentView = tab.dataset.view;
                currentFilter = null;
                document.getElementById('search').value = '';
                
                if (currentView === 'all') {
                    document.getElementById('filters').style.display = 'none';
                    renderBooks(DATA.books);
                } else {
                    renderFilters(currentView);
                    renderBooks(DATA.books);
                }
            });
        });
        
        document.getElementById('filters').addEventListener('click', e => {
            if (e.target.classList.contains('filter-tag')) {
                currentFilter = e.target.dataset.filter;
                filterBooks(currentView, currentFilter);
            }
        });
        
        document.getElementById('search').addEventListener('input', e => {
            if (e.target.value) searchBooks(e.target.value);
            else if (currentFilter) filterBooks(currentView, currentFilter);
            else renderBooks(DATA.books);
        });
        
        document.getElementById('modal').addEventListener('click', e => {
            if (e.target.id === 'modal') closeModal();
        });
        
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape') closeModal();
        });
    }
    
    function esc(s) { 
        if (!s) return '';
        return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); 
    }
    
    init();
    </script>
</body>
</html>'''


def generate_site():
    print("Generating books SPA...")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    books = get_all_books(DB_PATH)
    print(f"Found {len(books)} books")
    
    # Generate data.json
    data = generate_data_json(books)
    with open(os.path.join(OUTPUT_DIR, 'data.json'), 'w') as f:
        json.dump(data, f)
    print("Generated data.json")
    
    # Generate index.html
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w') as f:
        f.write(generate_html())
    print("Generated index.html")
    
    print(f"\n✓ Site generated in '{OUTPUT_DIR}/' (2 files)")


if __name__ == "__main__":
    generate_site()
