import logging
import signal
import atexit
import threading
import time
from flask import Flask
from flask_cors import CORS

from config import HOST, PORT, DEBUG, CORS_ORIGINS
from database import init_database, cleanup_database, update_chunk_embedding
from models import init_model, cleanup_model, get_model, is_model_ready
from services import dequeue_chunk_for_embedding
from api import health_bp, api_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Worker state
_worker_running = True
_worker_thread = None

# Create Flask app
app = Flask(__name__)

# Setup CORS
CORS(app, origins=CORS_ORIGINS)

# Register blueprints
app.register_blueprint(health_bp)
app.register_blueprint(api_bp)

def embedding_worker():
    """Background worker to process embedding queue."""
    global _worker_running
    logger.info("Starting embedding worker thread...")
    
    # Wait for model to be ready
    while _worker_running and not is_model_ready():
        logger.info("Embedding worker waiting for model to be ready...")
        time.sleep(5)
    
    if not _worker_running:
        return
    
    model = get_model()
    logger.info("Embedding worker ready, starting to process queue...")
    
    while _worker_running:
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
    
    logger.info("Embedding worker thread stopped")

def start_embedding_worker():
    """Start the embedding worker in a background thread."""
    global _worker_thread
    if _worker_thread is None or not _worker_thread.is_alive():
        _worker_thread = threading.Thread(target=embedding_worker, daemon=True)
        _worker_thread.start()
        logger.info("Embedding worker thread started")

def cleanup_resources():
    """Clean up resources on shutdown."""
    global _worker_running, _worker_thread
    logger.info("Shutting down gracefully...")
    
    # Stop worker thread
    _worker_running = False
    if _worker_thread and _worker_thread.is_alive():
        logger.info("Waiting for embedding worker to stop...")
        _worker_thread.join(timeout=10)
    
    cleanup_database()
    cleanup_model()
    logger.info("Graceful shutdown completed")

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    cleanup_resources()
    exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

# Register exit handler for normal program termination
atexit.register(cleanup_resources)

# Initialize services
def initialize_services():
    """Initialize all services."""
    logger.info("Initializing services...")
    init_database()
    init_model()
    start_embedding_worker()
    logger.info("Services initialization completed")

# Initialize services when module is imported (works with both direct run and gunicorn)
initialize_services()

if __name__ == '__main__':
    app.run(debug=DEBUG, host=HOST, port=PORT)