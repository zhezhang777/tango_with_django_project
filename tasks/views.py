"""
tasks/views.py

All views for the tasks app: dashboard, task CRUD, course CRUD,
and an AJAX endpoint for toggling task status.
Every view is protected by @login_required and scoped to request.user
so users can only see and modify their own data.
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q

from .models import Task, Course
from .forms import TaskForm, CourseForm


# ─────────────────────────────────────────────
#  Dashboard
# ─────────────────────────────────────────────

@login_required
def dashboard(request):
    """
    Landing page after login.
    Shows task statistics, upcoming deadlines, and a quick progress overview.
    """
    user_tasks = Task.objects.filter(user=request.user)
    now = timezone.now()
    today_end = now.replace(hour=23, minute=59, second=59)
    week_end = now + timezone.timedelta(days=7)

    stats = {
        "total":       user_tasks.count(),
        "done":        user_tasks.filter(status=Task.Status.DONE).count(),
        "in_progress": user_tasks.filter(status=Task.Status.IN_PROGRESS).count(),
        "overdue":     user_tasks.filter(due_date__lt=now).exclude(status=Task.Status.DONE).count(),
    }
    stats["pending"] = stats["total"] - stats["done"] - stats["in_progress"]
    stats["completion_pct"] = (
        round(stats["done"] / stats["total"] * 100) if stats["total"] else 0
    )

    # Tasks due within the next 7 days, not yet done
    upcoming = (
        user_tasks
        .filter(due_date__gte=now, due_date__lte=week_end)
        .exclude(status=Task.Status.DONE)
        .order_by("due_date")[:5]
    )

    # Overdue tasks
    overdue = (
        user_tasks
        .filter(due_date__lt=now)
        .exclude(status=Task.Status.DONE)
        .order_by("due_date")[:5]
    )

    return render(request, "tasks/dashboard.html", {
        "stats": stats,
        "upcoming": upcoming,
        "overdue": overdue,
    })


# ─────────────────────────────────────────────
#  Task list (with filter + search)
# ─────────────────────────────────────────────

@login_required
def task_list(request):
    """
    Displays the user's tasks with optional filtering by course, priority,
    status, and a text search across title/description.
    Also groups tasks into Today / This Week / All.
    """
    tasks = Task.objects.filter(user=request.user).select_related("course")
    courses = Course.objects.filter(user=request.user)
    now = timezone.now()

    # ── Filters from GET params ──
    q          = request.GET.get("q", "").strip()
    f_course   = request.GET.get("course", "")
    f_priority = request.GET.get("priority", "")
    f_status   = request.GET.get("status", "")
    f_group    = request.GET.get("group", "all")   # today | week | all
    f_sort     = request.GET.get("sort", "due_date")

    if q:
        tasks = tasks.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if f_course:
        tasks = tasks.filter(course_id=f_course)
    if f_priority:
        tasks = tasks.filter(priority=f_priority)
    if f_status:
        tasks = tasks.filter(status=f_status)

    # Date grouping
    if f_group == "today":
        tasks = tasks.filter(due_date__date=now.date())
    elif f_group == "week":
        tasks = tasks.filter(due_date__date__gte=now.date(),
                             due_date__date__lte=(now + timezone.timedelta(days=7)).date())

    # Sorting
    sort_map = {
        "due_date":  "due_date",
        "-due_date": "-due_date",
        "priority":  "-priority",
        "title":     "title",
    }
    tasks = tasks.order_by(sort_map.get(f_sort, "due_date"))

    return render(request, "tasks/task_list.html", {
        "tasks": tasks,
        "courses": courses,
        "priority_choices": Task.Priority.choices,
        "status_choices": Task.Status.choices,
        # pass active filter values back to template for UI state
        "filters": {
            "q": q, "course": f_course, "priority": f_priority,
            "status": f_status, "group": f_group, "sort": f_sort,
        },
        "now": now,
    })


# ─────────────────────────────────────────────
#  Task CRUD
# ─────────────────────────────────────────────

@login_required
def task_create(request):
    """Create a new task belonging to the current user."""
    if request.method == "POST":
        form = TaskForm(request.user, request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, f'Task "{task.title}" created successfully.')
            return redirect("tasks:task_list")
    else:
        # Pre-select course if passed via query string (e.g., from course page)
        initial = {}
        if cid := request.GET.get("course"):
            initial["course"] = cid
        form = TaskForm(request.user, initial=initial)

    return render(request, "tasks/task_form.html", {
        "form": form,
        "form_title": "New Task",
        "submit_label": "Create Task",
    })


@login_required
def task_detail(request, pk):
    """Show full details of a single task."""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    return render(request, "tasks/task_detail.html", {"task": task})


@login_required
def task_edit(request, pk):
    """Edit an existing task."""
    task = get_object_or_404(Task, pk=pk, user=request.user)

    if request.method == "POST":
        form = TaskForm(request.user, request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.title}" updated.')
            return redirect("tasks:task_detail", pk=task.pk)
    else:
        form = TaskForm(request.user, instance=task)

    return render(request, "tasks/task_form.html", {
        "form": form,
        "task": task,
        "form_title": "Edit Task",
        "submit_label": "Save Changes",
    })


@login_required
def task_delete(request, pk):
    """Delete a task after confirmation (POST only)."""
    task = get_object_or_404(Task, pk=pk, user=request.user)

    if request.method == "POST":
        title = task.title
        task.delete()
        messages.success(request, f'Task "{title}" deleted.')
        return redirect("tasks:task_list")

    return render(request, "tasks/task_confirm_delete.html", {"task": task})


@login_required
def task_toggle_status(request, pk):
    """
    AJAX endpoint — cycles through todo → in_progress → done → todo.
    Returns JSON with the new status so the UI can update without a page reload.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed."}, status=405)

    task = get_object_or_404(Task, pk=pk, user=request.user)

    cycle = {
        Task.Status.TODO:        Task.Status.DONE,
        Task.Status.IN_PROGRESS: Task.Status.DONE,
        Task.Status.DONE:        Task.Status.TODO,
    }
    task.status = cycle.get(task.status, Task.Status.TODO)
    task.save(update_fields=["status", "updated_at"])

    return JsonResponse({
        "status":       task.status,
        "status_label": task.get_status_display(),
        "is_done":      task.is_done,
    })


# ─────────────────────────────────────────────
#  Course CRUD
# ─────────────────────────────────────────────

@login_required
def course_list(request):
    """List all courses for the current user with task counts."""
    courses = (
        Course.objects.filter(user=request.user)
        .annotate(
            task_count=Count("tasks"),
            done_count=Count("tasks", filter=Q(tasks__status=Task.Status.DONE)),
        )
    )
    return render(request, "tasks/course_list.html", {"courses": courses})


@login_required
def course_create(request):
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.user = request.user
            course.save()
            messages.success(request, f'Course "{course.name}" added.')
            return redirect("tasks:course_list")
    else:
        form = CourseForm()

    return render(request, "tasks/course_form.html", {
        "form": form,
        "form_title": "Add Course",
        "submit_label": "Add Course",
    })


@login_required
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk, user=request.user)

    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Course "{course.name}" updated.')
            return redirect("tasks:course_list")
    else:
        form = CourseForm(instance=course)

    return render(request, "tasks/course_form.html", {
        "form": form,
        "course": course,
        "form_title": "Edit Course",
        "submit_label": "Save Changes",
    })


@login_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk, user=request.user)

    if request.method == "POST":
        name = course.name
        course.delete()
        messages.success(request, f'Course "{name}" deleted.')
        return redirect("tasks:course_list")

    return render(request, "tasks/course_confirm_delete.html", {"course": course})
