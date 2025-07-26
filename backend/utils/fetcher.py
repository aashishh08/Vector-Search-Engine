from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import re
import asyncio
from typing import List, Dict

def slugify(text: str) -> str:
    """Converts a string to a URL-friendly slug."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)  # Replace non-alphanumeric with hyphens
    return text.strip('-')  # Remove leading/trailing hyphens

async def fetch_and_parse_html(url: str) -> List[Dict[str, str]]:
    """
    Fetches HTML content from the given URL and parses it into logical content blocks.
    Removes script and style tags and extracts meaningful content.
    """
    try:
        # Enhanced headers to look more like a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        print(f"🌐 Fetching content from: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
    except requests.exceptions.RequestException as e:
        print(f"💥 Error fetching URL {url}: {e}")
        raise e

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove non-content tags that are not relevant for search
    unwanted_tags = [
        "script", "style", "noscript", "iframe", "object", "embed", "canvas",
        "svg", "button", "input", "select", "textarea"
    ]
    
    for tag_name in unwanted_tags:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Identify potential content blocks. Prioritize semantic HTML5 tags.
    # Also include common div patterns that might contain main content.
    content_selectors = [
        "main",                    # HTML5 main content
        "article",                 # Article content
        "section",                 # Section content
        "div.content",             # Common content class
        "div.main-content",        # Common main content class
        "div.post-content",        # Blog post content
        "div.entry-content",       # Entry content
        "div.article-body",        # Article body
        "div.text-content",        # Text content
        ".post-body",              # Post body class
        "p"                        # Fallback to paragraphs
    ]
    
    blocks = []
    for selector in content_selectors:
        blocks.extend(soup.select(selector))

    seen_texts = set()  # To deduplicate content blocks
    chunks_data = []
    base_path = urlparse(url).path or "/"
    
    print(f"📝 Processing {len(blocks)} potential content blocks...")

    for block in blocks:
        # Get the text content of the block
        text = block.get_text(separator=" ", strip=True)
        
        # More sophisticated text cleaning
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = text.strip()
        
        # Skip if block has very little text or is a duplicate
        if len(text) < 30 or text in seen_texts:  # Reduced minimum length
            continue
            
        seen_texts.add(text)

        # Attempt to find a meaningful heading within or near the block
        heading_tag = block.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        # If no heading in block, look for preceding heading
        if not heading_tag:
            previous_elements = block.find_all_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if previous_elements:
                heading_tag = previous_elements[0]
        
        heading = heading_tag.get_text(strip=True) if heading_tag else None

        # Construct a meaningful path for this block
        current_path = base_path
        if heading:
            current_path = f"{base_path}#{slugify(heading)}"
        elif block.get('id'):
            current_path = f"{base_path}#{slugify(block['id'])}"
        elif block.get('class'):
            # Use first meaningful class name
            classes = [cls for cls in block['class'] if not cls.startswith('css-')]
            if classes:
                current_path = f"{base_path}#{slugify(classes[0])}"

        # Store the block data
        chunks_data.append({
            "html": str(block),  # Convert to string for consistency
            "text": text,
            "path": current_path
        })

    print(f"✅ Extracted {len(chunks_data)} meaningful content blocks")
    
    # Sort by content length (longer content first) to prioritize substantial blocks
    chunks_data.sort(key=lambda x: len(x["text"]), reverse=True)
    
    return chunks_data