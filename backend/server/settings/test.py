"""
Test settings — overrides for running pytest locally against the Docker-managed
postgres (exposed on localhost:5432) and valkey (localhost:6379) instances.
"""

from .local import *

DATABASES["default"]["HOST"] = "localhost"  # type: ignore[index]
DATABASES["default"]["PORT"] = "5432"  # type: ignore[index]

CACHES["default"]["LOCATION"] = "redis://localhost:6379/1"  # type: ignore[index]

CELERY_BROKER_URL = "redis://localhost:6379/1"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
