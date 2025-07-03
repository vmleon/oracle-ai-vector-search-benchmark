# Vector Search Stress Testing

This directory contains load testing tools for vector search functionality using Locust.

## Setup

### Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Running Tests

### Run Locust for Vector Search
```bash
locust -f vector_search/locustfile.py
```

Then open http://localhost:8089 in your browser to configure and start the load test.