import os
import hashlib
import logging
import uuid
from datetime import datetime
from config import DOCUMENTS_STORAGE_PATH
from database import store_document
from .queue import enqueue_document_for_chunking

logger = logging.getLogger(__name__)

def get_file_hash(file_content):
    """Generate SHA256 hash of file content."""
    return hashlib.sha256(file_content).hexdigest()

def generate_unique_filename(original_filename):
    """Generate a unique filename to avoid conflicts."""
    # Get file extension
    name, ext = os.path.splitext(original_filename)
    
    # Generate unique identifier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    # Create unique filename
    unique_filename = f"{timestamp}_{unique_id}_{name}{ext}"
    return unique_filename

def process_document(file, include_embeddings=False):
    """Store document file and enqueue for chunking processing."""
    
    # Read file content for hashing
    file_content = file.read()
    file.seek(0)  # Reset file pointer
    
    # Generate file hash
    file_hash = get_file_hash(file_content)

    # Check if document already exists
    # TODO: Implement proper duplicate detection and handling
    
    # Ensure documents storage directory exists
    os.makedirs(DOCUMENTS_STORAGE_PATH, exist_ok=True)
    
    # Generate unique filename to avoid conflicts
    unique_filename = generate_unique_filename(file.filename)
    file_path = os.path.join(DOCUMENTS_STORAGE_PATH, unique_filename)
    
    try:
        # Save file to shared storage
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"Saved document {file.filename} to {file_path}")
        
        # Store document metadata in database (without processing)
        document_id = store_document(
            filename=file.filename,
            title=file.filename,  # Will be updated by chunker_service after processing
            page_count=0,  # Will be updated by chunker_service after processing
            file_hash=file_hash,
            file_path=unique_filename,  # Store relative path
            processing_status='pending'
        )
        
        # Enqueue document for chunking processing
        enqueue_document_for_chunking(document_id, unique_filename)
        
        logger.info(f"Enqueued document {file.filename} (ID: {document_id}) for chunking")
        
        # Format response
        response_data = {
            'document_id': document_id,
            'filename': file.filename,
            'file_hash': file_hash,
            'processing_status': 'pending',
            'message': 'Document uploaded and queued for processing'
        }
        
        # Note: Processing happens asynchronously
        if include_embeddings:
            response_data['note'] = 'Document chunking and embedding generation will happen asynchronously. Use the search endpoint once processing is complete.'
        
        logger.info(f"Successfully uploaded and queued document: {file.filename} (ID: {document_id})")
        return response_data
    
    except Exception as e:
        # Clean up file if database operation fails
        if os.path.exists(file_path):
            os.unlink(file_path)
        logger.error(f"Failed to process document {file.filename}: {e}")
        raise