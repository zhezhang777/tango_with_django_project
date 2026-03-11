"""
tasks/tests.py

Unit and integration tests for the tasks app.

Coverage:
  Models  — Course, Task (properties, ordering, constraints)
  Views   — dashboard, task list/create/edit/delete, toggle (AJAX),
            course list/create, access-control isolation

Run with:
    python manage.py test tasks --verbosity=2
"""

import json
from datetime import timedelta

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from .models import Course, Task


# ═══════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════

def make_user(username="alice", password="testpass123"):
    return User.objects.create_user(username=username, password=password)


def make_course(user, name="Maths", color="#4f46e5"):
    return Course.objects.create(user=user, name=name, color=color)


def make_task(user, title="Homework", course=None, status=Task.Status.TODO,
              priority=Task.Priority.MEDIUM, due_date=None):
    return Task.objects.create(
        user=user, title=title, course=course,
        status=status, priority=priority, due_date=due_date,
    )


# ═══════════════════════════════════════════════════════════════
#  Model Tests
# ═══════════════════════════════════════════════════════════════

class CourseModelTest(TestCase):
    """Tests for the Course model."""

    def setUp(self):
        self.user = make_user()

    def test_str_with_code(self):
        """__str__ should include both code and name when code is set."""
        course = Course.objects.create(user=self.user, name="Physics", code="PHY101")
        self.assertEqual(str(course), "PHY101 Physics")

    def test_str_without_code(self):
        """__str__ should return only name when no code is provided."""
        course = Course.objects.create(user=self.user, name="History")
        self.assertEqual(str(course).strip(), "History")

    def test_default_color(self):
        """Course should default to the indigo brand colour."""
        course = Course.objects.create(user=self.user, name="Art")
        self.assertEqual(course.color, "#4f46e5")

    def test_ordering_is_by_name(self):
        """Courses should be ordered alphabetically by name."""
        Course.objects.create(user=self.user, name="Zoology")
        Course.objects.create(user=self.user, name="Algebra")
        Course.objects.create(user=self.user, name="Marketing")
        names = list(Course.objects.filter(user=self.user).values_list("name", flat=True))
        self.assertEqual(names, sorted(names))

    def test_cascade_delete_with_user(self):
        """Deleting a user should cascade-delete all their courses."""
        Course.objects.create(user=self.user, name="Biology")
        self.user.delete()
        self.assertEqual(Course.objects.count(), 0)


