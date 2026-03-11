"""
studyplanner/urls.py

Root URL configuration. All app-level routes are delegated to their
own urls.py via include(), and all URLs are named to avoid hard-coding.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    # Delegate authentication routes to the accounts app
    path("accounts/", include("accounts.urls", namespace="accounts")),
    # Delegate task-related routes to the tasks app (root path)
    path("", include("tasks.urls", namespace="tasks")),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
