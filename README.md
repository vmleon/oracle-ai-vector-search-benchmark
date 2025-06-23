# Oracle AI Vector Search Benchmark

## Introduction

This project provides a comprehensive benchmarking suite for Oracle AI Vector Search capabilities. It combines a Flask-based vector embedding service with performance testing tools to evaluate vector search operations at scale.

The benchmark uses a curated dataset of PDF documents from [Kaggle](https://www.kaggle.com/datasets/manisha717/dataset-of-pdf-files?resource=download) to test document parsing, embedding generation, and vector search performance. The application leverages vLLM for efficient vector embeddings using the `intfloat/e5-mistral-7b-instruct` model and docling for robust document parsing across multiple file formats.

Key features:
- **Vector Embedding Service**: Flask API for generating embeddings from text and uploaded documents
- **Document Processing**: Support for PDF, Word, PowerPoint, HTML, text, and Markdown files
- **Scalable Architecture**: Designed for integration with Oracle Database, Liquibase migrations, and monitoring tools
- **Performance Testing**: Built for integration with Locust for load testing and benchmarking

## Getting Started

### Prerequisites

- Python 3.8+
- Virtual environment support
- Git

### Quick Start

1. **Clone and setup the repository:**

```bash
git clone <repository-url>
cd oracle-ai-vector-search-benchmark
```

2. **Download and prepare the dataset:**

```bash
python local.py
```

This will automatically:
- Download the PDF dataset from Kaggle using kagglehub
- Extract files to the `samples/` directory
- Set up the required directory structure

3. **Set up the vector embedding service:**

```bash
cd src
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. **Start the embedding service:**

```bash
python vector_maker.py
```

The service will be available at `http://localhost:8000`

### API Usage

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
curl -X POST http://localhost:8000/upload \
  -F "file=@samples/your-document.pdf"
```

### Configuration

- **Model**: `intfloat/e5-mistral-7b-instruct`
- **Chunk size**: 512 characters with 50 character overlap
- **Server**: Runs on `0.0.0.0:8000`

## API Reference

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

Upload a file, parse it with docling, chunk the content, and generate embeddings.

**Request**: Multipart form with a `file` field

**Response:**
```json
{
  "filename": "document.pdf",
  "chunks_count": 5,
  "embeddings": [
    {
      "text": "First chunk of text...",
      "embedding": [0.1, 0.2, ...],
      "size": 4096
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

## TODO

This is a work in progress with the following planned features:

- Test document parsing across all supported formats
- Include Oracle Database integration for vector storage
- Include Liquibase for database schema management
- Include Locust benchmarking for performance testing
- Include Prometheus and Grafana for monitoring and visualization