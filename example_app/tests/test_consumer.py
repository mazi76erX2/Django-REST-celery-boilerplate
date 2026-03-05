"""
Tests for WebSocket consumers.
"""

import pytest
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TestCase

from example_app.routing import websocket_urlpatterns


def make_communicator(path: str) -> WebsocketCommunicator:
    return WebsocketCommunicator(URLRouter(websocket_urlpatterns), path)


@pytest.mark.asyncio
class AnalysisConsumerTest(TestCase):
    """Tests for the AnalysisConsumer WebSocket consumer."""

    async def test_connect(self):
        """Test WebSocket connection and welcome message."""
        communicator = make_communicator("/ws/analysis/")
        connected, _ = await communicator.connect()

        assert connected
        response = await communicator.receive_json_from()
        assert response["type"] == "connection_established"
        assert "channel" in response

        await communicator.disconnect()

    async def test_ping_pong(self):
        """Test ping/pong health check."""
        communicator = make_communicator("/ws/analysis/")
        await communicator.connect()
        await communicator.receive_json_from()

        await communicator.send_json_to({"type": "ping", "timestamp": "123456"})

        response = await communicator.receive_json_from()
        assert response["type"] == "pong"
        assert response["timestamp"] == "123456"

        await communicator.disconnect()

    async def test_analyze_missing_text(self):
        """Test analyze with missing text field returns error."""
        communicator = make_communicator("/ws/analysis/")
        await communicator.connect()
        await communicator.receive_json_from()

        await communicator.send_json_to({"type": "analyze"})

        response = await communicator.receive_json_from()
        assert response["type"] == "error"
        assert "text" in response["message"].lower()

        await communicator.disconnect()

    async def test_analyze_dispatches_task(self):
        """Test that analyze with text creates an analysis and dispatches a task."""
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_analysis = MagicMock()
        mock_analysis.id = 1

        communicator = make_communicator("/ws/analysis/")
        await communicator.connect()
        await communicator.receive_json_from()

        with (
            patch("example_app.tasks.analyse_sentiment_task") as mock_task,
            patch(
                "example_app.consumers.AnalysisConsumer.create_analysis",
                new_callable=AsyncMock,
                return_value=mock_analysis,
            ),
        ):
            await communicator.send_json_to(
                {"type": "analyze", "text": "Testing WebSocket analysis"}
            )

            response = await communicator.receive_json_from()
            assert response["type"] == "analysis_started"
            assert "analysis_id" in response
            assert response["status"] == "processing"
            mock_task.delay.assert_called_once()

        await communicator.disconnect()

    async def test_bulk_analyze_missing_texts(self):
        """Test bulk_analyze with empty texts returns error."""
        communicator = make_communicator("/ws/analysis/")
        await communicator.connect()
        await communicator.receive_json_from()

        await communicator.send_json_to({"type": "bulk_analyze", "texts": []})

        response = await communicator.receive_json_from()
        assert response["type"] == "error"
        assert "texts" in response["message"].lower()

        await communicator.disconnect()

    async def test_bulk_analyze_dispatches_task(self):
        """Test bulk_analyze with valid texts queues a task."""
        from unittest.mock import patch

        communicator = make_communicator("/ws/analysis/")
        await communicator.connect()
        await communicator.receive_json_from()

        with patch("example_app.tasks.bulk_analyse_sentiment_task") as mock_task:
            mock_task.delay.return_value = None
            await communicator.send_json_to(
                {
                    "type": "bulk_analyze",
                    "texts": ["First text", "Second text", "Third text"],
                }
            )

            response = await communicator.receive_json_from()
            assert response["type"] == "bulk_analysis_started"
            assert response["total"] == 3
            assert response["status"] == "processing"
            assert "group" in response
            mock_task.delay.assert_called_once()

        await communicator.disconnect()

    async def test_subscribe_missing_analysis_id(self):
        """Test subscribe without analysis_id returns error."""
        communicator = make_communicator("/ws/analysis/")
        await communicator.connect()
        await communicator.receive_json_from()

        await communicator.send_json_to({"type": "subscribe"})

        response = await communicator.receive_json_from()
        assert response["type"] == "error"
        assert "analysis_id" in response["message"].lower()

        await communicator.disconnect()

    async def test_subscribe_to_analysis(self):
        """Test subscribing to a specific analysis ID."""
        communicator = make_communicator("/ws/analysis/")
        await communicator.connect()
        await communicator.receive_json_from()

        await communicator.send_json_to({"type": "subscribe", "analysis_id": 42})

        response = await communicator.receive_json_from()
        assert response["type"] == "subscribed"
        assert response["analysis_id"] == 42

        await communicator.disconnect()

    async def test_get_status_missing_analysis_id(self):
        """Test get_status without analysis_id returns error."""
        communicator = make_communicator("/ws/analysis/")
        await communicator.connect()
        await communicator.receive_json_from()

        await communicator.send_json_to({"type": "get_status"})

        response = await communicator.receive_json_from()
        assert response["type"] == "error"
        assert "analysis_id" in response["message"].lower()

        await communicator.disconnect()

    async def test_get_status_not_found(self):
        """Test get_status with non-existent analysis_id returns error."""
        from unittest.mock import AsyncMock, patch

        communicator = make_communicator("/ws/analysis/")
        await communicator.connect()
        await communicator.receive_json_from()

        with patch(
            "example_app.consumers.AnalysisConsumer.get_analysis",
            new_callable=AsyncMock,
            return_value=None,
        ):
            await communicator.send_json_to(
                {"type": "get_status", "analysis_id": 99999}
            )

            response = await communicator.receive_json_from()
            assert response["type"] == "error"
            assert "not found" in response["message"].lower()

        await communicator.disconnect()

    async def test_get_status_existing_analysis(self):
        """Test get_status returns correct data for an existing analysis."""
        from datetime import UTC, datetime
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_analysis = MagicMock()
        mock_analysis.id = 7
        mock_analysis.text = "Status test text"
        mock_analysis.status = "completed"
        mock_analysis.sentiment = "positive"
        mock_analysis.confidence_score = 0.95
        mock_analysis.created_at = datetime(2025, 1, 1, tzinfo=UTC)

        communicator = make_communicator("/ws/analysis/")
        await communicator.connect()
        await communicator.receive_json_from()

        with patch(
            "example_app.consumers.AnalysisConsumer.get_analysis",
            new_callable=AsyncMock,
            return_value=mock_analysis,
        ):
            await communicator.send_json_to(
                {"type": "get_status", "analysis_id": mock_analysis.id}
            )

            response = await communicator.receive_json_from()
            assert response["type"] == "status"
            assert response["analysis_id"] == mock_analysis.id
            assert response["status"] == "completed"
            assert response["sentiment"] == "positive"
            assert response["confidence_score"] == 0.95

        await communicator.disconnect()

    async def test_unknown_message_type(self):
        """Test handling of unknown message type returns error."""
        communicator = make_communicator("/ws/analysis/")
        await communicator.connect()
        await communicator.receive_json_from()

        await communicator.send_json_to({"type": "unknown_type"})

        response = await communicator.receive_json_from()
        assert response["type"] == "error"
        assert "unknown" in response["message"].lower()

        await communicator.disconnect()

    async def test_disconnect_cleans_up(self):
        """Test that disconnect removes the consumer from its group."""
        communicator = make_communicator("/ws/analysis/")
        connected, _ = await communicator.connect()
        assert connected
        await communicator.receive_json_from()

        await communicator.disconnect()
        # No assertion needed — disconnect() itself would raise if cleanup fails


