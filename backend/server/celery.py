"""
Celery configuration for the Django project.

This module sets up the Celery application and configures it to use Django settings.
"""

import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings.local")

app = Celery("server")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


# Optional: Configure periodic tasks using Celery Beat
app.conf.beat_schedule = {
    # Example periodic task - runs every hour
    "cleanup-old-analyses-every-hour": {
        "task": "example_app.tasks.cleanup_old_analyses",
        "schedule": crontab(minute=0),  # Every hour at minute 0
        "args": (30,),  # Delete analyses older than 30 days
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f"Request: {self.request!r}")
