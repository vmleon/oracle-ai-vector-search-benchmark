# Local Deployment

## Prerequisites

- Linux/MacOS
- Python 3.8+
- Podman or Docker
- SQLcl

> Recommended: GPU with sufficient VRAM (for embedding model)

## Project Structure

```
src/
├── api_service/          # Document upload & search
├── chunker_service/      # Document processing & chunking
├── vector_maker_service/ # Embedding generation
├── shared/documents/     # Document storage
└── liquibase/            # Database schema
```

## Quick Start

### 1. Setup Environment and Database

Clone repository:

```bash
git clone https://github.com/vmleon/oracle-ai-vector-search-benchmark.git
cd oracle-ai-vector-search-benchmark
```

If not created already, create virtual environment for setup scripts:

```bash
python -m venv venv
```

Activate environment

```bash
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Setup dataset and database:

```bash
python local.py setup
```

This creates directories, downloads the dataset, starts Oracle Database, configures database settings, and creates required tables and queues.

## Service Setup

### API Service

Navigate to service directory:

```bash
cd src/api_service
```

If not created already, create virtual environment:

```bash
python -m venv venv
```

Activate environment

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure environment (create `.env` file):

```bash
# Database Configuration
ORACLE_USER=SYSTEM
ORACLE_PASSWORD=your_password
ORACLE_HOST=localhost
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=FREEPDB1
ORACLE_DSN=localhost:1521/FREEPDB1

# Database Connection Pool
ORACLE_POOL_MIN=2
ORACLE_POOL_MAX=10
ORACLE_POOL_INCREMENT=1
ORACLE_POOL_PING_INTERVAL=60

# API Service Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=True
API_MAX_FILE_SIZE=16777216
API_CORS_ORIGINS=*

# Document Storage
DOCUMENTS_STORAGE_PATH=../shared/documents

# Dependent Services
VECTOR_SERVICE_URL=http://localhost:8001
CHUNKER_SERVICE_URL=http://localhost:8002
```

Run with gunicorn:

```bash
gunicorn app:app -c gunicorn.conf.py
```

### Chunker Service

Navigate to service directory:

```bash
cd src/chunker_service
```

If not created already, create virtual environment:

```bash
python -m venv venv
```

Activate environment

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure environment (create `.env` file):

```bash
# Database Configuration
ORACLE_USER=SYSTEM
ORACLE_PASSWORD=your_password
ORACLE_HOST=localhost
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=FREEPDB1
ORACLE_DSN=localhost:1521/FREEPDB1

# Database Connection Pool
ORACLE_POOL_MIN=2
ORACLE_POOL_MAX=10
ORACLE_POOL_INCREMENT=1
ORACLE_POOL_PING_INTERVAL=60

# Chunker Service Configuration
CHUNKER_HOST=0.0.0.0
CHUNKER_PORT=8002
CHUNKER_DEBUG=True
CHUNKER_CORS_ORIGINS=*
CHUNKER_CHUNK_SIZE=512
CHUNKER_CHUNK_OVERLAP=50

# Document Storage
DOCUMENTS_STORAGE_PATH=../shared/documents
```

Run with gunicorn:

```bash
gunicorn app:app -c gunicorn.conf.py
```

### Vector Maker Service

Navigate to service directory:

```bash
cd src/vector_maker_service
```

If not created already, create virtual environment:

```bash
python -m venv venv
```

Act

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure environment (create `.env` file):

```bash
# Database Configuration
ORACLE_USER=SYSTEM
ORACLE_PASSWORD=your_password
ORACLE_HOST=localhost
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=FREEPDB1
ORACLE_DSN=localhost:1521/FREEPDB1

# Database Connection Pool
ORACLE_POOL_MIN=2
ORACLE_POOL_MAX=10
ORACLE_POOL_INCREMENT=1
ORACLE_POOL_PING_INTERVAL=60

# Vector Maker Service Configuration
VECTOR_HOST=0.0.0.0
VECTOR_PORT=8001
VECTOR_DEBUG=True
VECTOR_CORS_ORIGINS=*
VECTOR_MODEL=intfloat/e5-mistral-7b-instruct
VECTOR_ENFORCE_EAGER=True
```

Run with gunicorn:

```bash
gunicorn app:app -c gunicorn.conf.py
```

## Health checks

API Service

```bash
curl http://localhost:8000/health/ready | jq .
```

Chunker Service

```bash
curl http://localhost:8002/health/ready | jq .
```

Vector Maker Service

```bash
curl http://localhost:8001/health/ready | jq .
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
