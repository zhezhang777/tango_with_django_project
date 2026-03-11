"""
tasks/urls.py

All task and dashboard related URL patterns.
Uses named URLs so templates never hard-code paths.
"""

from django.urls import path
from . import views

app_name = "tasks"

urlpatterns = [
    # Dashboard — landing page after login
    path("", views.dashboard, name="dashboard"),

    # Task CRUD
    path("tasks/", views.task_list, name="task_list"),
    path("tasks/create/", views.task_create, name="task_create"),
    path("tasks/<int:pk>/", views.task_detail, name="task_detail"),
    path("tasks/<int:pk>/edit/", views.task_edit, name="task_edit"),
    path("tasks/<int:pk>/delete/", views.task_delete, name="task_delete"),

    # AJAX endpoints
    path("tasks/<int:pk>/toggle/", views.task_toggle_status, name="task_toggle"),

    # Course management
    path("courses/", views.course_list, name="course_list"),
    path("courses/create/", views.course_create, name="course_create"),
    path("courses/<int:pk>/edit/", views.course_edit, name="course_edit"),
    path("courses/<int:pk>/delete/", views.course_delete, name="course_delete"),
]
