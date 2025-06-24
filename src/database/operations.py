import logging
import oracledb
from database.connection import get_db_pool, is_db_ready

logger = logging.getLogger(__name__)

def store_document(filename, title, page_count, file_hash):
    """Store document metadata and return document ID."""
    if not is_db_ready():
        raise Exception("Database not ready")
    
    db_pool = get_db_pool()
    with db_pool.acquire() as connection:
        cursor = connection.cursor()
        
        # Check if document already exists
        cursor.execute("SELECT id FROM documents WHERE file_hash = :hash", [file_hash])
        result = cursor.fetchone()
        
        if result:
            return result[0]  # Return existing document ID
        
        # Insert new document
        cursor.execute("""
            INSERT INTO documents (filename, title, page_count, file_hash)
            VALUES (:filename, :title, :page_count, :file_hash)
            RETURNING id INTO :doc_id
        """, {
            'filename': filename,
            'title': title,
            'page_count': page_count,
            'file_hash': file_hash,
            'doc_id': cursor.var(oracledb.NUMBER)
        })
        
        doc_id = cursor.getvar('doc_id').getvalue()[0]
        connection.commit()
        return doc_id

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

def search_similar_chunks(query_embedding, limit=10, similarity_threshold=0.7):
    """Search for similar chunks using vector similarity."""
    if not is_db_ready():
        raise Exception("Database not ready")
    
    db_pool = get_db_pool()
    with db_pool.acquire() as connection:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT 
                dc.chunk_text,
                d.filename,
                d.title,
                dc.chunk_index,
                VECTOR_DISTANCE(dc.embedding, :query_embedding, COSINE) as distance
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE VECTOR_DISTANCE(dc.embedding, :query_embedding, COSINE) < :threshold
            ORDER BY distance
            FETCH FIRST :limit ROWS ONLY
        """, {
            'query_embedding': query_embedding,
            'threshold': 1 - similarity_threshold,  # Convert similarity to distance
            'limit': limit
        })
        
        results = cursor.fetchall()
        
        return [{
            'text': row[0],
            'filename': row[1],
            'title': row[2],
            'chunk_index': row[3],
            'similarity': 1 - row[4]  # Convert distance back to similarity
        } for row in results]