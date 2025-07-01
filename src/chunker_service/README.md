# Chunker Service

Document chunking microservice that processes documents from the VECTOR_PENDING_DOCUMENT queue and creates text chunks for embedding generation.

## Features

- Document chunking using Docling for various formats (PDF, DOCX, etc.)
- Oracle Advanced Queue integration for async processing
- Lightweight Docling configuration to reduce memory usage
- Background worker for continuous queue processing
- Health and readiness endpoints
- Production-ready with gunicorn

## Architecture

The chunker service:
1. Dequeues documents from `VECTOR_PENDING_DOCUMENT` queue
2. Processes documents from shared file storage
3. Chunks document text using configurable parameters
4. Stores chunks in database without embeddings
5. Enqueues chunks to `VECTOR_PENDING_CHUNK` queue for embedding

## Configuration

Environment variables (`.env`):

```env
# Database Configuration
DB_USER=your_username
DB_PASSWORD=your_password
DB_DSN=your_oracle_dsn

# Service Configuration
HOST=0.0.0.0
PORT=8002
DEBUG=false
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Document Processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
DOCUMENTS_STORAGE_PATH=/shared/documents
```

## Running the Service

### Development Mode

```bash
cd src/chunker_service
python app.py
```

### Production Mode with Gunicorn

```bash
cd src/chunker_service
gunicorn --config gunicorn.conf.py app:app
```

## API Endpoints

### Health Check
- `GET /health` - Service health status
- `GET /ready` - Service readiness check

## Queue Processing

The service processes documents from the `VECTOR_PENDING_DOCUMENT` queue with the following payload structure:

```json
{
  "document_id": 123,
  "file_path": "relative/path/to/document.pdf"
}
```

Chunks are forwarded to `VECTOR_PENDING_CHUNK` queue with:

```json
{
  "document_id": 123,
  "chunk_index": 0,
  "chunk_text": "Document chunk content..."
}
```

## Document Processing

The service uses Docling for document processing with optimized configuration:
- OCR disabled to reduce memory usage
- Table structure recognition disabled
- Image processing minimized
- Fallback to default configuration if needed

## Dependencies

- Flask 3.0.3 - Web framework
- Flask-CORS 4.0.1 - CORS support
- oracledb 2.2.1 - Oracle database connectivity
- gunicorn 22.0.0 - WSGI server
- docling 2.5.2 - Document processing

## Development

Install dependencies:
```bash
pip install -r requirements.txt
```

The service automatically initializes database connections and starts the background worker thread on startup.