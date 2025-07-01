# Vector Maker Service

The Vector Maker Service handles embedding generation for text chunks. It provides an embedding API endpoint and runs a background worker that processes chunks from the queue to generate embeddings.

## Features

- Text embedding generation API
- Background worker for processing queued chunks
- Integration with Oracle Advanced Queues
- Health checks

## Dependencies

- vLLM for embedding model inference
- Flask for web framework
- Oracle Database for storage
- Oracle Advanced Queues for async processing

## Configuration

Set environment variables:

```bash
# Service Configuration
VECTOR_HOST=0.0.0.0
VECTOR_PORT=8001
VECTOR_DEBUG=True
VECTOR_CORS_ORIGINS=*

# Model Configuration
VECTOR_MODEL=intfloat/e5-mistral-7b-instruct
VECTOR_ENFORCE_EAGER=True

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

3. Ensure Oracle Database is running with the `vector_pending_chunk` `vector_pending_document` queue created

4. Ensure sufficient GPU memory for the embedding model

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
gunicorn app:app -b 0.0.0.0:8001 -w 1 --timeout 600 --max-requests 50
```

**Note:** Use `-w 1` (single worker) for GPU models to avoid conflicts.

## API Endpoints

### POST /embeddings

Generate embeddings for text arrays.

**Request:**

```json
{
  "texts": ["text 1", "text 2", "text 3"]
}
```

**Response:**

```json
{
  "embeddings": [
    {
      "text": "text 1",
      "embedding": [0.1, 0.2, 0.3, ...],
      "size": 4096
    }
  ]
}
```

### GET /health

Health check endpoint.

## Background Worker

The service automatically starts a background worker that:

1. **Dequeues chunks** from the `vector_pending_chunk` Oracle AQ
2. **Generates embeddings** using the loaded model
3. **Updates the database** with the generated embeddings
4. **Continues processing** until the service is stopped

## Architecture

The Vector Maker Service operates as:

1. **API Server**: Provides on-demand embedding generation
2. **Background Worker**: Processes queued chunks automatically
3. **Model Management**: Loads and manages the embedding model
4. **Database Integration**: Updates chunk embeddings in the database

## Model Information

Default model: `intfloat/e5-mistral-7b-instruct`

- High-quality multilingual embeddings
- 4096-dimensional vectors
- Requires significant GPU memory (~14GB)

## Performance Considerations

- **GPU Memory**: Ensure sufficient VRAM for the model
- **Batch Processing**: Worker processes one chunk at a time
- **Timeout**: Set appropriate gunicorn timeout for model loading (600s recommended)
- **Concurrency**: Use single worker to avoid GPU conflicts
- **Configuration**: Use `gunicorn.conf.py` for optimized production settings
- **Memory Management**: Lower `max_requests` prevents memory buildup with large models

## Monitoring

Monitor the service logs for:

- Model loading progress
- Worker processing status
- Queue processing rate
- Error conditions

## Notes

- The service must run alongside the api_service for complete functionality
- Model loading can take several minutes on first startup
- Worker automatically starts when the service initializes
- Designed for high-throughput embedding generation
