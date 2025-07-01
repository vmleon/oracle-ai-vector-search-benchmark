import os
import platform

bind = "0.0.0.0:8002"
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# Worker tmp directory - use /dev/shm if available (Linux), fallback to /tmp
if platform.system() == "Linux" and os.path.exists("/dev/shm"):
    worker_tmp_dir = "/dev/shm"
else:
    worker_tmp_dir = "/tmp"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "chunker_service"

# Preload app for better performance
preload_app = True

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190