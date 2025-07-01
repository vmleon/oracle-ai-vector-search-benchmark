import logging
import requests
import os
from database import search_similar_chunks

logger = logging.getLogger(__name__)

def search_documents(query_text, limit=10, similarity_threshold=0.7):
    """Search for similar document chunks using vector similarity."""
    
    # Get embedding from vector_maker_service
    vector_service_url = os.getenv('VECTOR_SERVICE_URL', 'http://localhost:8001')
    
    try:
        response = requests.post(
            f"{vector_service_url}/embeddings",
            json={"texts": [query_text]},
            timeout=30
        )
        response.raise_for_status()
        
        embeddings_data = response.json()
        query_embedding = embeddings_data['embeddings'][0]['embedding']
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get embedding from vector service: {e}")
        raise Exception(f"Vector service unavailable: {e}")
    except (KeyError, IndexError) as e:
        logger.error(f"Invalid response from vector service: {e}")
        raise Exception(f"Invalid embedding response: {e}")
    
    # Search for similar chunks
    results = search_similar_chunks(
        query_embedding=query_embedding,
        limit=limit,
        similarity_threshold=similarity_threshold
    )
    
    return {
        'query': query_text,
        'results_count': len(results),
        'results': results
    }