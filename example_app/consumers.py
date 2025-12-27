"""
WebSocket consumers for the example app.

This module contains Django Channels consumers for handling
WebSocket connections and real-time communication.
"""

import json
import logging
from typing import Any

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.cache import cache

logger = logging.getLogger(__name__)


class AnalysisConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time analysis updates.

    Handles:
    - Single text analysis with real-time results
    - Bulk analysis with progress updates
    - Subscription to analysis updates by ID
    """

    async def connect(self) -> None:
        """Handle WebSocket connection."""
        self.user = self.scope.get("user")
        self.room_group_name = "analysis_updates"

        # Join the general analysis updates group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()
        logger.info(f"WebSocket connected: {self.channel_name}")

        await self.send_json(
            {
                "type": "connection_established",
                "message": "Connected to analysis updates",
                "channel": self.channel_name,
            }
        )

    async def disconnect(self, close_code: int) -> None:
        """Handle WebSocket disconnection."""
        # Leave the room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        logger.info(f"WebSocket disconnected: {self.channel_name}, code: {close_code}")

    async def receive_json(self, content: dict[str, Any]) -> None:
        """
        Handle incoming WebSocket messages.

        Message types:
        - analyze: Start a new analysis
        - bulk_analyze: Start bulk analysis
        - subscribe: Subscribe to specific analysis updates
        - ping: Health check
        """
        message_type = content.get("type")

        handlers = {
            "analyze": self.handle_analyze,
            "bulk_analyze": self.handle_bulk_analyze,
            "subscribe": self.handle_subscribe,
            "ping": self.handle_ping,
            "get_status": self.handle_get_status,
        }

        handler = handlers.get(message_type)
        if handler:
            await handler(content)
        else:
            await self.send_json(
                {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                }
            )

    async def handle_analyze(self, content: dict[str, Any]) -> None:
        """Handle single text analysis request."""
        from example_app.tasks import analyse_sentiment_task

        text = content.get("text")
        if not text:
            await self.send_json(
                {
                    "type": "error",
                    "message": "Missing 'text' field",
                }
            )
            return

        # Create analysis record
        analysis = await self.create_analysis(text)

        # Send acknowledgment
        await self.send_json(
            {
                "type": "analysis_started",
                "analysis_id": analysis.id,
                "text": text[:100],
                "status": "processing",
            }
        )

        # Dispatch Celery task
        analyse_sentiment_task.delay(
            text=text,
            analysis_id=analysis.id,
            channel_name=self.channel_name,
            group_name=self.room_group_name,
        )

    async def handle_bulk_analyze(self, content: dict[str, Any]) -> None:
        """Handle bulk text analysis request."""
        from example_app.tasks import bulk_analyse_sentiment_task

        texts = content.get("texts", [])
        if not texts:
            await self.send_json(
                {
                    "type": "error",
                    "message": "Missing or empty 'texts' field",
                }
            )
            return

        # Create a unique group for this bulk operation
        import uuid

        bulk_group_name = f"bulk_analysis_{uuid.uuid4().hex[:8]}"

        # Join the bulk operation group
        await self.channel_layer.group_add(bulk_group_name, self.channel_name)

        # Send acknowledgment
        await self.send_json(
            {
                "type": "bulk_analysis_started",
                "total": len(texts),
                "group": bulk_group_name,
                "status": "processing",
            }
        )

        # Dispatch Celery task
        bulk_analyse_sentiment_task.delay(
            texts=texts,
            group_name=bulk_group_name,
        )

    async def handle_subscribe(self, content: dict[str, Any]) -> None:
        """Subscribe to updates for a specific analysis."""
        analysis_id = content.get("analysis_id")
        if not analysis_id:
            await self.send_json(
                {
                    "type": "error",
                    "message": "Missing 'analysis_id' field",
                }
            )
            return

        # Create a group for this specific analysis
        analysis_group = f"analysis_{analysis_id}"
        await self.channel_layer.group_add(analysis_group, self.channel_name)

        await self.send_json(
            {
                "type": "subscribed",
                "analysis_id": analysis_id,
            }
        )

    async def handle_ping(self, content: dict[str, Any]) -> None:
        """Handle ping/pong for connection health check."""
        await self.send_json(
            {
                "type": "pong",
                "timestamp": content.get("timestamp"),
            }
        )

    async def handle_get_status(self, content: dict[str, Any]) -> None:
        """Get status of an analysis."""
        analysis_id = content.get("analysis_id")
        if not analysis_id:
            await self.send_json(
                {
                    "type": "error",
                    "message": "Missing 'analysis_id' field",
                }
            )
            return

        analysis = await self.get_analysis(analysis_id)
        if analysis:
            await self.send_json(
                {
                    "type": "status",
                    "analysis_id": analysis.id,
                    "text": analysis.text[:100],
                    "sentiment": analysis.sentiment,
                    "confidence_score": analysis.confidence_score,
                    "status": analysis.status,
                    "created_at": analysis.created_at.isoformat(),
                }
            )
        else:
            await self.send_json(
                {
                    "type": "error",
                    "message": f"Analysis {analysis_id} not found",
                }
            )

    # Channel layer message handlers

    async def analysis_complete(self, event: dict[str, Any]) -> None:
        """Handle analysis completion message from Celery task."""
        await self.send_json(
            {
                "type": "analysis_complete",
                "data": event["data"],
            }
        )

    async def analysis_progress(self, event: dict[str, Any]) -> None:
        """Handle analysis progress message from Celery task."""
        await self.send_json(
            {
                "type": "analysis_progress",
                "data": event["data"],
            }
        )

    async def analysis_bulk_complete(self, event: dict[str, Any]) -> None:
        """Handle bulk analysis completion message from Celery task."""
        await self.send_json(
            {
                "type": "bulk_analysis_complete",
                "data": event["data"],
            }
        )

    # Database operations

    @database_sync_to_async
    def create_analysis(self, text: str):
        """Create a new Analysis record."""
        from example_app.models import Analysis

        return Analysis.objects.create(text=text, status="pending")

    @database_sync_to_async
    def get_analysis(self, analysis_id: int):
        """Get an Analysis record by ID."""
        from example_app.models import Analysis

        try:
            return Analysis.objects.get(id=analysis_id)
        except Analysis.DoesNotExist:
            return None


class TaskStatusConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for monitoring Celery task status.

    Allows clients to subscribe to task status updates.
    """

    async def connect(self) -> None:
        """Handle WebSocket connection."""
        self.task_group = "celery_tasks"

        await self.channel_layer.group_add(self.task_group, self.channel_name)
        await self.accept()

        await self.send_json(
            {
                "type": "connection_established",
                "message": "Connected to task status updates",
            }
        )

    async def disconnect(self, close_code: int) -> None:
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(self.task_group, self.channel_name)

    async def receive_json(self, content: dict[str, Any]) -> None:
        """Handle incoming messages."""
        message_type = content.get("type")

        if message_type == "get_task_status":
            await self.handle_get_task_status(content)
        elif message_type == "subscribe_task":
            await self.handle_subscribe_task(content)

    async def handle_get_task_status(self, content: dict[str, Any]) -> None:
        """Get status of a specific Celery task."""
        from celery.result import AsyncResult

        task_id = content.get("task_id")
        if not task_id:
            await self.send_json({"type": "error", "message": "Missing task_id"})
            return

        result = AsyncResult(task_id)
        await self.send_json(
            {
                "type": "task_status",
                "task_id": task_id,
                "status": result.status,
                "result": result.result if result.ready() else None,
            }
        )

    async def handle_subscribe_task(self, content: dict[str, Any]) -> None:
        """Subscribe to updates for a specific task."""
        task_id = content.get("task_id")
        if task_id:
            task_group = f"task_{task_id}"
            await self.channel_layer.group_add(task_group, self.channel_name)
            await self.send_json(
                {
                    "type": "subscribed",
                    "task_id": task_id,
                }
            )

    async def task_update(self, event: dict[str, Any]) -> None:
        """Handle task update messages."""
        await self.send_json(event)
