# Stress Testing

This directory contains load testing tools for both vector search and document ingestion functionality using Locust.

## Test Suites

- **`vector_search/`** - Load testing for search endpoints
- **`ingestion/`** - Load testing for document upload endpoints

## Setup

### Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Running Tests

### Vector Search Benchmarks

Use the Python benchmark tool with .env configuration:

```bash
cd vector_search
python benchmark.py [options]
```

**Examples:**

```bash
# Use defaults from .env file
python benchmark.py

# Override specific parameters
python benchmark.py --users 50 --run-time 600s

# Test different environments
python benchmark.py --environment staging
python benchmark.py --environment production

# Custom host and parameters
python benchmark.py --host http://custom:8000 --users 100 --spawn-rate 10
```

### Document Ingestion Benchmarks

Test document upload performance with PDF files (run-to-completion mode):

```bash
cd ingestion
python benchmark.py [options]
```

**Note:** This measures how long it takes to upload all 19 PDF files once, not continuous load testing.
<!-- TODO: Make PDF file count dynamic based on actual files in samples directory -->

**Examples:**

```bash
# Use defaults from .env file (single user)
python benchmark.py

# 3 users uploading concurrently (57 total uploads)
# TODO: Update calculations when file count becomes dynamic
python benchmark.py --users 3 --spawn-rate 2

# 5 users uploading concurrently (95 total uploads)  
# TODO: Update calculations when file count becomes dynamic
python benchmark.py --users 5 --spawn-rate 3

# Compare environments
python benchmark.py --environment staging
python benchmark.py --environment production

# Custom configuration
python benchmark.py --host http://custom:8000 --users 2 --samples-dir /path/to/pdfs
```

**Available Options:**

- `--environment` / `-e`: Target environment (local, staging, production)
- `--users` / `-u`: Number of concurrent users
- `--spawn-rate` / `-r`: Users spawned per second  
- `--run-time` / `-t`: Test duration like `300s`, `10m`, `1h` (vector_search only)
- `--host`: Override target host URL
- `--samples-dir`: Directory containing PDF files (ingestion only)

**Defaults (from .env files):**
- Vector Search: 20 users, 2/s spawn rate, 300s duration
- Ingestion: 1 user, 1/s spawn rate, runs to completion

### Interactive Mode

For manual testing with web UI:

**Vector Search:**

```bash
cd vector_search
locust -f locustfile.py --host http://localhost:8000
```

**Document Ingestion:**

```bash
cd ingestion
locust -f locustfile.py --host http://localhost:8000
```

_Note: In interactive mode, ingestion still runs to completion per user_

Then open http://localhost:8089 in your browser to configure and start the load test.

### Headless Mode

For CI/CD or automated testing:

**Vector Search:**

```bash
cd vector_search
locust -f locustfile.py --host http://localhost:8000 --users 50 --spawn-rate 5 --run-time 300s --headless
```

**Document Ingestion:**

```bash
cd ingestion
locust -f locustfile.py --host http://localhost:8000 --users 3 --spawn-rate 2 --headless
```

_Note: No --run-time needed, test completes when all uploads finish_

## Configuration

### Environment Variables

Configuration is managed through `.env` files in each test directory.

**Vector Search** (`.env` in `vector_search/` directory):

```bash
# Locust Configuration (for interactive mode)
LOCUST_HOST=http://localhost:8000
SEARCH_LIMIT=5

# Benchmark Configuration (for Python script)
BENCHMARK_HOST=http://localhost:8000
BENCHMARK_USERS=20
BENCHMARK_SPAWN_RATE=2
BENCHMARK_RUN_TIME=300s
BENCHMARK_ENVIRONMENT=local

# Environment-specific Hosts
LOCAL_HOST=http://localhost:8000
STAGING_HOST=http://staging-api.yourcompany.com
PRODUCTION_HOST=http://api.yourcompany.com
```

**Document Ingestion** (`.env` in `ingestion/` directory):

```bash
# Locust Configuration (for interactive mode)
LOCUST_HOST=http://localhost:8000

# Benchmark Configuration (for Python script)
BENCHMARK_HOST=http://localhost:8000
BENCHMARK_USERS=1
BENCHMARK_SPAWN_RATE=1
BENCHMARK_ENVIRONMENT=local

# Environment-specific Hosts
LOCAL_HOST=http://localhost:8000
STAGING_HOST=http://staging-api.yourcompany.com
PRODUCTION_HOST=http://api.yourcompany.com

# File Upload Configuration
SAMPLES_DIR=../../../samples
MAX_FILE_SIZE=16777216
```

### Test Scenarios

**Vector Search** includes weighted tasks:

- **Vector Search** (weight: 10) - Main search functionality
- **Health Check** (weight: 2) - Service health monitoring
- **Status Check** (weight: 1) - System status monitoring

**Document Ingestion** uses run-to-completion approach:

- **Sequential Upload Task** - Uploads all 19 PDF files once per user, then stops
- **Self-terminating** - Users quit after completing all uploads
- **Timing Measurement** - Measures total time to upload all files

## Reports

The benchmark script generates comprehensive reports:

- **HTML Report** - Visual dashboard with charts and metrics
- **CSV Files** - Raw data for analysis (`*_stats.csv`, `*_failures.csv`)
- **Log File** - Detailed execution logs

Reports are saved in `vector_search/reports/` or `ingestion/reports/` directories respectively.

## Benchmark Metrics

Key metrics for performance comparison:

- **RPS (Requests Per Second)** - Throughput
- **Response Time** - Average, median, 95th percentile
- **Error Rate** - Percentage of failed requests
- **Concurrent Users** - Maximum sustainable load

## Troubleshooting

**Common Issues:**

- Ensure API service is running on target host
- Check firewall/network connectivity
- Verify sufficient system resources for load generation
- Monitor target system resources during testing
- **For ingestion tests**: Ensure PDF files exist in `samples/` directory

**Service Health Check:**

```bash
curl http://localhost:8000/health/ready
```

**File Availability Check:**

```bash
ls -la samples/*.pdf | head -20
```
