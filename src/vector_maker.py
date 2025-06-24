from flask import Flask, request, jsonify
from flask_cors import CORS
from vllm import LLM
import os
import tempfile
import hashlib
import logging
from werkzeug.utils import secure_filename
from docling.document_converter import DocumentConverter
from dotenv import load_dotenv
import oracledb

load_dotenv()

# Ensure Oracle client operates in thin mode (doesn't require Oracle client libraries)
# By default, python-oracledb uses thin mode unless init_oracle_client() is called

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

# Oracle Database Configuration
ORACLE_USER = os.getenv('ORACLE_USER', 'SYSTEM')
ORACLE_PASSWORD = os.getenv('ORACLE_PASSWORD', os.getenv('ORACLE_DB_PASSWORD', 'password'))
ORACLE_HOST = os.getenv('ORACLE_HOST', 'localhost')
ORACLE_PORT = int(os.getenv('ORACLE_PORT', '1521'))
ORACLE_SERVICE_NAME = os.getenv('ORACLE_SERVICE_NAME', 'FREEPDB1')
ORACLE_DSN = os.getenv('ORACLE_DSN') or f'{ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_SERVICE_NAME}'

# Connection Pool Configuration
ORACLE_POOL_MIN = int(os.getenv('ORACLE_POOL_MIN', '2'))
ORACLE_POOL_MAX = int(os.getenv('ORACLE_POOL_MAX', '10'))
ORACLE_POOL_INCREMENT = int(os.getenv('ORACLE_POOL_INCREMENT', '1'))
ORACLE_POOL_PING_INTERVAL = int(os.getenv('ORACLE_POOL_PING_INTERVAL', '60'))

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Setup CORS
CORS(app, origins=CORS_ORIGINS)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for Oracle client environment variables that might interfere with thin mode
if 'ORACLE_HOME' in os.environ:
    logger.warning("ORACLE_HOME detected, this might cause issues with thin mode")
if 'TNS_ADMIN' in os.environ:
    logger.warning("TNS_ADMIN detected, this might cause issues with thin mode")

# Model and database state tracking
model_ready = False
db_pool = None
db_ready = False

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

