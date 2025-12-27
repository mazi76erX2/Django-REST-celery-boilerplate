"""
Celery configuration for the Django project.
"""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    os.environ.get("DJANGO_SETTINGS_MODULE", "server.settings.local"),
)

app = Celery("server")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

# Periodic tasks configuration
app.conf.beat_schedule = {
    "cleanup-old-analyses-every-hour": {
        "task": "example_app.tasks.cleanup_old_analyses",
        "schedule": crontab(minute=0),
        "args": (30,),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f"Request: {self.request!r}")
