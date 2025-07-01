import logging
import signal
import atexit
from flask import Flask
from flask_cors import CORS

from config import HOST, PORT, DEBUG, MAX_FILE_SIZE, CORS_ORIGINS
from database import init_database, cleanup_database
from api import health_bp, api_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Setup CORS
CORS(app, origins=CORS_ORIGINS)

# Register blueprints
app.register_blueprint(health_bp)
app.register_blueprint(api_bp)

def cleanup_resources():
    """Clean up resources on shutdown."""
    logger.info("Shutting down gracefully...")
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
    logger.info("Services initialization completed")

# Initialize services when module is imported (works with both direct run and gunicorn)
initialize_services()

if __name__ == '__main__':
    app.run(debug=DEBUG, host=HOST, port=PORT)