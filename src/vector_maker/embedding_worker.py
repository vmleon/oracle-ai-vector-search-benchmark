import time
import logging
import signal
import sys
from models import init_model, get_model, is_model_ready, cleanup_model
from database import init_database, update_chunk_embedding, cleanup_database
from services import dequeue_chunk_for_embedding

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Worker state
_running = True

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global _running
    logger.info(f"Received signal {signum}, shutting down worker...")
    _running = False

def process_embedding_queue():
    """Main worker loop to process embedding queue."""
    logger.info("Starting embedding worker...")
    
    # Initialize services
    init_database()
    init_model()
    
    # Wait for model to be ready
    while not is_model_ready():
        logger.info("Waiting for model to be ready...")
        time.sleep(5)
    
    model = get_model()
    logger.info("Embedding worker ready, starting to process queue...")
    
    while _running:
        try:
            # Try to dequeue a chunk (with 30 second timeout)
            chunk_data = dequeue_chunk_for_embedding(timeout=30)
            
            if chunk_data is None:
                # No message received within timeout, continue
                continue
            
            # Extract chunk information
            document_id = chunk_data['document_id']
            chunk_index = chunk_data['chunk_index']
            chunk_text = chunk_data['chunk_text']
            
            logger.info(f"Processing chunk {chunk_index} for document {document_id}")
            
            # Generate embedding
            output = model.embed([chunk_text])[0]
            embedding = output.outputs.embedding
            
            # Update database with embedding
            update_chunk_embedding(document_id, chunk_index, embedding)
            
            logger.info(f"Successfully processed chunk {chunk_index} for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error processing chunk: {e}")
            # Continue processing other chunks even if one fails
            continue
    
    logger.info("Embedding worker stopped")

def main():
    """Main function."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    try:
        process_embedding_queue()
    except Exception as e:
        logger.error(f"Fatal error in embedding worker: {e}")
        sys.exit(1)
    finally:
        # Cleanup resources
        cleanup_model()
        cleanup_database()

if __name__ == '__main__':
    main()