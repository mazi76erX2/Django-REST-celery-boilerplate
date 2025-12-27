from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AnalysisViewSet, TaskStatusViewSet

router = DefaultRouter()
router.register(r"analyses", AnalysisViewSet, basename="analyses")
router.register(r"tasks", TaskStatusViewSet, basename="tasks")

urlpatterns = [
    path("", include(router.urls)),
]
