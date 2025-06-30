import logging
from vllm import LLM
from config import MODEL_NAME, ENFORCE_EAGER

logger = logging.getLogger(__name__)

# Global state
_model = None
_model_ready = False

def init_model():
    """Initialize the vLLM embedding model."""
    global _model, _model_ready
    
    try:
        logger.info(f"Initializing vLLM model: {MODEL_NAME}")
        _model = LLM(
            model=MODEL_NAME,
            task="embed",
            enforce_eager=ENFORCE_EAGER,
        )
        _model_ready = True
        logger.info("vLLM model initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize model: {e}")
        _model = None
        _model_ready = False

def get_model():
    """Get the embedding model instance."""
    return _model

def is_model_ready():
    """Check if model is ready."""
    return _model_ready and _model is not None

def cleanup_model():
    """Clean up model resources."""
    global _model_ready
    
    if _model_ready:
        logger.info("Shutting down vLLM model...")
        _model_ready = False
        logger.info("vLLM model shutdown logged")