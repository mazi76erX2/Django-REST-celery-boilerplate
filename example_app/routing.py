"""
WebSocket URL routing for the example app.

This module defines the URL patterns for WebSocket connections.
"""

from django.urls import path, re_path

from . import consumers

websocket_urlpatterns = [
    path("ws/analysis/", consumers.AnalysisConsumer.as_asgi()),
    path("ws/tasks/", consumers.TaskStatusConsumer.as_asgi()),
    # Alternative with room support
    re_path(
        r"ws/analysis/(?P<room_name>\w+)/$",
        consumers.AnalysisConsumer.as_asgi(),
    ),
]
