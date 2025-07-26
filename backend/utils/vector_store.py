import weaviate
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import uuid

# Initialize global model
_model = SentenceTransformer('all-MiniLM-L6-v2')
_embedding_dimension = _model.get_sentence_embedding_dimension()

# Global variables for Weaviate client
client = None
CLASS_NAME = "Chunk"

# Simple in-memory fallback for testing
_in_memory_chunks = []
_in_memory_embeddings = []

def _get_client():
    """Get or create Weaviate client with connection."""
    global client
    if client is None:
        try:
            # Connect to local Weaviate (self-hosted Docker) - Updated to v4 API
            client = weaviate.WeaviateClient(weaviate.connect.ConnectionParams.from_url("http://localhost:8080", grpc_port=50051))
            client.connect()
            print("Connected to Weaviate successfully.")
        except Exception as e:
            print(f"Warning: Could not connect to Weaviate: {e}")
            print("Please ensure Weaviate is running on localhost:8080")
            return None
    return client

# Schema setup (if not already created) - Updated to v4 API
def setup_schema():
    client = _get_client()
    if client is None:
        return False
    
    try:
        if client.collections.exists(CLASS_NAME):
            return True
        
        client.collections.create(
            name=CLASS_NAME,
            vectorizer_config=weaviate.config.Configure.Vectorizer.none(),  # We're using custom embeddings
            properties=[
                weaviate.config.Property(name="text", data_type=weaviate.config.DataType.TEXT),
                weaviate.config.Property(name="original_html_context", data_type=weaviate.config.DataType.TEXT),
                weaviate.config.Property(name="path", data_type=weaviate.config.DataType.TEXT)
            ]
        )
        return True
    except Exception as e:
        print(f"Error setting up schema: {e}")
        return False

# Replaces FAISS index + chunk metadata wipe - Updated to v4 API
def clear_vector_store():
    """
    Clears all vector data from Weaviate (entire Chunk class objects).
    """
    global _in_memory_chunks, _in_memory_embeddings
    
    # Clear in-memory storage
    _in_memory_chunks = []
    _in_memory_embeddings = []
    
    if not setup_schema():
        print("Could not setup schema, using in-memory fallback.")
        return
    
    try:
        client = _get_client()
        if client is None:
            return
        
        client.collections.delete_many(
            collection_name=CLASS_NAME,
            where=weaviate.classes.query.Filter.by_property("text").not_equal(None)
        )
        print("Vector store cleared.")
    except Exception as e:
        print(f"Error clearing vector store: {e}")

# Replaces FAISS add() and _chunks_metadata.extend() - Updated to v4 API
def embed_and_index_chunks(chunks: List[Dict]):
    """
    Embeds and inserts text chunks into Weaviate with metadata.
    """
    global _in_memory_chunks, _in_memory_embeddings
    
    if not chunks:
        return

    # Generate embeddings
    texts = [c["text"] for c in chunks]
    embeddings = _model.encode(texts).tolist()
    
    # Store in memory for fallback
    _in_memory_chunks.extend(chunks)
    _in_memory_embeddings.extend(embeddings)

    client = _get_client()
    if client is None:
        print("Could not connect to Weaviate, using in-memory storage.")
        print(f"Indexed {len(chunks)} chunks in memory.")
        return

    try:
        # Insert chunks with their embeddings
        collection = client.collections.get(CLASS_NAME)
        for chunk, embedding in zip(chunks, embeddings):
            collection.data.insert(
                properties={
                    "text": chunk["text"],
                    "original_html_context": chunk["original_html_context"],
                    "path": chunk["path"]
                },
                vector=embedding
            )
        print(f"Indexed {len(chunks)} chunks.")
    except Exception as e:
        print(f"Error indexing chunks: {e}")

# Replaces FAISS search() and indexed metadata lookup - Updated to v4 API
def search_chunks_in_store(query: str, top_k: int = 10) -> List[Dict]:
    """
    Searches Weaviate for the most relevant text chunks by query.
    Returns chunk with same structure as before (including score).
    """
    global _in_memory_chunks, _in_memory_embeddings
    
    # Generate query embedding
    query_vector = _model.encode([query])[0].tolist()
    
    # Simple cosine similarity search for in-memory fallback
    if _in_memory_chunks and _in_memory_embeddings:
        import numpy as np
        
        # Calculate cosine similarities
        similarities = []
        for embedding in _in_memory_embeddings:
            # Convert to numpy arrays for calculation
            query_np = np.array(query_vector)
            embed_np = np.array(embedding)
            
            # Calculate cosine similarity
            dot_product = np.dot(query_np, embed_np)
            norm_query = np.linalg.norm(query_np)
            norm_embed = np.linalg.norm(embed_np)
            
            if norm_query > 0 and norm_embed > 0:
                similarity = dot_product / (norm_query * norm_embed)
            else:
                similarity = 0
                
            similarities.append(similarity)
        
        # Get top-k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Only include positive similarities
                results.append({
                    "text": _in_memory_chunks[idx]["text"],
                    "original_html_context": _in_memory_chunks[idx]["original_html_context"],
                    "path": _in_memory_chunks[idx]["path"],
                    "score": round(similarities[idx], 4)
                })
        
        print(f"Found {len(results)} results using in-memory search.")
        return results

    client = _get_client()
    if client is None:
        print("Could not connect to Weaviate, returning empty results.")
        return []

    try:
        # Use the correct Weaviate v4 API for vector search
        result = client.collections.get(CLASS_NAME).with_near_vector({
            "vector": query_vector
        }).with_limit(top_k).with_additional(["distance"]).do()

        matches = result.objects
        
        # Convert to previous format + include distance as score (lower distance is better, so we invert)
        return [
            {
                "text": m.properties["text"],
                "original_html_context": m.properties["original_html_context"],
                "path": m.properties["path"],
                "score": round(1 - m.metadata.distance, 4)  # Convert distance to similarity score
            }
            for m in matches
        ]
    except Exception as e:
        print(f"Error searching chunks: {e}")
        return []
