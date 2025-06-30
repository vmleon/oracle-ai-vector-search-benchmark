import logging
from models import get_model, is_model_ready
from database import search_similar_chunks

logger = logging.getLogger(__name__)

def search_documents(query_text, limit=10, similarity_threshold=0.7):
    """Search for similar document chunks using vector similarity."""
    if not is_model_ready():
        raise Exception("Model not ready")
    
    # Generate embedding for the query
    model = get_model()
    query_output = model.embed([query_text])
    query_embedding = query_output[0].outputs.embedding
    
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