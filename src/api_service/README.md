# API Service

The API Service handles document upload and search functionality. It stores documents and enqueues them for processing by the Chunker Service.

## Features

- Document upload and storage (PDF, DOCX, TXT, etc.)
- Document search using vector similarity
- Queuing documents for chunking by Chunker Service
- Health checks

## Dependencies

- Flask for web framework
- Oracle Database for storage
- Oracle Advanced Queues for async processing

## Configuration

Set environment variables:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=True
API_MAX_FILE_SIZE=16777216  # 16MB
API_CORS_ORIGINS=*

# Oracle Database
ORACLE_USER=SYSTEM
ORACLE_PASSWORD=password
ORACLE_HOST=localhost
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=FREEPDB1
ORACLE_POOL_MIN=2
ORACLE_POOL_MAX=10
```

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set environment variables (create `.env` file)

3. Ensure Oracle Database is running with the `vector_pending_chunk` and `vector_pending_document` queue created

## Running

### Development

```bash
python app.py
```

### Production with Gunicorn

```bash
# Using configuration file (recommended)
gunicorn app:app -c gunicorn.conf.py

# Or with manual settings
gunicorn app:app -b 0.0.0.0:8000 -w 2 --timeout 300 --max-requests 100
```

## API Endpoints

### POST /upload

Upload and process a document.

**Request:**

- `file`: Document file (multipart/form-data)
- `include_embeddings` (optional): Boolean query parameter

**Response:**

```json
{
  "document_id": 123,
  "filename": "document.pdf",
  "title": "Document Title",
  "page_count": 10,
  "chunks_count": 25,
  "file_hash": "sha256_hash",
  "message": "Document processed and queued for embedding generation"
}
```

### POST /search

Search for similar document chunks.

**Request:**

```json
{
  "query": "search text",
  "limit": 10
}
```

**Response:**

```json
{
  "results": [
    {
      "text": "chunk text",
      "filename": "document.pdf",
      "title": "Document Title",
      "chunk_index": 0,
      "similarity": 0.85
    }
  ]
}
```

### GET /health

Health check endpoint.

## Architecture

The API Service is designed to be stateless and scalable:

1. **Document Upload**: Stores documents and enqueues them for processing by Chunker Service
2. **Queue Integration**: Enqueues documents for chunking and chunks for embedding generation
3. **Search**: Searches through embedded chunks (requires chunker_service and vector_maker_service to have processed them)
4. **Database**: Stores document metadata

## Notes

- Documents are queued for processing by the Chunker Service, which handles chunking
- Embeddings are generated asynchronously by the Vector Maker Service
- Search will only return results for documents that have been processed by both the chunker_service and vector_maker_service
- The service is designed to work in conjunction with the chunker_service and vector_maker_service
