from django.contrib import admin
from .models import Course, Task


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "user", "created_at"]
    list_filter = ["user"]
    search_fields = ["name", "code"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "course", "priority", "status", "due_date", "is_overdue"]
    list_filter = ["status", "priority", "course"]
    search_fields = ["title", "description"]
    readonly_fields = ["created_at", "updated_at"]
