# Oracle AI Vector Search Benchmark

A microservices architecture for document processing, embedding generation, and vector similarity search using Oracle Database with AI Vector Search capabilities.

## Architecture

![Architecture Diagram](./docs/architecture.drawio.png)

The system is split into three independent services:

### 1. API Service (`src/api_service/`)

- **Purpose**: Document upload and search
- **Port**: 8000 (default)
- **Endpoints**: `/upload`, `/search`, `/health`
- **Dependencies**: Flask, Oracle DB

### 2. Chunker Service (`src/chunker_service/`)

- **Purpose**: Document processing and text chunking
- **Port**: 8002 (default)
- **Endpoints**: `/health`, `/ready`
- **Dependencies**: Flask, Docling, Oracle DB
- **Features**: Background worker for queue processing, lightweight Docling configuration

### 3. Vector Maker Service (`src/vector_maker_service/`)

- **Purpose**: Embedding generation and queue processing
- **Port**: 8001 (default)
- **Endpoints**: `/embeddings`, `/health`
- **Dependencies**: Flask, vLLM, Oracle DB
- **Features**: Background worker for async processing

## System Flow

1. **Document Upload** → API Service stores documents and queues them for processing
2. **Document Processing** → Chunker Service processes documents from queue and creates text chunks
3. **Chunk Queuing** → Chunker Service queues chunks for embedding generation
4. **Embedding Generation** → Vector Maker Service generates embeddings for queued chunks
5. **Search** → API Service searches using generated embeddings

## API Endpoints

- **API Service**: `/upload` (POST), `/search` (POST), `/health` (GET)
- **Vector Maker Service**: `/embeddings` (POST), `/health` (GET)
- **Chunker Service**: `/health` (GET), `/ready` (GET)

_For detailed API documentation with request/response schemas, see individual service READMEs._

## Database Schema

### Tables

- **documents**: Document metadata and file information
- **document_chunks**: Text chunks with vector embeddings

### Oracle Advanced Queues

- **VECTOR_PENDING_DOCUMENT**: Queue for documents awaiting chunking (processed by Chunker Service)
- **VECTOR_PENDING_CHUNK**: Queue for chunks awaiting embedding generation (processed by Vector Maker Service)

## Local Deployment

Visit this [LOCAL Deployment](LOCAL.md) step by step guide.

### Key Features

- Vector index on embeddings for fast similarity search
- SHA256-based file deduplication
- Automatic chunking with configurable overlap
- Connection pooling for optimal performance
- Liquibase-managed schema versioning and migrations

## Supported File Types

Multiple formats supported via Docling: PDF, DOCX, PPTX, HTML, TXT, MD

## Production Deployment

### Resource Requirements

- **API Service**: CPU-optimized, can scale horizontally
- **Chunker Service**: CPU-optimized, moderate memory for document processing
- **Vector Maker Service**: GPU with 14GB+ VRAM for embedding model
- **Database**: Oracle Database 23ai with sufficient storage for vectors

### Deployment Commands

**API Service:**

```bash
gunicorn app:app -c gunicorn.conf.py
```

**Chunker Service:**

```bash
gunicorn app:app -c gunicorn.conf.py
```

**Vector Maker Service:**

```bash
gunicorn app:app -c gunicorn.conf.py
```

### Monitoring

- Health endpoints for service status
- Comprehensive logging for debugging
- Database connection pool monitoring
- Queue depth monitoring for processing bottlenecks

## Performance Notes

- **API Service**: Horizontally scalable
- **Chunker/Vector Services**: Single worker recommended
- **Database**: Vector indexes for fast search
- Use provided `gunicorn.conf.py` for production settings

## License

This project is licensed under the MIT License - see below for details.

```
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
