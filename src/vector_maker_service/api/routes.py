import logging
from flask import Blueprint, request, jsonify
from models import get_model, is_model_ready

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