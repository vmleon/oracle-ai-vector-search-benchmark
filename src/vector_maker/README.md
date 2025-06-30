# Vector Search Benchmark

A Flask application that provides vector embeddings using vLLM with support for text input and file uploads with document parsing.

## Setup

### 1. Create and activate virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
gunicorn -w 1 -b 0.0.0.0:8000 app:app
```

The application will start on `http://localhost:8000`

## API Endpoints

### 1. Text Embeddings Endpoint

Generate embeddings for an array of text strings.

**Endpoint:** `POST /embeddings`

**Request body:**

```json
{
  "texts": ["Your text here", "Another text"]
}
```

**cURL example:**

```bash
curl -X POST http://localhost:8000/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "This is a sample text for embedding",
      "Another example text to process"
    ]
  }'
```

### 2. File Upload Endpoint

Upload a file, parse it with docling, chunk the content, and generate embeddings.

**Endpoint:** `POST /upload`

**Request:** Multipart form with a `file` field

**cURL example:**

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@/path/to/your/document.pdf"
```

**Example with a text file:**

```bash
# Create a sample text file
echo "This is a sample document with multiple sentences. It will be parsed by docling and chunked into smaller pieces for embedding generation." > sample.txt

# Upload the file
curl -X POST http://localhost:8000/upload \
  -F "file=@../samples/0a29925ccc5e6299e132a73325956a3abef6dd26.pdf"
```

## Response Format

### Text Embeddings Response

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

### File Upload Response

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

## Supported File Types

The application uses docling for document parsing, which supports:

- PDF files
- Word documents (.docx)
- PowerPoint presentations (.pptx)
- HTML files
- Text files
- Markdown files

## Configuration

- **Model:** `intfloat/e5-mistral-7b-instruct`
- **Chunk size:** 512 characters
- **Chunk overlap:** 50 characters
- **Server:** `0.0.0.0:8000`
