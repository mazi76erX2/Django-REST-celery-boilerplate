"""
Celery tasks for the example app.

This module contains all asynchronous tasks that can be executed
by Celery workers.
"""

import logging
from datetime import timedelta
from typing import Any

from celery import shared_task
from channels.layers import get_channel_layer
from django.utils import timezone

from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def analyse_sentiment_task(
    self,
    text: str,
    analysis_id: int | None = None,
    channel_name: str | None = None,
    group_name: str | None = None,
) -> dict[str, Any]:
    """
    Celery task to analyze sentiment of a given text.

    Args:
        self: Task instance (bound task).
        text: The text to analyze.
        analysis_id: Optional ID of the Analysis object to update.
        channel_name: Optional WebSocket channel to send results to.
        group_name: Optional WebSocket group to broadcast results to.

    Returns:
        Dictionary containing sentiment analysis results.
    """
    from example_app.models import Analysis

    try:
        logger.info(f"Starting sentiment analysis for text: {text[:50]}...")

        # Simulate sentiment analysis (replace with actual ML model)
        # In production, you would load your model here
        sentiment_result = _perform_sentiment_analysis(text)

        # Update the Analysis object if ID is provided
        if analysis_id:
            try:
                analysis = Analysis.objects.get(id=analysis_id)
                analysis.sentiment = sentiment_result["sentiment"]
                analysis.confidence_score = sentiment_result["confidence_score"]
                analysis.status = "completed"
                analysis.save()
                logger.info(f"Updated Analysis {analysis_id} with results")
            except Analysis.DoesNotExist:
                logger.error(f"Analysis {analysis_id} not found")

        # Send result via WebSocket if channel/group is provided
        if channel_name or group_name:
            _send_websocket_notification(
                sentiment_result, analysis_id, channel_name, group_name
            )

        logger.info(f"Completed sentiment analysis: {sentiment_result}")
        return sentiment_result

    except Exception as exc:
        logger.error(f"Error in sentiment analysis task: {exc}")
        # Update status to failed if we have an analysis_id
        if analysis_id:
            try:
                Analysis.objects.filter(id=analysis_id).update(status="failed")
            except Exception:
                pass
        # Retry the task
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def bulk_analyse_sentiment_task(
    self,
    texts: list[str],
    group_name: str | None = None,
) -> list[dict[str, Any]]:
    """
    Celery task to analyze sentiment for multiple texts.

    Args:
        self: Task instance (bound task).
        texts: List of texts to analyze.
        group_name: Optional WebSocket group to broadcast progress to.

    Returns:
        List of sentiment analysis results.
    """
    from example_app.models import Analysis

    results = []
    total = len(texts)

    for index, text in enumerate(texts, 1):
        try:
            # Create Analysis object with pending status
            analysis = Analysis.objects.create(
                text=text,
                status="processing",
            )

            # Perform analysis
            sentiment_result = _perform_sentiment_analysis(text)

            # Update Analysis object
            analysis.sentiment = sentiment_result["sentiment"]
            analysis.confidence_score = sentiment_result["confidence_score"]
            analysis.status = "completed"
            analysis.save()

            result = {
                "id": analysis.id,
                "text": text,
                **sentiment_result,
                "status": "completed",
            }
            results.append(result)

            # Send progress update via WebSocket
            if group_name:
                _send_progress_update(group_name, index, total, result)

        except Exception as exc:
            logger.error(f"Error analyzing text '{text[:50]}...': {exc}")
            results.append(
                {
                    "text": text,
                    "error": str(exc),
                    "status": "failed",
                }
            )

    # Send completion notification
    if group_name:
        _send_completion_notification(group_name, results)

    return results


@shared_task
def cleanup_old_analyses(days: int = 30) -> dict[str, int]:
    """
    Periodic task to clean up old analysis records.

    Args:
        days: Number of days to keep analyses.

    Returns:
        Dictionary with count of deleted records.
    """
    from example_app.models import Analysis

    cutoff_date = timezone.now() - timedelta(days=days)
    deleted_count, _ = Analysis.objects.filter(created_at__lt=cutoff_date).delete()

    logger.info(f"Cleaned up {deleted_count} analyses older than {days} days")
    return {"deleted_count": deleted_count}


@shared_task
def health_check_task() -> dict[str, str]:
    """
    Simple health check task to verify Celery is working.

    Returns:
        Dictionary with status message.
    """
    return {"status": "healthy", "message": "Celery is working!"}


def _perform_sentiment_analysis(text: str) -> dict[str, Any]:
    """
    Perform actual sentiment analysis on the text.

    This is a placeholder implementation. In production, you would:
    1. Load your ML model (e.g., transformers, tensorflow)
    2. Preprocess the text
    3. Run inference
    4. Return results

    Args:
        text: Text to analyze.

    Returns:
        Dictionary with sentiment and confidence_score.
    """
    # Placeholder implementation - replace with actual ML model
    import hashlib
    import random

    # Use hash for deterministic "fake" results in development
    text_hash = int(hashlib.md5(text.encode()).hexdigest(), 16)
    random.seed(text_hash)

    sentiments = ["positive", "neutral", "negative"]
    sentiment = random.choice(sentiments)
    confidence = round(random.uniform(0.6, 0.99), 4)

    return {
        "sentiment": sentiment,
        "confidence_score": confidence,
    }


def _send_websocket_notification(
    result: dict[str, Any],
    analysis_id: int | None,
    channel_name: str | None,
    group_name: str | None,
) -> None:
    """Send analysis result via WebSocket."""
    channel_layer = get_channel_layer()

    message = {
        "type": "analysis_complete",
        "data": {
            "analysis_id": analysis_id,
            **result,
        },
    }

    if channel_name:
        async_to_sync(channel_layer.send)(channel_name, message)

    if group_name:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "analysis.complete",
                "data": message["data"],
            },
        )


def _send_progress_update(
    group_name: str, current: int, total: int, result: dict[str, Any]
) -> None:
    """Send progress update via WebSocket."""
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "analysis.progress",
            "data": {
                "current": current,
                "total": total,
                "progress_percent": round((current / total) * 100, 1),
                "latest_result": result,
            },
        },
    )


def _send_completion_notification(
    group_name: str, results: list[dict[str, Any]]
) -> None:
    """Send completion notification via WebSocket."""
    channel_layer = get_channel_layer()

    successful = sum(1 for r in results if r.get("status") == "completed")
    failed = sum(1 for r in results if r.get("status") == "failed")

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "analysis.bulk_complete",
            "data": {
                "total": len(results),
                "successful": successful,
                "failed": failed,
                "results": results,
            },
        },
    )