class TaskModelTest(TestCase):
    """Tests for the Task model properties and behaviour."""

    def setUp(self):
        self.user = make_user()
        self.course = make_course(self.user)

    # ── Basic creation ──────────────────────────────────────────

    def test_task_str(self):
        task = make_task(self.user, title="Write essay")
        self.assertEqual(str(task), "Write essay")

    def test_default_status_is_todo(self):
        task = make_task(self.user)
        self.assertEqual(task.status, Task.Status.TODO)

    def test_default_priority_is_medium(self):
        task = make_task(self.user)
        self.assertEqual(task.priority, Task.Priority.MEDIUM)

    def test_task_can_have_course(self):
        task = make_task(self.user, course=self.course)
        self.assertEqual(task.course, self.course)

    def test_task_can_be_courseless(self):
        task = make_task(self.user, course=None)
        self.assertIsNone(task.course)

    def test_course_set_null_on_course_delete(self):
        """Deleting a course should set task.course to NULL (not delete the task)."""
        task = make_task(self.user, course=self.course)
        self.course.delete()
        task.refresh_from_db()
        self.assertIsNone(task.course)

    # ── is_done property ────────────────────────────────────────

    def test_is_done_true_when_status_done(self):
        task = make_task(self.user, status=Task.Status.DONE)
        self.assertTrue(task.is_done)

    def test_is_done_false_when_todo(self):
        task = make_task(self.user, status=Task.Status.TODO)
        self.assertFalse(task.is_done)

    def test_is_done_false_when_in_progress(self):
        task = make_task(self.user, status=Task.Status.IN_PROGRESS)
        self.assertFalse(task.is_done)

    # ── is_overdue property ─────────────────────────────────────

    def test_is_overdue_past_due_todo(self):
        """A past-due TODO task should be overdue."""
        past = timezone.now() - timedelta(hours=1)
        task = make_task(self.user, status=Task.Status.TODO, due_date=past)
        self.assertTrue(task.is_overdue)

    def test_is_overdue_false_when_done(self):
        """A done task is never overdue even if the due date has passed."""
        past = timezone.now() - timedelta(days=5)
        task = make_task(self.user, status=Task.Status.DONE, due_date=past)
        self.assertFalse(task.is_overdue)

    def test_is_overdue_false_for_future_due_date(self):
        future = timezone.now() + timedelta(days=3)
        task = make_task(self.user, status=Task.Status.TODO, due_date=future)
        self.assertFalse(task.is_overdue)

    def test_is_overdue_false_when_no_due_date(self):
        task = make_task(self.user, due_date=None)
        self.assertFalse(task.is_overdue)

    # ── days_until_due property ─────────────────────────────────

    def test_days_until_due_positive_for_future(self):
        future = timezone.now() + timedelta(days=4)
        task = make_task(self.user, due_date=future)
        self.assertGreaterEqual(task.days_until_due, 3)

    def test_days_until_due_negative_for_past(self):
        past = timezone.now() - timedelta(days=2)
        task = make_task(self.user, due_date=past)
        self.assertLess(task.days_until_due, 0)

    def test_days_until_due_none_when_no_due_date(self):
        task = make_task(self.user, due_date=None)
        self.assertIsNone(task.days_until_due)

    # ── Ordering ────────────────────────────────────────────────

    def test_tasks_ordered_by_due_date_then_priority(self):
        """Default ordering: earliest due_date first, then highest priority."""
        soon  = timezone.now() + timedelta(days=1)
        later = timezone.now() + timedelta(days=5)
        t1 = make_task(self.user, title="Soon",  due_date=soon)
        t2 = make_task(self.user, title="Later", due_date=later)
        qs = list(Task.objects.filter(user=self.user))
        self.assertEqual(qs[0], t1)
        self.assertEqual(qs[1], t2)

    # ── User isolation ──────────────────────────────────────────

    def test_tasks_belong_to_their_user(self):
        other = make_user("bob")
        make_task(self.user, title="Alice task")
        make_task(other, title="Bob task")
        self.assertEqual(Task.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Task.objects.filter(user=other).count(), 1)


# ═══════════════════════════════════════════════════════════════
#  View Tests — Accounts
# ═══════════════════════════════════════════════════════════════

