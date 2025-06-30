import logging
from flask import Blueprint, request, jsonify
from models import get_model, is_model_ready
from database import is_db_ready
from services import process_document, search_documents
from config import MAX_FILE_SIZE

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

@api_bp.route('/embeddings', methods=['POST'])
def create_embeddings():
    if not is_model_ready():
        return jsonify({'error': 'Model not ready'}), 503
    
    try:
        data = request.get_json()
        if not data or 'texts' not in data:
            return jsonify({'error': 'Missing texts array in request body'}), 400
        
        texts = data['texts']
        if not isinstance(texts, list):
            return jsonify({'error': 'texts must be an array'}), 400
        
        # Generate embeddings
        model = get_model()
        outputs = model.embed(texts)
        
        # Format response
        embeddings = []
        for text, output in zip(texts, outputs):
            embeddings.append({
                'text': text,
                'embedding': output.outputs.embedding,
                'size': len(output.outputs.embedding)
            })
        
        return jsonify({'embeddings': embeddings})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/upload', methods=['POST'])
def upload_file():
    try:
        if not is_model_ready():
            return jsonify({'error': 'Model not ready'}), 503
            
        if not is_db_ready():
            return jsonify({'error': 'Database not ready'}), 503
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read file content for size validation
        file_content = file.read()
        file.seek(0)  # Reset file pointer
        
        # Validate file size
        file_size = len(file_content)
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large. Maximum size is {MAX_FILE_SIZE} bytes'}), 413
        
        # Process document
        include_embeddings = request.args.get('include_embeddings', 'false').lower() == 'true'
        response_data = process_document(file, include_embeddings)
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/search', methods=['POST'])
def search_documents_endpoint():
    """Search for similar document chunks using vector similarity."""
    try:
        if not is_model_ready():
            return jsonify({'error': 'Model not ready'}), 503
            
        if not is_db_ready():
            return jsonify({'error': 'Database not ready'}), 503
        
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Missing query in request body'}), 400
        
        query_text = data['query']
        limit = data.get('limit', 10)
        similarity_threshold = data.get('similarity_threshold', 0.7)
        
        # Search for similar documents
        results = search_documents(
            query_text=query_text,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
        
        return jsonify(results)
    
    except Exception as e:
        logger.error(f"Error processing search: {str(e)}")
        return jsonify({'error': str(e)}), 500