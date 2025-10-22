from django.urls import path
from .views import CleanupApi

urlpatterns = [
    path('internal/cleanup/v1', CleanupApi.as_view(), name='internal.cleanup'),
]

