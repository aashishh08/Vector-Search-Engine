from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import requests

from utils.fetcher import fetch_and_parse_html
from utils.tokenizer import chunk_text
from utils.vector_store import embed_and_index_chunks, search_chunks_in_store, clear_vector_store

# Create FastAPI app
app = FastAPI(
    title="Website Content Search API",
    description="API for fetching, parsing, chunking, and semantically searching website content."
)

# CORS setup to allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development. In production, specify your frontend URL.
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Request schema for the search endpoint
class SearchRequest(BaseModel):
    url: str
    query: str

# Response schema for a single search result
class SearchResult(BaseModel):
    chunk_content: str # The 500-token chunk that matched
    original_html_context: str # The larger HTML block where the chunk was found
    path: str # The path/slug of the section
    relevance_score: float # The raw FAISS distance score
    match_percentage: float # Calculated percentage match

@app.post("/search", response_model=List[SearchResult])
async def search_website_content(payload: SearchRequest):
    """
    Endpoint to search content of a given URL based on a query.
    Fetches HTML, parses it into logical blocks, chunks text within blocks,
    embeds and indexes these chunks, then performs a semantic search.
    """
    try:
        # Clear the vector store for each new request to avoid mixing content from different URLs.
        # This assumes a stateless, per-request indexing approach.
        clear_vector_store()

        # 1. Fetch structured HTML blocks and their text content
        # This function now returns a list of dictionaries, where each dict contains
        # 'html' (the original block's HTML), 'text' (the block's plain text), and 'path'.
        print(f"Fetching content from: {payload.url}")
        html_blocks = await fetch_and_parse_html(payload.url)
        print(f"Found {len(html_blocks)} HTML blocks")

        if not html_blocks:
            raise HTTPException(status_code=404, detail="No readable content found or URL is inaccessible.")

        # 2. Tokenize and chunk the text from each HTML block into max_tokens=500 segments
        # We need to map these smaller chunks back to their original HTML context and path.
        chunks_for_indexing = []
        for block in html_blocks:
            # Chunk the text content of the block
            text_chunks_from_block = chunk_text(block["text"], max_tokens=500)
            print(f"Block '{block['path']}' generated {len(text_chunks_from_block)} chunks")
            for text_chunk in text_chunks_from_block:
                chunks_for_indexing.append({
                    "text": text_chunk, # This is the actual chunk to embed
                    "original_html_context": block["html"], # Keep reference to the full HTML block for display
                    "path": block["path"] # Keep reference to the path
                })

        print(f"Total chunks for indexing: {len(chunks_for_indexing)}")
        if not chunks_for_indexing:
            raise HTTPException(status_code=404, detail="No text chunks could be generated from the content.")

        # 3. Embed and index the generated chunks
        # This function will add the embeddings and metadata to the in-memory FAISS index and store.
        embed_and_index_chunks(chunks_for_indexing)

        # 4. Perform semantic search using the query
        # This returns the top_k results with their raw FAISS L2 distances.
        raw_results = search_chunks_in_store(payload.query, top_k=10)

        # 5. Convert similarity score to a percentage match for better interpretability
        final_results = []
        for r in raw_results:
            # The score is now a similarity score (0-1, where 1 is most similar)
            # Convert to percentage (0-100)
            similarity_score = r["score"]
            match_percentage = max(0.0, min(100.0, similarity_score * 100))

            final_results.append(SearchResult(
                chunk_content=r["text"],
                original_html_context=r["original_html_context"],
                path=r["path"],
                relevance_score=r["score"],
                match_percentage=round(match_percentage, 2)
            ))

        return final_results

    except HTTPException as e:
        # Re-raise HTTPExceptions to be handled by FastAPI's error handling
        raise e
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="Request to target URL timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=502, detail="Could not connect to the target URL. Please check the URL.")
    except Exception as e:
        # Catch any other unexpected errors
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")