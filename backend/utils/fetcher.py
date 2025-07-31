from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict

def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

async def fetch_and_parse_html(url: str) -> List[Dict[str, str]]:
    """Fetch and parse HTML into content blocks."""
    try:
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

    # Remove non-content tags
    unwanted_tags = [
        "script", "style", "noscript", "iframe", "object", "embed", "canvas",
        "svg", "button", "input", "select", "textarea"
    ]
    
    for tag_name in unwanted_tags:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Find content blocks
    content_selectors = [
        "main", "article", "section", 
        "div.content", "div.main-content", "div.post-content", 
        "div.entry-content", "div.article-body", "div.text-content",
        ".post-body", "p"
    ]
    
    blocks = []
    for selector in content_selectors:
        blocks.extend(soup.select(selector))

    seen_texts = set()
    chunks_data = []
    base_path = urlparse(url).path or "/"
    
    print(f"📝 Processing {len(blocks)} potential content blocks...")

    for block in blocks:
        text = block.get_text(separator=" ", strip=True)
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) < 50 or text in seen_texts:  # Increased minimum length for better quality
            continue
            
        seen_texts.add(text)

        # Find heading for this block
        heading_tag = block.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not heading_tag:
            previous_elements = block.find_all_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if previous_elements:
                heading_tag = previous_elements[0]
        
        heading = heading_tag.get_text(strip=True) if heading_tag else None

        # Build path
        current_path = base_path
        if heading:
            current_path = f"{base_path}#{slugify(heading)}"
        elif block.get('id'):
            current_path = f"{base_path}#{slugify(block['id'])}"
        elif block.get('class'):
            classes = [cls for cls in block['class'] if not cls.startswith('css-')]
            if classes:
                current_path = f"{base_path}#{slugify(classes[0])}"

        # Find the specific element that contains the main text content
        text_elements = block.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span', 'li'])
        relevant_html = str(block)  # Default to full block
        
        # Try to find the most specific element containing the text
        for element in text_elements:
            element_text = element.get_text(separator=" ", strip=True)
            element_text = re.sub(r'\s+', ' ', element_text).strip()
            
            # If this element contains a significant portion of our text, use it
            if len(element_text) > 20 and element_text in text:
                relevant_html = str(element)
                break
        
        chunks_data.append({
            "html": relevant_html,
            "text": text,
            "path": current_path
        })

    print(f"✅ Extracted {len(chunks_data)} meaningful content blocks")
    
    # Sort by content length and quality
    chunks_data.sort(key=lambda x: len(x["text"]), reverse=True)
    
    # Filter out very short or low-quality content
    quality_chunks = []
    for chunk in chunks_data:
        text = chunk["text"]
        # Check for meaningful content (not just navigation, ads, etc.)
        meaningful_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        word_count = len(text.split())
        meaningful_word_count = sum(1 for word in text.lower().split() if word not in meaningful_words)
        
        if word_count >= 10 and meaningful_word_count >= 5:
            quality_chunks.append(chunk)
    
    print(f"✅ Filtered to {len(quality_chunks)} high-quality content blocks")
    return quality_chunks