from .base import *

ALLOWED_HOSTS = ["0.0.0.0", "localhost", "127.0.0.1"]

# define which origins are allowed
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

INSTALLED_APPS += [
    "debug_toolbar",
]

MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]

# Celery - Eager execution for easier debugging in development
# Set to True to execute tasks synchronously (useful for debugging)
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = True