# Initialize Oracle Database Connection Pool
def init_database():
    """Initialize Oracle database connection pool and create tables."""
    global db_pool, db_ready
    
    try:
        logger.info("Initializing Oracle database connection pool...")
        logger.info(f"Connecting to: {ORACLE_DSN} as user: {ORACLE_USER}")
        
        # First test with a simple connection to ensure we're using thin mode correctly
        logger.info("Testing connection...")
        test_conn = oracledb.connect(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN
        )
        test_conn.close()
        logger.info("Test connection successful")
        
        # Create connection pool using thin mode (no Oracle client installation required)
        db_pool = oracledb.create_pool(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN,
            min=ORACLE_POOL_MIN,
            max=ORACLE_POOL_MAX,
            increment=ORACLE_POOL_INCREMENT,
            ping_interval=ORACLE_POOL_PING_INTERVAL
        )
        
        # Test connection and create tables
        with db_pool.acquire() as connection:
            # TODO make a simple select from dual to check connection pool and mark db_ready as True
            None
        
        db_ready = True
        logger.info("Database connection pool initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        db_pool = None
        db_ready = False

def get_file_hash(file_content):
    """Generate SHA256 hash of file content."""
    return hashlib.sha256(file_content).hexdigest()

def store_document(filename, title, page_count, file_hash):
    """Store document metadata and return document ID."""
    if not db_ready or not db_pool:
        raise Exception("Database not ready")
    
    with db_pool.acquire() as connection:
        cursor = connection.cursor()
        
        # Check if document already exists
        cursor.execute("SELECT id FROM documents WHERE file_hash = :hash", [file_hash])
        result = cursor.fetchone()
        
        if result:
            return result[0]  # Return existing document ID
        
        # Insert new document
        cursor.execute("""
            INSERT INTO documents (filename, title, page_count, file_hash)
            VALUES (:filename, :title, :page_count, :file_hash)
            RETURNING id INTO :doc_id
        """, {
            'filename': filename,
            'title': title,
            'page_count': page_count,
            'file_hash': file_hash,
            'doc_id': cursor.var(oracledb.NUMBER)
        })
        
        doc_id = cursor.getvar('doc_id').getvalue()[0]
        connection.commit()
        return doc_id

def store_document_chunks(document_id, chunks_with_embeddings):
    """Store document chunks with their embeddings."""
    if not db_ready or not db_pool:
        raise Exception("Database not ready")
    
    with db_pool.acquire() as connection:
        cursor = connection.cursor()
        
        # Clear existing chunks for this document
        cursor.execute("DELETE FROM document_chunks WHERE document_id = :doc_id", [document_id])
        
        # Insert new chunks
        for i, (chunk_text, embedding) in enumerate(chunks_with_embeddings):
            cursor.execute("""
                INSERT INTO document_chunks (document_id, chunk_index, chunk_text, embedding, chunk_size)
                VALUES (:doc_id, :chunk_idx, :chunk_text, :embedding, :chunk_size)
            """, {
                'doc_id': document_id,
                'chunk_idx': i,
                'chunk_text': chunk_text,
                'embedding': embedding,
                'chunk_size': len(chunk_text)
            })
        
        connection.commit()
        logger.info(f"Stored {len(chunks_with_embeddings)} chunks for document {document_id}")

def search_similar_chunks(query_embedding, limit=10, similarity_threshold=0.7):
    """Search for similar chunks using vector similarity."""
    if not db_ready or not db_pool:
        raise Exception("Database not ready")
    
    with db_pool.acquire() as connection:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT 
                dc.chunk_text,
                d.filename,
                d.title,
                dc.chunk_index,
                VECTOR_DISTANCE(dc.embedding, :query_embedding, COSINE) as distance
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE VECTOR_DISTANCE(dc.embedding, :query_embedding, COSINE) < :threshold
            ORDER BY distance
            FETCH FIRST :limit ROWS ONLY
        """, {
            'query_embedding': query_embedding,
            'threshold': 1 - similarity_threshold,  # Convert similarity to distance
            'limit': limit
        })
        
        results = cursor.fetchall()
        
        return [{
            'text': row[0],
            'filename': row[1],
            'title': row[2],
            'chunk_index': row[3],
            'similarity': 1 - row[4]  # Convert distance back to similarity
        } for row in results]

# Initialize database on startup
init_database()

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
    health_status = {
        'status': 'ready',
        'timestamp': os.times().system,
        'model': MODEL_NAME,
        'services': {
            'model': False,
            'database': False
        }
    }
    
    # Check model status
    if not model_ready or model is None:
        health_status['status'] = 'not ready'
        health_status['reason'] = 'model not initialized'
        return jsonify(health_status), 503
    
    try:
        # Test model with a simple embedding request
        test_output = model.embed(["test"])
        if test_output and len(test_output) > 0:
            health_status['services']['model'] = True
        else:
            health_status['status'] = 'not ready'
            health_status['reason'] = 'model test failed'
            return jsonify(health_status), 503
    except Exception as e:
        health_status['status'] = 'not ready'
        health_status['reason'] = f'model error: {str(e)}'
        return jsonify(health_status), 503
    
    # Check database status
    if not db_ready or not db_pool:
        health_status['status'] = 'not ready'
        health_status['reason'] = 'database not ready'
        return jsonify(health_status), 503
    
    try:
        # Test database connection
        with db_pool.acquire() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            cursor.fetchone()
            health_status['services']['database'] = True
    except Exception as e:
        health_status['status'] = 'not ready'
        health_status['reason'] = f'database error: {str(e)}'
        return jsonify(health_status), 503
    
    return jsonify(health_status), 200

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
        if not model_ready or model is None:
            return jsonify({'error': 'Model not ready'}), 503
            
        if not db_ready or not db_pool:
            return jsonify({'error': 'Database not ready'}), 503
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read file content for hashing
        file_content = file.read()
        file.seek(0)  # Reset file pointer
        
        # Validate file size
        file_size = len(file_content)
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large. Maximum size is {MAX_FILE_SIZE} bytes'}), 413
        
        # Generate file hash
        file_hash = get_file_hash(file_content)
        
        # Create temporary file in specified directory
        os.makedirs(TEMP_DIR, exist_ok=True)
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1], dir=TEMP_DIR) as tmp_file:
            tmp_file.write(file_content)
            temp_path = tmp_file.name
        
        try:
            # Convert document using docling
            result = converter.convert(temp_path)

            # Extract document metadata
            document_title = result.document.name or file.filename
            document_page_count = len(result.document.pages)
            
            # Extract text content
            text_content = result.document.export_to_markdown()
            
            # Chunk the text
            chunks = chunk_text(text_content)
            
            # Generate embeddings for chunks
            outputs = model.embed(chunks)
            
            # Store document in database
            document_id = store_document(
                filename=file.filename,
                title=document_title,
                page_count=document_page_count,
                file_hash=file_hash
            )
            
            # Prepare chunks with embeddings for database storage
            chunks_with_embeddings = [
                (chunk, output.outputs.embedding) 
                for chunk, output in zip(chunks, outputs)
            ]
            
            # Store chunks and embeddings in database
            store_document_chunks(document_id, chunks_with_embeddings)
            
            # Format response (exclude embeddings for performance)
            response_data = {
                'document_id': document_id,
                'filename': file.filename,
                'title': document_title,
                'page_count': document_page_count,
                'chunks_count': len(chunks),
                'file_hash': file_hash,
                'message': 'Document processed and stored successfully'
            }
            
            # Optionally include embeddings in response if requested
            include_embeddings = request.args.get('include_embeddings', 'false').lower() == 'true'
            if include_embeddings:
                response_data['embeddings'] = [
                    {
                        'chunk_index': i,
                        'text': chunk,
                        'embedding': output.outputs.embedding,
                        'size': len(output.outputs.embedding)
                    }
                    for i, (chunk, output) in enumerate(zip(chunks, outputs))
                ]
            
            logger.info(f"Successfully processed and stored document: {file.filename} (ID: {document_id})")
            return jsonify(response_data)
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['POST'])
def search_documents():
    """Search for similar document chunks using vector similarity."""
    try:
        if not model_ready or model is None:
            return jsonify({'error': 'Model not ready'}), 503
            
        if not db_ready or not db_pool:
            return jsonify({'error': 'Database not ready'}), 503
        
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Missing query in request body'}), 400
        
        query_text = data['query']
        limit = data.get('limit', 10)
        similarity_threshold = data.get('similarity_threshold', 0.7)
        
        # Generate embedding for the query
        query_output = model.embed([query_text])
        query_embedding = query_output[0].outputs.embedding
        
        # Search for similar chunks
        results = search_similar_chunks(
            query_embedding=query_embedding,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
        
        return jsonify({
            'query': query_text,
            'results_count': len(results),
            'results': results
        })
    
    except Exception as e:
        logger.error(f"Error processing search: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=DEBUG, host=HOST, port=PORT)