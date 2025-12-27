"""
Tests for WebSocket consumers.
"""

from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TestCase, override_settings

import pytest

from example_app.consumers import AnalysisConsumer, TaskStatusConsumer
from example_app.routing import websocket_urlpatterns


@pytest.mark.asyncio
class AnalysisConsumerTest(TestCase):
    """Tests for the AnalysisConsumer WebSocket consumer."""

    async def test_connect(self):
        """Test WebSocket connection."""
        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(application, "/ws/analysis/")

        connected, _ = await communicator.connect()
        assert connected

        # Should receive connection established message
        response = await communicator.receive_json_from()
        assert response["type"] == "connection_established"

        await communicator.disconnect()

    async def test_ping_pong(self):
        """Test ping/pong functionality."""
        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(application, "/ws/analysis/")

        await communicator.connect()
        # Consume connection message
        await communicator.receive_json_from()

        # Send ping
        await communicator.send_json_to({"type": "ping", "timestamp": "123456"})

        # Should receive pong
        response = await communicator.receive_json_from()
        assert response["type"] == "pong"
        assert response["timestamp"] == "123456"

        await communicator.disconnect()

    async def test_analyze_missing_text(self):
        """Test analyze with missing text field."""
        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(application, "/ws/analysis/")

        await communicator.connect()
        await communicator.receive_json_from()

        # Send analyze without text
        await communicator.send_json_to({"type": "analyze"})

        response = await communicator.receive_json_from()
        assert response["type"] == "error"
        assert "text" in response["message"].lower()

        await communicator.disconnect()

    async def test_unknown_message_type(self):
        """Test handling of unknown message type."""
        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(application, "/ws/analysis/")

        await communicator.connect()
        await communicator.receive_json_from()

        # Send unknown message type
        await communicator.send_json_to({"type": "unknown_type"})

        response = await communicator.receive_json_from()
        assert response["type"] == "error"
        assert "unknown" in response["message"].lower()

        await communicator.disconnect()


@pytest.mark.asyncio
class TaskStatusConsumerTest(TestCase):
    """Tests for the TaskStatusConsumer WebSocket consumer."""

    async def test_connect(self):
        """Test WebSocket connection."""
        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(application, "/ws/tasks/")

        connected, _ = await communicator.connect()
        assert connected

        response = await communicator.receive_json_from()
        assert response["type"] == "connection_established"

        await communicator.disconnect()

    async def test_get_task_status_missing_id(self):
        """Test get_task_status without task_id."""
        application = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(application, "/ws/tasks/")

        await communicator.connect()
        await communicator.receive_json_from()

        await communicator.send_json_to({"type": "get_task_status"})

        response = await communicator.receive_json_from()
        assert response["type"] == "error"

        await communicator.disconnect()
