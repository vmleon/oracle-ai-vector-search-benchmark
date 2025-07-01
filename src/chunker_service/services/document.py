import os
import logging
from config import CHUNK_SIZE, CHUNK_OVERLAP, DOCUMENTS_STORAGE_PATH
from database import store_document_chunks_without_embeddings, update_document_with_chunks
from .queue import enqueue_chunk_for_embedding

logger = logging.getLogger(__name__)

# Lazy initialization of docling converter to reduce startup memory
converter = None

def get_converter():
    """Get or initialize the document converter with lightweight configuration."""
    global converter
    if converter is None:
        from docling.document_converter import DocumentConverter
        
        try:
            # Try lightweight configuration first
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.datamodel.base_models import InputFormat
            from docling.document_converter import PdfFormatOption
            
            # Configure lightweight pipeline options
            pipeline_options = PdfPipelineOptions(
                do_ocr=False,  # Disable OCR to reduce memory usage
                do_table_structure=False,  # Disable table structure recognition
                images_scale=1.0,
                generate_page_images=False,
                generate_picture_images=False
            )
            
            # Initialize converter with lightweight configuration
            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
            logger.info("Docling converter initialized with lightweight configuration")
            
        except Exception as e:
            # Fallback to default configuration if lightweight config fails
            logger.warning(f"Failed to initialize lightweight config: {e}")
            logger.info("Falling back to default Docling configuration")
            converter = DocumentConverter()
            logger.info("Docling converter initialized with default configuration")
    
    return converter

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

def process_document_from_file(document_id, file_path):
    """Process document from file path and create chunks."""
    
    # Ensure documents storage directory exists
    os.makedirs(DOCUMENTS_STORAGE_PATH, exist_ok=True)
    
    # Get full path to the document
    full_file_path = os.path.join(DOCUMENTS_STORAGE_PATH, file_path)
    
    if not os.path.exists(full_file_path):
        raise FileNotFoundError(f"Document file not found: {full_file_path}")
    
    try:
        # Convert document using docling
        converter = get_converter()
        result = converter.convert(full_file_path)

        # Extract text content
        text_content = result.document.export_to_markdown()
        
        # Chunk the text
        chunks = chunk_text(text_content)
        
        logger.info(f"Document {document_id} chunked into {len(chunks)} chunks")
        
        # Store chunks without embeddings in database
        store_document_chunks_without_embeddings(document_id, chunks)
        
        # Update document metadata with extracted information
        update_document_with_chunks(
            document_id, 
            len(chunks), 
            title=text_content[:100] + "..." if len(text_content) > 100 else text_content,  # Simple title extraction
            page_count=len(result.document.pages)
        )
        
        # Enqueue chunks for embedding processing
        for i, chunk in enumerate(chunks):
            enqueue_chunk_for_embedding(document_id, i, chunk)
        
        logger.info(f"Successfully processed document {document_id}, queued {len(chunks)} chunks for embedding")
        
        return {
            'document_id': document_id,
            'chunks_count': len(chunks),
            'message': f'Document processed and {len(chunks)} chunks queued for embedding'
        }
    
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        raise