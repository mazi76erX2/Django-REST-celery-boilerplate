from rest_framework import serializers

from .models import Analysis


class AnalysisSerializer(serializers.ModelSerializer):
    """
    Serializer class for the Analysis model.
    """

    class Meta:
        model = Analysis
        fields = [
            "id",
            "text",
            "sentiment",
            "confidence_score",
            "status",
            "task_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "sentiment",
            "confidence_score",
            "status",
            "task_id",
            "created_at",
            "updated_at",
        ]


class AnalysisCreateSerializer(serializers.Serializer):
    """
    Serializer for creating new analysis requests.
    """

    text = serializers.CharField(required=True, max_length=10000)
    async_mode = serializers.BooleanField(default=True)


class BulkAnalysisCreateSerializer(serializers.Serializer):
    """
    Serializer for bulk analysis requests.
    """

    texts = serializers.ListField(
        child=serializers.CharField(max_length=10000),
        min_length=1,
        max_length=100,
    )
    async_mode = serializers.BooleanField(default=True)


class TaskStatusSerializer(serializers.Serializer):
    """
    Serializer for task status responses.
    """

    task_id = serializers.CharField()
    status = serializers.CharField()
    result = serializers.DictField(required=False, allow_null=True)
