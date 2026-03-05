"""
Tests for Celery tasks.
"""

from django.test import TestCase, override_settings

from example_app.models import Analysis
from example_app.tasks import (
    _perform_sentiment_analysis,
    analyse_sentiment_task,
    bulk_analyse_sentiment_task,
    cleanup_old_analyses,
    health_check_task,
)


class SentimentAnalysisTaskTest(TestCase):
    """Tests for the sentiment analysis Celery task."""

    def test_perform_sentiment_analysis_returns_valid_result(self):
        """Test that _perform_sentiment_analysis returns valid sentiment data."""
        text = "This is a test text"
        result = _perform_sentiment_analysis(text)

        assert "sentiment" in result
        assert "confidence_score" in result
        assert result["sentiment"] in ["positive", "neutral", "negative"]
        assert 0.0 <= result["confidence_score"] <= 1.0

    def test_perform_sentiment_analysis_deterministic(self):
        """Test that same text produces same result (deterministic)."""
        text = "This is a test text"
        result1 = _perform_sentiment_analysis(text)
        result2 = _perform_sentiment_analysis(text)

        assert result1 == result2

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_analyse_sentiment_task_creates_result(self):
        """Test that analyse_sentiment_task processes and saves results."""
        analysis = Analysis.objects.create(
            text="Test text for analysis",
            status="pending",
        )

        analyse_sentiment_task(
            text=analysis.text,
            analysis_id=analysis.id,
        )

        analysis.refresh_from_db()
        assert analysis.status == "completed"
        assert analysis.sentiment is not None
        assert analysis.confidence_score is not None

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_analyse_sentiment_task_without_analysis_id(self):
        """Test that task works without an analysis_id."""
        result = analyse_sentiment_task(text="Test text")

        assert "sentiment" in result
        assert "confidence_score" in result

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_bulk_analyse_sentiment_task(self):
        """Test bulk sentiment analysis task."""
        texts = ["Text one", "Text two", "Text three"]

        results = bulk_analyse_sentiment_task(texts=texts)

        assert len(results) == 3
        for result in results:
            assert result["status"] == "completed"
            assert "sentiment" in result
            assert "confidence_score" in result

        # Verify Analysis objects were created
        assert Analysis.objects.count() == 3


class CleanupTaskTest(TestCase):
    """Tests for the cleanup task."""

    def test_cleanup_old_analyses(self):
        """Test that old analyses are cleaned up."""
        from datetime import timedelta

        from django.utils import timezone

        # Create old analysis
        old_analysis = Analysis.objects.create(
            text="Old analysis",
            status="completed",
        )
        # Manually set created_at to 31 days ago
        Analysis.objects.filter(id=old_analysis.id).update(
            created_at=timezone.now() - timedelta(days=31)
        )

        # Create recent analysis
        recent_analysis = Analysis.objects.create(
            text="Recent analysis",
            status="completed",
        )

        result = cleanup_old_analyses(days=30)

        assert result["deleted_count"] == 1
        assert Analysis.objects.count() == 1
        assert Analysis.objects.first().id == recent_analysis.id


class HealthCheckTaskTest(TestCase):
    """Tests for the health check task."""

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_health_check_task(self):
        """Test that health check task returns healthy status."""
        result = health_check_task()

        assert result["status"] == "healthy"
        assert "message" in result
