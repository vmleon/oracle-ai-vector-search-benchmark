# Local Deployment

## Prerequisites

- Oracle Database 23ai with AI Vector Search
- Python 3.8+
- Podman or Docker
- SQLcl

> Recommended: GPU with sufficient VRAM (for embedding model)

## Development

### Project Structure

```
src/
├── api_service/          # Document upload & search
├── chunker_service/      # Document processing & chunking
├── vector_maker_service/ # Embedding generation
├── shared/documents/     # Document storage
└── liquibase/            # Database schema
```

### Architecture Principles

- Microservices with clear separation of concerns
- Independent deployment and scaling
- Queue-based async processing

## Quick Start

### 1. Setup Environment and Database

```bash
# Clone repository
git clone https://github.com/vmleon/oracle-ai-vector-search-benchmark.git
cd oracle-ai-vector-search-benchmark

# Create virtual environment for setup scripts
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup dataset and database
python local.py setup
```

This will create directories, download the dataset, start Oracle Database, configure database settings, and create required tables and queues - providing a complete environment setup.

### 2. Install Service Dependencies

**API Service:**

```bash
cd src/api_service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Chunker Service:**

```bash
cd src/chunker_service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Vector Maker Service:**

```bash
cd src/vector_maker_service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` files in all service directories:

```bash
# Database Configuration (all services)
ORACLE_USER=SYSTEM
ORACLE_PASSWORD=your_password
ORACLE_HOST=localhost
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=FREEPDB1

# API Service specific (.env in src/api_service/)
API_HOST=0.0.0.0
API_PORT=8000
API_MAX_FILE_SIZE=16777216

# Chunker Service specific (.env in src/chunker_service/)
CHUNKER_HOST=0.0.0.0
CHUNKER_PORT=8002
CHUNKER_CHUNK_SIZE=512
CHUNKER_CHUNK_OVERLAP=50
DOCUMENTS_STORAGE_PATH=../shared/documents

# Vector Maker Service specific (.env in src/vector_maker_service/)
VECTOR_HOST=0.0.0.0
VECTOR_PORT=8001
VECTOR_MODEL=intfloat/e5-mistral-7b-instruct
VECTOR_ENFORCE_EAGER=True
```

### 4. Run Services

**Start Vector Maker Service (first):**

```bash
cd src/vector_maker_service
source venv/bin/activate
python app.py
# or with gunicorn (recommended): gunicorn app:app -c gunicorn.conf.py
```

**Start Chunker Service:**

```bash
cd src/chunker_service
source venv/bin/activate
python app.py
# or with gunicorn (recommended): gunicorn app:app -c gunicorn.conf.py
```

**Start API Service:**

```bash
cd src/api_service
source venv/bin/activate
python app.py
# or with gunicorn (recommended): gunicorn app:app -c gunicorn.conf.py
```

## Usage Examples

### Upload Document

```bash
curl -X POST -F "file=@samples/document.pdf" http://localhost:8000/upload
```

### Search Documents

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"query": "machine learning algorithms", "limit": 5}' \
  http://localhost:8000/search
```

### Generate Embeddings (Direct)

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"texts": ["text to embed"]}' \
  http://localhost:8001/embeddings
```

### Health Checks

```bash
# API Service health
curl http://localhost:8000/health

# Chunker Service health
curl http://localhost:8002/health

# Vector Maker Service health
curl http://localhost:8001/health
```

## Cleanup

When finished:

```bash
python local.py cleanup
```

This stops the Oracle Database container and cleans up sample files.

## Troubleshooting

Common issues:

- **GPU memory**: 14GB+ VRAM required for embedding model
- **Database connectivity**: Check Oracle Database connection settings
- **Port conflicts**: Ensure ports 8000, 8001, and 8002 are available
- **Service health**: Check service health endpoints and logs for debugging
