import weaviate
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import re

# Initialize model - using a better model for improved semantic search
_model = SentenceTransformer('all-mpnet-base-v2')
_embedding_dimension = _model.get_sentence_embedding_dimension()

# Global variables
client = None
CLASS_NAME = "Chunk"

# In-memory fallback
_in_memory_chunks = []
_in_memory_embeddings = []



def calculate_content_relevance(content: str, query: str) -> float:
    """Calculate content relevance boost based on query term presence."""
    content_lower = content.lower()
    query_terms = query.lower().split()
    
    # Count query terms in content
    term_matches = sum(1 for term in query_terms if term in content_lower)
    term_ratio = term_matches / len(query_terms) if query_terms else 0
    
    # Calculate term frequency boost
    total_occurrences = sum(content_lower.count(term) for term in query_terms)
    frequency_boost = min(0.1, total_occurrences * 0.02)  # Max 10% boost
    
    # Calculate proximity boost (terms appearing close together)
    proximity_boost = 0
    if len(query_terms) > 1:
        # Check if multiple terms appear in the same sentence
        sentences = re.split(r'[.!?]+', content)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if all(term in sentence_lower for term in query_terms):
                proximity_boost += 0.05  # 5% boost per sentence with all terms
    
    total_boost = (term_ratio * 0.15) + frequency_boost + min(0.1, proximity_boost)
    return total_boost

def _get_client():
    """Get or create Weaviate client."""
    global client
    if client is None:
        try:
            client = weaviate.WeaviateClient(weaviate.connect.ConnectionParams.from_url("http://localhost:8080", grpc_port=50051))
            client.connect()
            print("Connected to Weaviate successfully.")
        except Exception as e:
            print(f"Warning: Could not connect to Weaviate: {e}")
            print("Please ensure Weaviate is running on localhost:8080")
            return None
    return client

def setup_schema():
    """Setup Weaviate schema."""
    client = _get_client()
    if client is None:
        return False
    
    try:
        if client.collections.exists(CLASS_NAME):
            return True
        
        client.collections.create(
            name=CLASS_NAME,
            vectorizer_config=weaviate.config.Configure.Vectorizer.none(),
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

def clear_vector_store():
    """Clear all vector data."""
    global _in_memory_chunks, _in_memory_embeddings
    
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

def embed_and_index_chunks(chunks: List[Dict]):
    """Embed and index text chunks."""
    global _in_memory_chunks, _in_memory_embeddings
    
    if not chunks:
        return

    texts = [c["text"] for c in chunks]
    embeddings = _model.encode(texts).tolist()
    
    _in_memory_chunks.extend(chunks)
    _in_memory_embeddings.extend(embeddings)

    client = _get_client()
    if client is None:
        print("Could not connect to Weaviate, using in-memory storage.")
        print(f"Indexed {len(chunks)} chunks in memory.")
        return

    try:
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

def search_chunks_in_store(query: str, top_k: int = 10) -> List[Dict]:
    """Search for relevant text chunks."""
    global _in_memory_chunks, _in_memory_embeddings
    
    query_vector = _model.encode([query])[0].tolist()
    
    # In-memory search fallback
    if _in_memory_chunks and _in_memory_embeddings:
        import numpy as np
        
        similarities = []
        for embedding in _in_memory_embeddings:
            query_np = np.array(query_vector)
            embed_np = np.array(embedding)
            
            dot_product = np.dot(query_np, embed_np)
            norm_query = np.linalg.norm(query_np)
            norm_embed = np.linalg.norm(embed_np)
            
            if norm_query > 0 and norm_embed > 0:
                similarity = dot_product / (norm_query * norm_embed)
            else:
                similarity = 0
                
            similarities.append(similarity)
        
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                # Enhanced scoring with content relevance boost
                base_score = similarities[idx]
                content_boost = calculate_content_relevance(_in_memory_chunks[idx]["text"], query)
                final_score = min(1.0, base_score + content_boost)
                
                results.append({
                    "text": _in_memory_chunks[idx]["text"],
                    "original_html_context": _in_memory_chunks[idx]["original_html_context"],
                    "path": _in_memory_chunks[idx]["path"],
                    "score": round(final_score, 4)
                })
        
        print(f"Found {len(results)} results using in-memory search.")
        return results

    client = _get_client()
    if client is None:
        print("Could not connect to Weaviate, returning empty results.")
        return []

    try:
        result = client.collections.get(CLASS_NAME).with_near_vector({
            "vector": query_vector
        }).with_limit(top_k).with_additional(["distance"]).do()

        matches = result.objects
        
        return [
            {
                "text": m.properties["text"],
                "original_html_context": m.properties["original_html_context"],
                "path": m.properties["path"],
                "score": round(1 - m.metadata.distance, 4)
            }
            for m in matches
        ]
    except Exception as e:
        print(f"Error searching chunks: {e}")
        return []
