import logging
import oracledb
import array
from .connection import get_db_pool, is_db_ready

logger = logging.getLogger(__name__)



def store_document_chunks_without_embeddings(document_id, chunks):
    """Store document chunks without embeddings."""
    if not is_db_ready():
        raise Exception("Database not ready")
    
    db_pool = get_db_pool()
    with db_pool.acquire() as connection:
        cursor = connection.cursor()
        
        # Clear existing chunks for this document
        cursor.execute("DELETE FROM document_chunks WHERE document_id = :doc_id", [document_id])
        
        # Insert new chunks without embeddings
        for i, chunk_text in enumerate(chunks):
            cursor.execute("""
                INSERT INTO document_chunks (document_id, chunk_index, chunk_text, chunk_size)
                VALUES (:doc_id, :chunk_idx, :chunk_text, :chunk_size)
            """, {
                'doc_id': document_id,
                'chunk_idx': i,
                'chunk_text': chunk_text,
                'chunk_size': len(chunk_text)
            })
        
        connection.commit()
        logger.info(f"Stored {len(chunks)} chunks without embeddings for document {document_id}")

def update_chunk_embedding(document_id, chunk_index, embedding):
    """Update a specific chunk with its embedding."""
    if not is_db_ready():
        raise Exception("Database not ready")
    
    db_pool = get_db_pool()
    with db_pool.acquire() as connection:
        cursor = connection.cursor()
        
        # Convert embedding list to proper format for Oracle VECTOR type
        if isinstance(embedding, list):
            embedding_array = array.array('f', embedding)
        else:
            embedding_array = embedding
        
        cursor.execute("""
            UPDATE document_chunks 
            SET embedding = :embedding 
            WHERE document_id = :doc_id AND chunk_index = :chunk_idx
        """, {
            'embedding': embedding_array,
            'doc_id': document_id,
            'chunk_idx': chunk_index
        })
        
        connection.commit()
        logger.info(f"Updated embedding for chunk {chunk_index} of document {document_id}")