"""
Tests for the REST API views.
"""

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from example_app.models import Analysis


class AnalysisViewSetTest(APITestCase):
    """Tests for the AnalysisViewSet."""

    def setUp(self):
        self.list_url = reverse("analyses-list")
        self.bulk_url = reverse("analyses-bulk")

    def test_create_analysis_missing_text(self):
        """Test creating analysis without text field."""
        response = self.client.post(self.list_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_create_analysis_async(self):
        """Test creating analysis in async mode."""
        response = self.client.post(
            self.list_url,
            {"text": "This is a test text", "async_mode": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("task_id", response.data)
        self.assertEqual(response.data["status"], "pending")

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_create_analysis_sync(self):
        """Test creating analysis in sync mode."""
        response = self.client.post(
            self.list_url,
            {"text": "This is a test text", "async_mode": False},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("sentiment", response.data)
        self.assertEqual(response.data["status"], "completed")

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_bulk_analysis(self):
        """Test bulk analysis endpoint."""
        texts = ["Text one", "Text two", "Text three"]
        response = self.client.post(
            self.bulk_url,
            {"texts": texts},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("task_id", response.data)
        self.assertEqual(response.data["total"], 3)

    def test_bulk_analysis_empty_texts(self):
        """Test bulk analysis with empty texts list."""
        response = self.client.post(
            self.bulk_url,
            {"texts": []},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_analyses(self):
        """Test listing analyses."""
        Analysis.objects.create(text="Test 1", status="completed")
        Analysis.objects.create(text="Test 2", status="completed")

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_analysis(self):
        """Test retrieving a specific analysis."""
        analysis = Analysis.objects.create(
            text="Test text",
            sentiment="positive",
            confidence_score=0.95,
            status="completed",
        )

        url = reverse("analyses-detail", kwargs={"pk": analysis.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["text"], "Test text")
        self.assertEqual(response.data["sentiment"], "positive")

    def test_retrieve_analysis_not_found(self):
        """Test retrieving non-existent analysis."""
        url = reverse("analyses-detail", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_analysis_status(self):
        """Test getting analysis status."""
        analysis = Analysis.objects.create(
            text="Test text",
            status="processing",
            task_id="test-task-id",
        )

        url = reverse("analyses-status", kwargs={"pk": analysis.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "processing")
        self.assertEqual(response.data["task_id"], "test-task-id")


class TaskStatusViewSetTest(APITestCase):
    """Tests for the TaskStatusViewSet."""

    def test_retrieve_task_status(self):
        """Test retrieving task status."""
        url = reverse("tasks-detail", kwargs={"pk": "test-task-id"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("status", response.data)
        self.assertEqual(response.data["task_id"], "test-task-id")

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_health_check(self):
        """Test Celery health check endpoint."""
        url = reverse("tasks-health")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["celery_status"], "healthy")
