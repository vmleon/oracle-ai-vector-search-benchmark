from flask import Flask, request, jsonify
from flask_cors import CORS
from vllm import LLM
import os
import tempfile
from werkzeug.utils import secure_filename
from docling.document_converter import DocumentConverter
from dotenv import load_dotenv

load_dotenv()

# Configuration from environment variables with sensible defaults
HOST = os.getenv('VECTOR_HOST', '0.0.0.0')
PORT = int(os.getenv('VECTOR_PORT', '8000'))
MODEL_NAME = os.getenv('VECTOR_MODEL', 'intfloat/e5-mistral-7b-instruct')
CHUNK_SIZE = int(os.getenv('VECTOR_CHUNK_SIZE', '512'))
CHUNK_OVERLAP = int(os.getenv('VECTOR_CHUNK_OVERLAP', '50'))
DEBUG = os.getenv('VECTOR_DEBUG', 'True').lower() in ('true', '1', 'yes')
ENFORCE_EAGER = os.getenv('VECTOR_ENFORCE_EAGER', 'True').lower() in ('true', '1', 'yes')
MAX_FILE_SIZE = int(os.getenv('VECTOR_MAX_FILE_SIZE', '16777216'))  # 16MB default
TEMP_DIR = os.getenv('VECTOR_TEMP_DIR', tempfile.gettempdir())
CORS_ORIGINS = os.getenv('VECTOR_CORS_ORIGINS', '*').split(',')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Setup CORS
CORS(app, origins=CORS_ORIGINS)

# Model state tracking
model_ready = False

# Create an LLM.
# You should pass task="embed" for embedding models
try:
    model = LLM(
        model=MODEL_NAME,
        task="embed",
        enforce_eager=ENFORCE_EAGER,
    )
    model_ready = True
except Exception as e:
    print(f"Failed to initialize model: {e}")
    model = None
    model_ready = False

# Initialize docling converter
converter = DocumentConverter()

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

@app.route('/health/live', methods=['GET'])
def liveness_check():
    """Liveness probe - checks if the application is running"""
    return jsonify({
        'status': 'alive',
        'timestamp': os.times().system
    }), 200

@app.route('/health/ready', methods=['GET'])
def readiness_check():
    """Readiness probe - checks if the application is ready to serve requests"""
    if not model_ready or model is None:
        return jsonify({
            'status': 'not ready',
            'reason': 'model not initialized',
            'timestamp': os.times().system
        }), 503
    
    try:
        # Test model with a simple embedding request
        test_output = model.embed(["test"])
        if test_output and len(test_output) > 0:
            return jsonify({
                'status': 'ready',
                'model': MODEL_NAME,
                'timestamp': os.times().system
            }), 200
        else:
            return jsonify({
                'status': 'not ready',
                'reason': 'model test failed',
                'timestamp': os.times().system
            }), 503
    except Exception as e:
        return jsonify({
            'status': 'not ready',
            'reason': f'model error: {str(e)}',
            'timestamp': os.times().system
        }), 503

@app.route('/embeddings', methods=['POST'])
def create_embeddings():
    if not model_ready or model is None:
        return jsonify({'error': 'Model not ready'}), 503
    
    try:
        data = request.get_json()
        if not data or 'texts' not in data:
            return jsonify({'error': 'Missing texts array in request body'}), 400
        
        texts = data['texts']
        if not isinstance(texts, list):
            return jsonify({'error': 'texts must be an array'}), 400
        
        # Generate embeddings
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

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large. Maximum size is {MAX_FILE_SIZE} bytes'}), 413
        
        # Create temporary file in specified directory
        os.makedirs(TEMP_DIR, exist_ok=True)
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1], dir=TEMP_DIR) as tmp_file:
            file.save(tmp_file.name)
            temp_path = tmp_file.name
        
        try:
            # Convert document using docling
            result = converter.convert(temp_path)

            # Extract title
            document_title = result.document.name
            document_page_count = len(result.document.pages)
            
            # Extract text content
            text_content = result.document.export_to_markdown()
            
            # Chunk the text
            chunks = chunk_text(text_content)
            
            # Generate embeddings for chunks
            outputs = model.embed(chunks)
            
            # Format response
            embeddings = []
            for chunk, output in zip(chunks, outputs):
                embeddings.append({
                    'title': document_title,
                    'text': chunk,
                    'embedding': output.outputs.embedding,
                    'size': len(output.outputs.embedding)
                })
            
            return jsonify({
                'filename': file.filename,
                'chunks_count': len(chunks),
                'embeddings': embeddings
            })
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=DEBUG, host=HOST, port=PORT)
