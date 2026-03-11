"""
tasks/models.py

Core data models for the Study Planner application.
ER relationships:
  User (1) ──< Course (many)
  User (1) ──< Task (many)
  Course (1) ──< Task (many)
  Task (1) ──< Comment (many)   [optional, for future use]
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Course(models.Model):
    """Represents a university course a student is enrolled in."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="courses")
    name = models.CharField(max_length=100, verbose_name="Course name")
    code = models.CharField(max_length=20, blank=True, verbose_name="Course code")
    color = models.CharField(
        max_length=7,
        default="#4f46e5",
        verbose_name="Label colour",
        help_text="Hex colour code used to distinguish courses in the UI",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self):
        return f"{self.code} {self.name}".strip()


class Task(models.Model):
    """Represents a single study task or assignment."""

    class Priority(models.IntegerChoices):
        LOW = 1, "Low"
        MEDIUM = 2, "Medium"
        HIGH = 3, "High"
        URGENT = 4, "Urgent"

    class Status(models.TextChoices):
        TODO = "todo", "To Do"
        IN_PROGRESS = "in_progress", "In Progress"
        DONE = "done", "Done"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name="Course",
    )
    title = models.CharField(max_length=200, verbose_name="Title")
    description = models.TextField(blank=True, verbose_name="Description")
    priority = models.IntegerField(
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name="Priority",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
        verbose_name="Status",
    )
    due_date = models.DateTimeField(null=True, blank=True, verbose_name="Due date")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_date", "-priority"]
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

    def __str__(self):
        return self.title

    @property
    def is_done(self):
        return self.status == self.Status.DONE

    @property
    def is_overdue(self):
        """Returns True if the task is past due and not yet completed."""
        if self.due_date and not self.is_done:
            return timezone.now() > self.due_date
        return False

    @property
    def days_until_due(self):
        """Returns the number of days remaining until due date (negative if overdue)."""
        if self.due_date:
            delta = self.due_date - timezone.now()
            return delta.days
        return None
