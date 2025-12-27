"""
Views for the example app.
"""

import logging
from typing import Optional

from celery.result import AsyncResult
from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from adrf.viewsets import ViewSet
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .models import Analysis
from .serializers import (
    AnalysisCreateSerializer,
    AnalysisSerializer,
    BulkAnalysisCreateSerializer,
    TaskStatusSerializer,
)
from .tasks import analyse_sentiment_task, bulk_analyse_sentiment_task

logger = logging.getLogger(__name__)


class AnalysisViewSet(ViewSet):
    """
    ViewSet for sentiment analysis operations.
    """

    queryset = Analysis.objects.all()
    serializer_class = AnalysisSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=AnalysisCreateSerializer,
        responses={
            201: AnalysisSerializer,
            202: openapi.Response(
                description="Analysis task queued",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "task_id": openapi.Schema(type=openapi.TYPE_STRING),
                        "status": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    async def create(self, request: Request) -> Response:
        """
        Create a new sentiment analysis.

        If async_mode is True (default), the analysis is queued as a Celery task.
        """
        serializer = AnalysisCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        text = serializer.validated_data["text"]
        async_mode = serializer.validated_data["async_mode"]

        # Check cache first
        cache_key = f"sentiment:{hash(text)}"
        cached_result = cache.get(cache_key)

        if cached_result:
            logger.info("Returning cached result for text")
            return Response(cached_result, status=status.HTTP_200_OK)

        # Create Analysis object
        analysis = await Analysis.objects.acreate(
            text=text,
            status="pending" if async_mode else "processing",
        )

        if async_mode:
            # Dispatch Celery task
            task = analyse_sentiment_task.delay(
                text=text,
                analysis_id=analysis.id,
            )

            analysis.task_id = task.id
            await analysis.asave()

            logger.info(f"Analysis {analysis.id} queued as task {task.id}")

            return Response(
                {
                    "id": analysis.id,
                    "task_id": task.id,
                    "status": "pending",
                    "message": "Analysis queued for processing",
                },
                status=status.HTTP_202_ACCEPTED,
            )
        else:
            # Synchronous execution
            from .tasks import _perform_sentiment_analysis

            result = _perform_sentiment_analysis(text)

            analysis.sentiment = result["sentiment"]
            analysis.confidence_score = result["confidence_score"]
            analysis.status = "completed"
            await analysis.asave()

            # Cache the result
            cache.set(cache_key, AnalysisSerializer(analysis).data, timeout=3600)

            return Response(
                AnalysisSerializer(analysis).data,
                status=status.HTTP_201_CREATED,
            )

    @swagger_auto_schema(
        request_body=BulkAnalysisCreateSerializer,
        responses={202: "Bulk analysis queued"},
    )
    @action(detail=False, methods=["post"])
    async def bulk(self, request: Request) -> Response:
        """
        Create bulk sentiment analysis.
        """
        serializer = BulkAnalysisCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        texts = serializer.validated_data["texts"]

        # Dispatch Celery task
        task = bulk_analyse_sentiment_task.delay(texts=texts)

        logger.info(f"Bulk analysis queued as task {task.id} for {len(texts)} texts")

        return Response(
            {
                "task_id": task.id,
                "total": len(texts),
                "status": "pending",
                "message": "Bulk analysis queued for processing",
            },
            status=status.HTTP_202_ACCEPTED,
        )

    async def list(self, request: Request) -> Response:
        """
        List all analyses.
        """
        analyses = [analysis async for analysis in Analysis.objects.all()[:100]]
        serializer = AnalysisSerializer(analyses, many=True)
        return Response(serializer.data)

    async def retrieve(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Retrieve a specific analysis.
        """
        try:
            analysis = await Analysis.objects.aget(pk=pk)
            serializer = AnalysisSerializer(analysis)
            return Response(serializer.data)
        except Analysis.DoesNotExist:
            return Response(
                {"error": "Analysis not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True, methods=["get"])
    async def status(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Get the status of a specific analysis.
        """
        try:
            analysis = await Analysis.objects.aget(pk=pk)

            response_data = {
                "id": analysis.id,
                "status": analysis.status,
                "task_id": analysis.task_id,
            }

            # If there's a task_id, also get Celery task status
            if analysis.task_id:
                task_result = AsyncResult(analysis.task_id)
                response_data["celery_status"] = task_result.status

            if analysis.status == "completed":
                response_data["sentiment"] = analysis.sentiment
                response_data["confidence_score"] = analysis.confidence_score

            return Response(response_data)

        except Analysis.DoesNotExist:
            return Response(
                {"error": "Analysis not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class TaskStatusViewSet(ViewSet):
    """
    ViewSet for checking Celery task status.
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        responses={200: TaskStatusSerializer},
    )
    def retrieve(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Get the status of a Celery task.
        """
        if not pk:
            return Response(
                {"error": "Task ID required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task_result = AsyncResult(pk)

        response_data = {
            "task_id": pk,
            "status": task_result.status,
            "result": None,
        }

        if task_result.ready():
            if task_result.successful():
                response_data["result"] = task_result.result
            else:
                response_data["error"] = str(task_result.result)

        return Response(response_data)

    @action(detail=True, methods=["post"])
    def revoke(self, request: Request, pk: Optional[str] = None) -> Response:
        """
        Revoke/cancel a Celery task.
        """
        if not pk:
            return Response(
                {"error": "Task ID required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task_result = AsyncResult(pk)
        task_result.revoke(terminate=True)

        return Response(
            {
                "task_id": pk,
                "status": "revoked",
                "message": "Task has been revoked",
            }
        )

    @action(detail=False, methods=["get"])
    def health(self, request: Request) -> Response:
        """
        Check Celery health by running a simple task.
        """
        from .tasks import health_check_task

        try:
            # Run health check task synchronously with timeout
            result = health_check_task.apply_async()
            task_result = result.get(timeout=10)

            return Response(
                {
                    "celery_status": "healthy",
                    "task_result": task_result,
                }
            )
        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return Response(
                {
                    "celery_status": "unhealthy",
                    "error": str(e),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
