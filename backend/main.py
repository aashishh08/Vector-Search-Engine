from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import requests

from utils.fetcher import fetch_and_parse_html
from utils.tokenizer import chunk_text
from utils.vector_store import embed_and_index_chunks, search_chunks_in_store, clear_vector_store
from bs4 import BeautifulSoup

app = FastAPI(title="Website Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    url: str
    query: str

class SearchResult(BaseModel):
    chunk_content: str
    original_html_context: str
    path: str
    relevance_score: float
    match_percentage: float

def find_element_containing_text(soup, text_chunk):
    """Find the first div that contains the given text chunk."""
    # Clean the text chunk for comparison
    clean_chunk = ' '.join(text_chunk.split())
    
    # First, find the innermost element that contains the text
    innermost_element = None
    for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span', 'li', 'article', 'section']):
        element_text = ' '.join(element.get_text().split())
        
        # If this element contains our text chunk, remember it
        if clean_chunk in element_text:
            innermost_element = element
            break
    
    if not innermost_element:
        return str(soup)
    
    # For very long text chunks, try to find a more specific div
    if len(clean_chunk) > 500:  # If text is very long
        # Look for divs with specific classes that might contain the content
        for div in soup.find_all('div', class_=True):
            div_text = ' '.join(div.get_text().split())
            if clean_chunk in div_text and len(div_text) < 2000:
                return str(div)
    
    # Now find the first div that contains this element, but limit the search
    current_element = innermost_element
    search_depth = 0
    max_depth = 5  # Limit how far up we search to avoid getting the entire page
    
    while current_element and search_depth < max_depth:
        if current_element.name == 'div':
            # Check if this div is not too large (avoid page-level divs)
            div_text = ' '.join(current_element.get_text().split())
            # Use a smaller limit and prefer smaller divs
            if len(div_text) < 800:  # Even more aggressive limit
                return str(current_element)
        current_element = current_element.parent
        search_depth += 1
    
    # If no suitable div found, try to find a smaller div with a reasonable size
    current_element = innermost_element
    while current_element:
        if current_element.name == 'div':
            div_text = ' '.join(current_element.get_text().split())
            if len(div_text) < 2000:  # Reduced fallback limit
                return str(current_element)
        current_element = current_element.parent
    
    # If no suitable div found, return the innermost element
    return str(innermost_element)

@app.post("/search", response_model=List[SearchResult])
async def search_website_content(payload: SearchRequest):
    """Search website content for relevant text chunks."""
    try:
        clear_vector_store()

        print(f"Fetching content from: {payload.url}")
        html_blocks = await fetch_and_parse_html(payload.url)
        print(f"Found {len(html_blocks)} HTML blocks")

        if not html_blocks:
            raise HTTPException(status_code=404, detail="No readable content found.")

        # Process blocks into searchable chunks
        chunks_for_indexing = []
        for block in html_blocks:
            text_chunks = chunk_text(block["text"], max_tokens=500)
            print(f"Block '{block['path']}' generated {len(text_chunks)} chunks")
            
            # Parse the HTML to find specific elements
            soup = BeautifulSoup(block["html"], "html.parser")
            
            for text_chunk in text_chunks:
                # Find the specific element that contains this text chunk
                specific_html = find_element_containing_text(soup, text_chunk)
                
                chunks_for_indexing.append({
                    "text": text_chunk,
                    "original_html_context": specific_html,
                    "path": block["path"]
                })

        print(f"Total chunks for indexing: {len(chunks_for_indexing)}")
        if not chunks_for_indexing:
            raise HTTPException(status_code=404, detail="No text chunks could be generated.")

        embed_and_index_chunks(chunks_for_indexing)
        raw_results = search_chunks_in_store(payload.query, top_k=10)

        # Convert scores to percentages with improved scaling
        final_results = []
        for r in raw_results:
            # Enhanced percentage calculation for better user experience
            base_percentage = r["score"] * 100
            # Boost scores to make them more meaningful (60-95% range instead of 40-60%)
            adjusted_percentage = min(95.0, max(60.0, base_percentage * 1.3))

            final_results.append(SearchResult(
                chunk_content=r["text"],
                original_html_context=r["original_html_context"],
                path=r["path"],
                relevance_score=r["score"],
                match_percentage=round(adjusted_percentage, 2)
            ))

        return final_results

    except HTTPException:
        raise
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="Request timed out.")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=502, detail="Could not connect to URL.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")