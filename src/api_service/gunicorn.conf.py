# Gunicorn configuration for API Service

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 2
worker_class = "sync"
worker_connections = 1000
keepalive = 2

# Worker timeout - important for document processing
timeout = 300
graceful_timeout = 30

# Memory management
max_requests = 100
max_requests_jitter = 50
preload_app = False  # Set to False to avoid docling initialization in master process

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "api_service"