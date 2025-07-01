import logging
import oracledb
from .connection import get_db_pool, is_db_ready

logger = logging.getLogger(__name__)

def update_document_with_chunks(document_id, chunks_count, title=None, page_count=None):
    """Update document with chunks count and metadata after processing."""
    if not is_db_ready():
        raise Exception("Database not ready")
    
    db_pool = get_db_pool()
    with db_pool.acquire() as connection:
        cursor = connection.cursor()
        
        # Build update query dynamically based on provided parameters
        update_fields = ["chunks_count = :chunks_count", "processing_status = 'chunked'", "processed_time = CURRENT_TIMESTAMP"]
        params = {'chunks_count': chunks_count, 'doc_id': document_id}
        
        if title:
            update_fields.append("title = :title")
            params['title'] = title
            
        if page_count is not None:
            update_fields.append("page_count = :page_count")
            params['page_count'] = page_count
        
        # Update document with metadata
        cursor.execute(f"""
            UPDATE documents 
            SET {', '.join(update_fields)}
            WHERE id = :doc_id
        """, params)
        
        connection.commit()
        logger.info(f"Updated document {document_id} with {chunks_count} chunks")

def store_document_chunks(document_id, chunks_with_embeddings):
    """Store document chunks with their embeddings."""
    if not is_db_ready():
        raise Exception("Database not ready")
    
    db_pool = get_db_pool()
    with db_pool.acquire() as connection:
        cursor = connection.cursor()
        
        # Clear existing chunks for this document
        cursor.execute("DELETE FROM document_chunks WHERE document_id = :doc_id", [document_id])
        
        # Insert new chunks
        for i, (chunk_text, embedding) in enumerate(chunks_with_embeddings):
            cursor.execute("""
                INSERT INTO document_chunks (document_id, chunk_index, chunk_text, embedding, chunk_size)
                VALUES (:doc_id, :chunk_idx, :chunk_text, :embedding, :chunk_size)
            """, {
                'doc_id': document_id,
                'chunk_idx': i,
                'chunk_text': chunk_text,
                'embedding': embedding,
                'chunk_size': len(chunk_text)
            })
        
        connection.commit()
        logger.info(f"Stored {len(chunks_with_embeddings)} chunks for document {document_id}")

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
        
        cursor.execute("""
            UPDATE document_chunks 
            SET embedding = :embedding 
            WHERE document_id = :doc_id AND chunk_index = :chunk_idx
        """, {
            'embedding': embedding,
            'doc_id': document_id,
            'chunk_idx': chunk_index
        })
        
        connection.commit()
        logger.info(f"Updated embedding for chunk {chunk_index} of document {document_id}")