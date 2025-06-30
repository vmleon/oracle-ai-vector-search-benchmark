import os
import tempfile
import hashlib
import logging
from docling.document_converter import DocumentConverter
from config import CHUNK_SIZE, CHUNK_OVERLAP, TEMP_DIR
from models import get_model, is_model_ready
from database import store_document, store_document_chunks, store_document_chunks_without_embeddings
from .queue import enqueue_chunk_for_embedding

logger = logging.getLogger(__name__)

# Initialize docling converter
converter = DocumentConverter()

def get_file_hash(file_content):
    """Generate SHA256 hash of file content."""
    return hashlib.sha256(file_content).hexdigest()

def chunk_text(text, chunk_size=None, overlap=None):
    """Split text into overlapping chunks."""
    if chunk_size is None:
        chunk_size = CHUNK_SIZE
    if overlap is None:
        overlap = CHUNK_OVERLAP
    
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # Find the last space before the chunk size limit
        while end > start and text[end] != ' ':
            end -= 1
        
        if end == start:  # No space found, force break
            end = start + chunk_size
        
        chunks.append(text[start:end])
        start = end - overlap
    
    return chunks

def process_document(file, include_embeddings=False):
    """Process document file and return response data."""
    if not is_model_ready():
        raise Exception("Model not ready")
    
    # Read file content for hashing
    file_content = file.read()
    file.seek(0)  # Reset file pointer
    
    # Generate file hash
    file_hash = get_file_hash(file_content)

    # TODO check if the file_hash is already in the database, if so, log the event and skip chunking and embedding creation. Return the information as processed
    
    # Create temporary file in specified directory
    os.makedirs(TEMP_DIR, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1], dir=TEMP_DIR) as tmp_file:
        tmp_file.write(file_content)
        temp_path = tmp_file.name
    
    try:
        # Convert document using docling
        result = converter.convert(temp_path)

        # Extract document metadata
        document_title = result.document.name or file.filename
        document_page_count = len(result.document.pages)
        
        # Extract text content
        text_content = result.document.export_to_markdown()
        
        # Chunk the text
        chunks = chunk_text(text_content)
        
        # Store document in database
        document_id = store_document(
            filename=file.filename,
            title=document_title,
            page_count=document_page_count,
            file_hash=file_hash
        )

        logger.info(f"Document {file.filename} chunked in {len(chunks)} chunks.")
        
        # Store chunks without embeddings in database
        store_document_chunks_without_embeddings(document_id, chunks)
        
        # Enqueue chunks for embedding processing
        for i, chunk in enumerate(chunks):
            enqueue_chunk_for_embedding(document_id, i, chunk)
        
        # Format response
        response_data = {
            'document_id': document_id,
            'filename': file.filename,
            'title': document_title,
            'page_count': document_page_count,
            'chunks_count': len(chunks),
            'file_hash': file_hash,
            'message': 'Document processed and queued for embedding generation'
        }
        
        # Note: Embeddings are now generated asynchronously via queue
        if include_embeddings:
            response_data['note'] = 'Embeddings will be generated asynchronously. Use the search endpoint once processing is complete.'
        
        logger.info(f"Successfully processed and stored document: {file.filename} (ID: {document_id})")
        return response_data
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)