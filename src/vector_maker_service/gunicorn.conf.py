# Gunicorn configuration for Vector Maker Service
import os

# Server socket
bind = "0.0.0.0:8001"
backlog = 2048

# Worker processes - single worker for GPU model
workers = 1
worker_class = "sync"
worker_connections = 1000
keepalive = 2

# Worker timeout - very important for model loading
timeout = 600  # 10 minutes for model loading
graceful_timeout = 60

# Memory management
max_requests = 50  # Lower to prevent memory buildup with large models
max_requests_jitter = 10
preload_app = False  # Don't preload to avoid GPU conflicts

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "vector_maker_service"

# Resource limits - cross-platform compatible
if os.path.exists("/dev/shm"):
    worker_tmp_dir = "/dev/shm"  # Use memory-based tmp on Linux
# On macOS/Windows, use default tmp directory