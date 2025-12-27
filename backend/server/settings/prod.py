import os
from pathlib import Path

from .base import *

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DATABASE_NAME", "server"),
        "USER": os.environ.get("DATABASE_USERNAME", "postgres"),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", "postgres"),
        "HOST": os.environ.get("DATABASE_HOST", "db"),
        "PORT": os.environ.get("DATABASE_PORT", "5432"),
    }
}

DEBUG = False

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOST_DNS", "").split(" ")

# For admin static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
CSRF_TRUSTED_ORIGINS = ["http://localhost:1337", "https://yourdomain.com"]

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Celery production settings
CELERY_TASK_ALWAYS_EAGER = False
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
