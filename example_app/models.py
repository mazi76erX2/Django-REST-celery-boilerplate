from django.db import models


class Analysis(models.Model):
    """
    Stores the results of text sentiment analysis.

    Fields:
        text (str): The analyzed text content.
        sentiment (SentimentChoices): The overall sentiment of the text.
        confidence_score (float, optional): The confidence score associated
            with the sentiment prediction (between 0.0 and 1.0).
        status (StatusChoices): The current status of the analysis.
        task_id (str, optional): The Celery task ID for tracking.
        created_at (datetime.datetime): The timestamp when the analysis was
            created (automatically set on creation).
        updated_at (datetime.datetime): The timestamp when the analysis was
            last updated.
    """

    class SentimentChoices(models.TextChoices):
        POSITIVE = "positive"
        NEGATIVE = "negative"
        NEUTRAL = "neutral"

    class StatusChoices(models.TextChoices):
        PENDING = "pending"
        PROCESSING = "processing"
        COMPLETED = "completed"
        FAILED = "failed"

    text = models.TextField(blank=False, null=False)
    sentiment = models.CharField(
        choices=SentimentChoices.choices,
        max_length=8,
        blank=True,
        null=True,
    )
    confidence_score = models.FloatField(blank=True, null=True)
    status = models.CharField(
        choices=StatusChoices.choices,
        max_length=10,
        default=StatusChoices.PENDING,
    )
    task_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Analysis"
        verbose_name_plural = "Analyses"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.text[:20]}... ({self.status})" if self.text else ""
