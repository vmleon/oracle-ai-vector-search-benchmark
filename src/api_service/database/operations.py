import logging
import oracledb
import array
from .connection import get_db_pool, is_db_ready

logger = logging.getLogger(__name__)

def store_document(filename, title, page_count, file_hash, file_path=None, processing_status='pending'):
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
        
        # Insert new document with file_path and processing_status
        cursor.execute("""
            INSERT INTO documents (filename, title, page_count, file_hash, file_path, processing_status)
            VALUES (:filename, :title, :page_count, :file_hash, :file_path, :processing_status)
            RETURNING id INTO :doc_id
        """, {
            'filename': filename,
            'title': title,
            'page_count': page_count,
            'file_hash': file_hash,
            'file_path': file_path,
            'processing_status': processing_status,
            'doc_id': cursor.var(oracledb.NUMBER)
        })
        
        doc_id = cursor.bindvars['doc_id'].getvalue()[0]
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

def search_similar_chunks(query_embedding, limit=10):
    """Search for similar chunks using vector similarity."""
    if not is_db_ready():
        raise Exception("Database not ready")
    
    db_pool = get_db_pool()
    with db_pool.acquire() as connection:
        cursor = connection.cursor()
        
        # Convert query embedding to proper format for Oracle VECTOR type
        if isinstance(query_embedding, list):
            query_embedding_array = array.array('f', query_embedding)
        else:
            query_embedding_array = query_embedding
            
        cursor.execute("""
            SELECT 
                dc.chunk_text,
                d.filename,
                d.title,
                dc.chunk_index,
                VECTOR_DISTANCE(dc.embedding, :query_embedding, COSINE) as distance
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            ORDER BY VECTOR_DISTANCE(dc.embedding, :query_embedding, COSINE)
            FETCH FIRST :limit ROWS ONLY
        """, {
            'query_embedding': query_embedding_array,
            'limit': limit
        })
        
        results = cursor.fetchall()
        logger.info("results")
        logger.info(results)
        
        return [{
            'text': row[0].read() if hasattr(row[0], 'read') else row[0],
            'filename': row[1],
            'title': row[2],
            'chunk_index': row[3],
            'similarity': 1 - row[4]  # Convert distance back to similarity
        } for row in results]

def get_document_counts_by_status():
    """Get document counts grouped by processing status."""
    if not is_db_ready():
        raise Exception("Database not ready")
    
    db_pool = get_db_pool()
    with db_pool.acquire() as connection:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT 
                processing_status,
                COUNT(*) as count
            FROM documents
            GROUP BY processing_status
        """)
        
        results = cursor.fetchall()
        
        # Convert to dictionary with status as key and count as value
        status_counts = {row[0]: row[1] for row in results}
        
        # Calculate total
        total = sum(status_counts.values())
        
        return {
            'total': total,
            'by_status': status_counts
        }

def get_chunks_by_embedding_status():
    """Get chunk counts by embedding status (with/without embeddings)."""
    if not is_db_ready():
        raise Exception("Database not ready")
    
    db_pool = get_db_pool()
    with db_pool.acquire() as connection:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_chunks,
                SUM(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) as chunks_with_embedding,
                SUM(CASE WHEN embedding IS NULL THEN 1 ELSE 0 END) as chunks_without_embedding
            FROM document_chunks
        """)
        
        result = cursor.fetchone()
        
        if result:
            total_chunks = result[0]
            with_embedding = result[1] 
            without_embedding = result[2]
            
            # Calculate embedding completion rate
            completion_rate = (with_embedding / total_chunks * 100) if total_chunks > 0 else 0
            
            return {
                'total': total_chunks,
                'with_embedding': with_embedding,
                'without_embedding': without_embedding,
                'embedding_completion_rate': round(completion_rate, 1)
            }
        else:
            return {
                'total': 0,
                'with_embedding': 0,
                'without_embedding': 0,
                'embedding_completion_rate': 0
            }