class RegisterViewTest(TestCase):

    def test_register_page_loads(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create your account")

    def test_register_creates_user_and_redirects(self):
        data = {
            "username": "newuser",
            "email": "new@test.com",
            "password1": "securepass99!",
            "password2": "securepass99!",
        }
        response = self.client.post(reverse("accounts:register"), data)
        self.assertRedirects(response, reverse("tasks:dashboard"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_with_mismatched_passwords_shows_error(self):
        data = {
            "username": "user2",
            "email": "u2@test.com",
            "password1": "securepass99!",
            "password2": "different99!",
        }
        response = self.client.post(reverse("accounts:register"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="user2").exists())

    def test_register_with_duplicate_email_shows_error(self):
        User.objects.create_user(username="existing", email="dup@test.com", password="pass")
        data = {
            "username": "newuser2",
            "email": "dup@test.com",
            "password1": "securepass99!",
            "password2": "securepass99!",
        }
        response = self.client.post(reverse("accounts:register"), data)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_redirected_from_register(self):
        user = make_user()
        self.client.force_login(user)
        response = self.client.get(reverse("accounts:register"))
        self.assertRedirects(response, reverse("tasks:dashboard"))


class LoginViewTest(TestCase):

    def setUp(self):
        self.user = make_user(username="alice", password="testpass123")

    def test_login_page_loads(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome back")

    def test_valid_login_redirects_to_dashboard(self):
        response = self.client.post(reverse("accounts:login"), {
            "username": "alice", "password": "testpass123",
        })
        self.assertRedirects(response, reverse("tasks:dashboard"))

    def test_invalid_password_shows_error(self):
        response = self.client.post(reverse("accounts:login"), {
            "username": "alice", "password": "wrongpass",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_authenticated_user_redirected_from_login(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:login"))
        self.assertRedirects(response, reverse("tasks:dashboard"))

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:logout"))
        # GET should NOT log out — user still authenticated
        self.assertEqual(response.wsgi_request.user.is_authenticated, True)

    def test_logout_post_logs_out_user(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))
        # Follow redirect and confirm user is no longer logged in
        response2 = self.client.get(reverse("tasks:dashboard"))
        self.assertRedirects(
            response2,
            reverse("accounts:login") + "?next=" + reverse("tasks:dashboard"),
        )


# ═══════════════════════════════════════════════════════════════
#  View Tests — Tasks
# ═══════════════════════════════════════════════════════════════

class DashboardViewTest(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_dashboard_redirects_anonymous_user(self):
        response = self.client.get(reverse("tasks:dashboard"))
        self.assertRedirects(
            response,
            reverse("accounts:login") + "?next=" + reverse("tasks:dashboard"),
        )

    def test_dashboard_loads_for_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("tasks:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")

    def test_dashboard_shows_correct_stats(self):
        self.client.force_login(self.user)
        make_task(self.user, title="Done task", status=Task.Status.DONE)
        make_task(self.user, title="Todo task", status=Task.Status.TODO)
        response = self.client.get(reverse("tasks:dashboard"))
        self.assertEqual(response.context["stats"]["total"], 2)
        self.assertEqual(response.context["stats"]["done"], 1)

    def test_dashboard_does_not_show_other_users_tasks(self):
        """Stats on the dashboard must only count the logged-in user's tasks."""
        other = make_user("bob")
        make_task(other, title="Bob's task")
        self.client.force_login(self.user)
        response = self.client.get(reverse("tasks:dashboard"))
        self.assertEqual(response.context["stats"]["total"], 0)


class TaskListViewTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_task_list_loads(self):
        response = self.client.get(reverse("tasks:task_list"))
        self.assertEqual(response.status_code, 200)

    def test_task_list_shows_only_own_tasks(self):
        other = make_user("bob")
        make_task(self.user, title="My task")
        make_task(other, title="Bob's task")
        response = self.client.get(reverse("tasks:task_list"))
        titles = [t.title for t in response.context["tasks"]]
        self.assertIn("My task", titles)
        self.assertNotIn("Bob's task", titles)

    def test_search_filter(self):
        make_task(self.user, title="Write report")
        make_task(self.user, title="Read textbook")
        response = self.client.get(reverse("tasks:task_list") + "?q=report")
        titles = [t.title for t in response.context["tasks"]]
        self.assertIn("Write report", titles)
        self.assertNotIn("Read textbook", titles)

    def test_status_filter(self):
        make_task(self.user, title="Done", status=Task.Status.DONE)
        make_task(self.user, title="Todo", status=Task.Status.TODO)
        response = self.client.get(reverse("tasks:task_list") + "?status=done")
        titles = [t.title for t in response.context["tasks"]]
        self.assertIn("Done", titles)
        self.assertNotIn("Todo", titles)

    def test_priority_filter(self):
        make_task(self.user, title="Urgent", priority=Task.Priority.URGENT)
        make_task(self.user, title="Low", priority=Task.Priority.LOW)
        response = self.client.get(
            reverse("tasks:task_list") + f"?priority={Task.Priority.URGENT}"
        )
        titles = [t.title for t in response.context["tasks"]]
        self.assertIn("Urgent", titles)
        self.assertNotIn("Low", titles)


class TaskCreateViewTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_create_page_loads(self):
        response = self.client.get(reverse("tasks:task_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New Task")

    def test_create_task_saves_and_redirects(self):
        response = self.client.post(reverse("tasks:task_create"), {
            "title": "Study for exam",
            "priority": Task.Priority.HIGH,
            "status": Task.Status.TODO,
        })
        self.assertRedirects(response, reverse("tasks:task_list"))
        self.assertTrue(Task.objects.filter(title="Study for exam", user=self.user).exists())

    def test_create_task_missing_title_shows_errors(self):
        response = self.client.post(reverse("tasks:task_create"), {
            "title": "",
            "priority": Task.Priority.MEDIUM,
            "status": Task.Status.TODO,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.filter(user=self.user).count(), 0)

    def test_anonymous_user_redirected_from_create(self):
        self.client.logout()
        response = self.client.get(reverse("tasks:task_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response["Location"])


class TaskEditDeleteViewTest(TestCase):

    def setUp(self):
        self.user  = make_user()
        self.other = make_user("bob")
        self.task  = make_task(self.user, title="Original title")
        self.client.force_login(self.user)

    def test_edit_page_loads(self):
        response = self.client.get(reverse("tasks:task_edit", args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)

    def test_edit_updates_task(self):
        self.client.post(reverse("tasks:task_edit", args=[self.task.pk]), {
            "title": "Updated title",
            "priority": Task.Priority.HIGH,
            "status": Task.Status.IN_PROGRESS,
        })
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Updated title")

    def test_cannot_edit_another_users_task(self):
        """Editing another user's task should return 404."""
        other_task = make_task(self.other, title="Bob's task")
        response = self.client.get(reverse("tasks:task_edit", args=[other_task.pk]))
        self.assertEqual(response.status_code, 404)

    def test_delete_removes_task(self):
        self.client.post(reverse("tasks:task_delete", args=[self.task.pk]))
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())

    def test_cannot_delete_another_users_task(self):
        other_task = make_task(self.other, title="Bob's task")
        response = self.client.post(reverse("tasks:task_delete", args=[other_task.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Task.objects.filter(pk=other_task.pk).exists())


class TaskToggleViewTest(TestCase):
    """Tests for the AJAX toggle endpoint."""

    def setUp(self):
        self.user = make_user()
        self.task = make_task(self.user, status=Task.Status.TODO)
        self.client.force_login(self.user)

    def test_toggle_todo_to_done(self):
        response = self.client.post(
            reverse("tasks:task_toggle", args=[self.task.pk]),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["is_done"])
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.DONE)

    def test_toggle_done_back_to_todo(self):
        self.task.status = Task.Status.DONE
        self.task.save()
        self.client.post(
            reverse("tasks:task_toggle", args=[self.task.pk]),
            content_type="application/json",
        )
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.TODO)

    def test_toggle_returns_json(self):
        response = self.client.post(
            reverse("tasks:task_toggle", args=[self.task.pk]),
            content_type="application/json",
        )
        self.assertEqual(response["Content-Type"], "application/json")
        data = json.loads(response.content)
        self.assertIn("status", data)
        self.assertIn("is_done", data)
        self.assertIn("status_label", data)

    def test_toggle_get_not_allowed(self):
        """Toggle endpoint must refuse GET requests."""
        response = self.client.get(reverse("tasks:task_toggle", args=[self.task.pk]))
        self.assertEqual(response.status_code, 405)

    def test_cannot_toggle_another_users_task(self):
        other = make_user("bob")
        other_task = make_task(other)
        response = self.client.post(
            reverse("tasks:task_toggle", args=[other_task.pk]),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)


# ═══════════════════════════════════════════════════════════════
#  View Tests — Courses
# ═══════════════════════════════════════════════════════════════

class CourseViewTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_course_list_loads(self):
        response = self.client.get(reverse("tasks:course_list"))
        self.assertEqual(response.status_code, 200)

    def test_create_course_saves_and_redirects(self):
        response = self.client.post(reverse("tasks:course_create"), {
            "name": "Calculus",
            "code": "MATH201",
            "color": "#4f46e5",
        })
        self.assertRedirects(response, reverse("tasks:course_list"))
        self.assertTrue(Course.objects.filter(name="Calculus", user=self.user).exists())

    def test_cannot_view_another_users_course(self):
        other = make_user("bob")
        course = make_course(other, name="Bob's course")
        response = self.client.get(reverse("tasks:course_edit", args=[course.pk]))
        self.assertEqual(response.status_code, 404)

    def test_course_task_count_annotation(self):
        course = make_course(self.user)
        make_task(self.user, course=course)
        make_task(self.user, course=course, status=Task.Status.DONE)
        response = self.client.get(reverse("tasks:course_list"))
        courses = list(response.context["courses"])
        self.assertEqual(courses[0].task_count, 2)
        self.assertEqual(courses[0].done_count, 1)
