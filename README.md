# Oracle AI Vector Search Benchmark

## Introduction

This project provides a comprehensive benchmarking suite for Oracle AI Vector Search capabilities. It combines a Flask-based vector embedding service with Oracle Database backend for storing and searching vector embeddings at scale.

### Technical overview

The benchmark uses a curated dataset of PDF documents from [Kaggle Dataset of PDF files](https://www.kaggle.com/datasets/manisha717/dataset-of-pdf-files?resource=download) to test document parsing, embedding generation, and vector search performance. The application leverages vLLM for efficient vector embeddings using the `intfloat/e5-mistral-7b-instruct` model, docling for robust document parsing across multiple file formats, and Oracle Database's native vector capabilities for similarity search.

Key features:

- **Vector Embedding Service**: Flask API for generating embeddings from text and uploaded documents
- **Oracle Database Integration**: Native vector storage and similarity search using Oracle's VECTOR data type
- **Document Processing**: Support for PDF, Word, PowerPoint, HTML, text, and Markdown files with automatic chunking
- **Vector Search**: Cosine similarity search with configurable thresholds and result limits
- **Connection Pooling**: Optimized database connections with configurable pool parameters
- **Scalable Architecture**: Designed for production use with comprehensive error handling and logging

## Getting Started

### Prerequisites

- Python 3.8+
- Podman or Docker
- SQLcl
- Oracle Database 23ai or later (with Vector support)
- Virtual environment support
- Git

### Quick Start

1. **Clone and setup the repository:**

```bash
git clone https://github.com/vmleon/oracle-ai-vector-search-benchmark.git
cd oracle-ai-vector-search-benchmark
```

2. **Prepare the environment:**

Before starting the Oracle Database, ensure your system is ready:

```bash
# Create and activate a Python virtual environment (recommended)
python -m venv venv
```

```bash
# On Linux/macOS:
source venv/bin/activate
```

```bash
# On Windows:
venv\Scripts\activate
```

```bash
# Install local script dependencies
pip install -r requirements.txt
```

```bash
# Start Podman machine (if not already running)
podman machine start
```

**Note:** The `requirements.txt` in the root directory contains dependencies for the local setup script (kagglehub, python-dotenv). The vector service has its own requirements file in `src/vector_maker/requirements.txt`.

3. **Setup the environment and dataset:**

```bash
python local.py setup
```

This will automatically:

- Download the PDF dataset from Kaggle using kagglehub (if not already present)
- Extract files to the `samples/` directory
- Set up the required directory structure

4. **Start Oracle Database:**

```bash
python local.py run
```

This will:

- Check that podman machine is running
- Start Oracle Database container (if not already running)
- Wait for database to be healthy
- Generate and set a random database password
- Create necessary database tables and indexes

5. **Set up the vector embedding service:**

```bash
cd src/vector_maker
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

6. **Start the embedding service:**

```bash
gunicorn -w 1 -b 0.0.0.0:8000 app:app
```

The service will be available at `http://localhost:8000`

7. **Cleanup (when done):**

```bash
python local.py cleanup
```

This will stop and remove the Oracle Database container and clean up sample files.

### API Usage

#### Health Check

```bash
# Check if service is alive
curl http://localhost:8000/health/live

# Check if service is ready (model and database)
curl http://localhost:8000/health/ready
```

#### Generate Text Embeddings

```bash
curl -X POST http://localhost:8000/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Sample text for embedding generation",
      "Another text to process"
    ]
  }'
```

#### Upload and Process Documents

```bash
# Upload document (stores in database)
curl -X POST http://localhost:8000/upload \
  -F "file=@samples/your-document.pdf"

# Upload with embeddings in response (optional)
curl -X POST http://localhost:8000/upload?include_embeddings=true \
  -F "file=@samples/your-document.pdf"
```

#### Search for Similar Content

```bash
# Search with default parameters
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms"
  }'

# Search with custom parameters
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "neural networks",
    "limit": 5,
    "similarity_threshold": 0.8
  }'
```

### Configuration

The application can be configured using environment variables:

#### Vector Service Configuration

- **Model**: `intfloat/e5-mistral-7b-instruct`
- **Chunk size**: 512 characters with 50 character overlap
- **Server**: Runs on `0.0.0.0:8000`
- **Max file size**: 16MB default

#### Oracle Database Configuration

- **Host**: `localhost` (default)
- **Port**: `1521` (default)
- **Service**: `FREEPDB1` (default)
- **User**: `SYSTEM` (default)
- **Password**: Generated automatically by `local.py run` (stored as `ORACLE_DB_PASSWORD` in `.env`)

#### Connection Pool Settings

- **Min connections**: 2 (default)
- **Max connections**: 10 (default)
- **Increment**: 1 (default)
- **Ping interval**: 60 seconds (default)

#### Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Vector service
VECTOR_HOST=0.0.0.0
VECTOR_PORT=8000
VECTOR_MODEL=intfloat/e5-mistral-7b-instruct
VECTOR_CHUNK_SIZE=512
VECTOR_CHUNK_OVERLAP=50

# Oracle Database
ORACLE_USER=SYSTEM
ORACLE_PASSWORD=your-password
ORACLE_HOST=localhost
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=FREEPDB1

# Connection Pool
ORACLE_POOL_MIN=2
ORACLE_POOL_MAX=10
ORACLE_POOL_INCREMENT=1
ORACLE_POOL_PING_INTERVAL=60
```

## API Reference

### Health Endpoints

**GET** `/health/live`

Check if the application is running.

**Response:**

```json
{
  "status": "alive",
  "timestamp": 1234567890.123
}
```

**GET** `/health/ready`

Check if the application is ready to serve requests (model and database).

**Response:**

```json
{
  "status": "ready",
  "timestamp": 1234567890.123,
  "model": "intfloat/e5-mistral-7b-instruct",
  "services": {
    "model": true,
    "database": true
  }
}
```

### Embeddings Endpoint

**POST** `/embeddings`

Generate embeddings for an array of text strings.

**Request Body:**

```json
{
  "texts": ["Your text here", "Another text"]
}
```

**Response:**

```json
{
  "embeddings": [
    {
      "text": "Your input text",
      "embedding": [0.1, 0.2, ...],
      "size": 4096
    }
  ]
}
```

### File Upload Endpoint

**POST** `/upload`

Upload a file, parse it with docling, chunk the content, generate embeddings, and store in Oracle Database.

**Request**: Multipart form with a `file` field

**Query Parameters:**

- `include_embeddings=true` (optional): Include embeddings in response

**Response:**

```json
{
  "document_id": 123,
  "filename": "document.pdf",
  "title": "Document Title",
  "page_count": 10,
  "chunks_count": 5,
  "file_hash": "sha256hash...",
  "message": "Document processed and stored successfully"
}
```

**Response with embeddings** (when `include_embeddings=true`):

```json
{
  "document_id": 123,
  "filename": "document.pdf",
  "title": "Document Title",
  "page_count": 10,
  "chunks_count": 5,
  "file_hash": "sha256hash...",
  "message": "Document processed and stored successfully",
  "embeddings": [
    {
      "chunk_index": 0,
      "text": "First chunk of text...",
      "embedding": [0.1, 0.2, ...],
      "size": 4096
    }
  ]
}
```

### Vector Search Endpoint

**POST** `/search`

Search for similar document chunks using vector similarity.

**Request Body:**

```json
{
  "query": "search text",
  "limit": 10,
  "similarity_threshold": 0.7
}
```

**Parameters:**

- `query` (required): Text to search for
- `limit` (optional): Maximum number of results (default: 10)
- `similarity_threshold` (optional): Minimum similarity score (default: 0.7)

**Response:**

```json
{
  "query": "search text",
  "results_count": 3,
  "results": [
    {
      "text": "Matching chunk text...",
      "filename": "document.pdf",
      "title": "Document Title",
      "chunk_index": 2,
      "similarity": 0.85
    }
  ]
}
```

### Supported File Types

The application uses docling for document parsing and supports:

- PDF files
- Word documents (.docx)
- PowerPoint presentations (.pptx)
- HTML files
- Text files
- Markdown files

## Database Schema

The application automatically creates the following Oracle Database tables:

### `documents` table

```sql
CREATE TABLE documents (
    id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    filename VARCHAR2(255) NOT NULL,
    title VARCHAR2(500),
    page_count NUMBER,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_hash VARCHAR2(64) UNIQUE
);
```

### `document_chunks` table

```sql
CREATE TABLE document_chunks (
    id NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    document_id NUMBER REFERENCES documents(id),
    chunk_index NUMBER NOT NULL,
    chunk_text CLOB NOT NULL,
    embedding VECTOR(4096, FLOAT32),
    chunk_size NUMBER,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Vector Index

```sql
CREATE INDEX idx_chunks_embedding ON document_chunks (embedding) INDEXTYPE IS VECTOR;
```

## Features

### ✅ Implemented

- **Oracle Database Integration**: Native vector storage and similarity search
- **Connection Pooling**: Optimized database connections with configurable parameters
- **Document Processing**: Automatic chunking and embedding generation
- **Vector Search**: Cosine similarity search with configurable thresholds
- **File Deduplication**: SHA256-based duplicate detection
- **Health Monitoring**: Comprehensive health checks for model and database
- **Error Handling**: Robust error handling and logging throughout

### 🚧 Planned Features

- Test document parsing across all supported formats
- Include Liquibase for database schema management
- Include Locust benchmarking for performance testing
- Include Prometheus and Grafana for monitoring and visualization
- Add authentication and authorization
- Implement document metadata search
- Add batch processing capabilities
