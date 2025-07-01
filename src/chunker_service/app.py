import logging
import signal
import atexit
import threading
import time
from flask import Flask
from flask_cors import CORS

from config import HOST, PORT, DEBUG, CORS_ORIGINS
from database import init_database, cleanup_database
from services import dequeue_document_for_chunking, process_document_from_file
from api import health_bp

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

def chunking_worker():
    """Background worker to process document chunking queue."""
    global _worker_running
    logger.info("Starting chunking worker thread...")
    
    while _worker_running:
        try:
            # Try to dequeue a document (with 30 second timeout)
            document_data = dequeue_document_for_chunking(timeout=30)
            
            if document_data is None:
                # No message received within timeout, continue
                continue
            
            # Extract document information
            document_id = document_data['document_id']
            file_path = document_data['file_path']
            
            logger.info(f"Processing document {document_id} from {file_path}")
            
            # Process document and create chunks
            result = process_document_from_file(document_id, file_path)
            
            logger.info(f"Successfully processed document {document_id}: {result['message']}")
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            # Continue processing other documents even if one fails
            continue
    
    logger.info("Chunking worker thread stopped")

def start_chunking_worker():
    """Start the chunking worker in a background thread."""
    global _worker_thread
    if _worker_thread is None or not _worker_thread.is_alive():
        _worker_thread = threading.Thread(target=chunking_worker, daemon=True)
        _worker_thread.start()
        logger.info("Chunking worker thread started")

def cleanup_resources():
    """Clean up resources on shutdown."""
    global _worker_running, _worker_thread
    logger.info("Shutting down gracefully...")
    
    # Stop worker thread
    _worker_running = False
    if _worker_thread and _worker_thread.is_alive():
        logger.info("Waiting for chunking worker to stop...")
        _worker_thread.join(timeout=10)
    
    cleanup_database()
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
    start_chunking_worker()
    logger.info("Services initialization completed")

# Initialize services when module is imported (works with both direct run and gunicorn)
initialize_services()

if __name__ == '__main__':
    app.run(debug=DEBUG, host=HOST, port=PORT)