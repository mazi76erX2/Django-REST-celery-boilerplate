"""
Gunicorn configuration file for production deployment.

This configuration is optimized for running Django with Channels
using Uvicorn workers.
"""

import multiprocessing
import os

# Server socket
bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")
backlog = 2048

# Worker processes
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
threads = int(os.environ.get("GUNICORN_THREADS", 2))

# Timeout configuration
timeout = 30
keepalive = 5
graceful_timeout = 30

# Request handling
max_requests = 10000
max_requests_jitter = 1000

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
capture_output = True
enable_stdio_inheritance = True

# Process naming
proc_name = "django-rest-api"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed, configure in nginx instead)
keyfile = None
certfile = None


# Hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    pass


def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    pass


def when_ready(server):
    """Called just after the server is started."""
    pass


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    pass


def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    pass


def worker_int(worker):
    """Called when a worker receives SIGINT or SIGQUIT."""
    pass


def worker_abort(worker):
    """Called when a worker receives SIGABRT."""
    pass


def pre_exec(server):
    """Called just before a new master process is forked."""
    pass


def child_exit(server, worker):
    """Called in the master process after a worker has exited."""
    pass


def worker_exit(server, worker):
    """Called in the worker process just after a worker has exited."""
    pass


def nworkers_changed(server, new_value, old_value):
    """Called when the number of workers has been changed."""
    pass


def on_exit(server):
    """Called just before exiting Gunicorn."""
    pass
