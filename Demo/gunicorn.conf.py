"""
Gunicorn configuration for production deployment
"""
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
# Container hat 0.5 CPU / 1Gi RAM → 1 Worker reicht, LLM-Calls sind I/O-bound
workers = int(os.getenv("GUNICORN_WORKERS", "1"))
worker_class = "sync"
worker_connections = 1000
timeout = 600  # 10 Minuten für LLM-Calls
keepalive = 5

# Restart workers after this many requests (prevent memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "agentic-ai-backend"

# Initialisiere das Agent-System in jedem Worker nach dem Fork
def post_fork(server, worker):
    import sys
    sys.path.insert(0, "/app")
    from web_server import initialize_system
    initialize_system()

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (handled by Azure)
keyfile = None
certfile = None