@pytest.mark.asyncio
class TaskStatusConsumerTest(TestCase):
    """Tests for the TaskStatusConsumer WebSocket consumer."""

    async def test_connect(self):
        """Test WebSocket connection and welcome message."""
        communicator = make_communicator("/ws/tasks/")
        connected, _ = await communicator.connect()

        assert connected
        response = await communicator.receive_json_from()
        assert response["type"] == "connection_established"

        await communicator.disconnect()

    async def test_get_task_status_missing_id(self):
        """Test get_task_status without task_id returns error."""
        communicator = make_communicator("/ws/tasks/")
        await communicator.connect()
        await communicator.receive_json_from()

        await communicator.send_json_to({"type": "get_task_status"})

        response = await communicator.receive_json_from()
        assert response["type"] == "error"
        assert "task_id" in response["message"].lower()

        await communicator.disconnect()

    async def test_get_task_status_with_id(self):
        """Test get_task_status with a task_id returns status response."""
        from unittest.mock import MagicMock, patch

        mock_result = MagicMock()
        mock_result.status = "PENDING"
        mock_result.ready.return_value = False
        mock_result.result = None

        communicator = make_communicator("/ws/tasks/")
        await communicator.connect()
        await communicator.receive_json_from()

        with patch("celery.result.AsyncResult", return_value=mock_result):
            await communicator.send_json_to(
                {"type": "get_task_status", "task_id": "fake-task-id-123"}
            )

            response = await communicator.receive_json_from()
            assert response["type"] == "task_status"
            assert response["task_id"] == "fake-task-id-123"
            assert "status" in response

        await communicator.disconnect()

    async def test_subscribe_task(self):
        """Test subscribing to a specific task ID."""
        communicator = make_communicator("/ws/tasks/")
        await communicator.connect()
        await communicator.receive_json_from()

        await communicator.send_json_to(
            {"type": "subscribe_task", "task_id": "my-task-abc"}
        )

        response = await communicator.receive_json_from()
        assert response["type"] == "subscribed"
        assert response["task_id"] == "my-task-abc"

        await communicator.disconnect()

    async def test_disconnect_cleans_up(self):
        """Test that disconnect removes the consumer from its group."""
        communicator = make_communicator("/ws/tasks/")
        connected, _ = await communicator.connect()
        assert connected
        await communicator.receive_json_from()

        await communicator.disconnect()
