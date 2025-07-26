# Website Content Search API Backend

A FastAPI backend that fetches, parses, chunks, and semantically searches website content using Weaviate as the vector database.

## Features

- **Web Scraping**: Fetches and parses HTML content from any website
- **Text Chunking**: Breaks down content into manageable 500-token chunks
- **Semantic Search**: Uses sentence transformers for embedding and similarity search
- **Vector Database**: Stores embeddings in Weaviate for fast retrieval
- **REST API**: Clean FastAPI endpoints for search operations

## Prerequisites

- Python 3.8+
- Weaviate instance (local or cloud)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Weaviate (optional - the app will work without it but with limited functionality):
   - **Local setup**: Run Weaviate using Docker
   ```bash
   docker run -d \
     --name weaviate \
     -p 8080:8080 \
     -p 50051:50051 \
     -e QUERY_DEFAULTS_LIMIT=25 \
     -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
     -e PERSISTENCE_DATA_PATH='/var/lib/weaviate' \
     -e DEFAULT_VECTORIZER_MODULE='none' \
     -e ENABLE_MODULES='' \
     -e CLUSTER_HOSTNAME='node1' \
     semitechnologies/weaviate:1.32.1
   ```

## Usage

1. Start the backend server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. The API will be available at `http://localhost:8000`

3. Use the `/search` endpoint to search website content:
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "query": "your search query"
  }'
```

## API Endpoints

### POST /search
Search for content on a specific website.

**Request Body:**
```json
{
  "url": "https://example.com",
  "query": "search terms"
}
```

**Response:**
```json
[
  {
    "chunk_content": "The actual text chunk that matched",
    "original_html_context": "The full HTML block containing the chunk",
    "path": "The path/section where the chunk was found",
    "relevance_score": 0.85,
    "match_percentage": 85.0
  }
]
```

## Architecture

- **`main.py`**: FastAPI application with search endpoint
- **`utils/fetcher.py`**: HTML fetching and parsing utilities
- **`utils/tokenizer.py`**: Text chunking and tokenization
- **`utils/vector_store.py`**: Weaviate integration for vector storage and search

## Vector Store

The application uses Weaviate v4 as the vector database:
- Automatically creates collections and schemas
- Handles connection failures gracefully
- Uses sentence transformers for embeddings
- Supports similarity search with configurable top-k results

## Error Handling

The application includes comprehensive error handling:
- Connection failures to Weaviate are handled gracefully
- Invalid URLs return appropriate HTTP status codes
- Missing content is reported with descriptive messages
- All operations include try-catch blocks for robustness

## Development

The backend is designed to work both with and without Weaviate:
- If Weaviate is available, full vector search functionality is enabled
- If Weaviate is unavailable, the app will start but return empty search results
- All Weaviate operations are wrapped in error handling
