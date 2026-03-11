"""
tasks/forms.py

Forms for creating/editing tasks and courses.
All widgets are styled with Bootstrap classes.
"""

from django import forms
from .models import Task, Course


class TaskForm(forms.ModelForm):
    """Form for creating and editing a study task."""

    class Meta:
        model = Task
        fields = ("title", "course", "description", "priority", "status", "due_date")
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Write Chapter 3 essay",
                "autofocus": True,
            }),
            "course": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Add any notes or details about this task…",
            }),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            # datetime-local input for a clean browser date/time picker
            "due_date": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show courses that belong to the current user
        self.fields["course"].queryset = Course.objects.filter(user=user)
        self.fields["course"].empty_label = "— No course —"
        self.fields["due_date"].required = False

        # Pre-fill datetime-local value in the correct format when editing
        if self.instance and self.instance.pk and self.instance.due_date:
            self.initial["due_date"] = self.instance.due_date.strftime("%Y-%m-%dT%H:%M")


class CourseForm(forms.ModelForm):
    """Form for creating and editing a course."""

    class Meta:
        model = Course
        fields = ("name", "code", "color")
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Introduction to Psychology",
                "autofocus": True,
            }),
            "code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. PSY101 (optional)",
            }),
            "color": forms.TextInput(attrs={
                "class": "form-control form-control-color",
                "type": "color",
                "title": "Pick a label colour for this course",
            }),
        }
