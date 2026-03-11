"""
accounts/tests.py

Unit tests for the accounts app: RegisterForm, ProfileForm validation.

Run with:
    python manage.py test accounts --verbosity=2
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from .forms import RegisterForm, ProfileForm


class RegisterFormTest(TestCase):
    """Form-level validation tests for RegisterForm."""

    def _valid_data(self, **overrides):
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password1": "securepass99!",
            "password2": "securepass99!",
        }
        data.update(overrides)
        return data

    def test_valid_form_is_valid(self):
        form = RegisterForm(self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_mismatched_passwords_invalid(self):
        form = RegisterForm(self._valid_data(password2="different99!"))
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_duplicate_email_invalid(self):
        User.objects.create_user(username="other", email="test@example.com", password="pass")
        form = RegisterForm(self._valid_data())
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_blank_username_invalid(self):
        form = RegisterForm(self._valid_data(username=""))
        self.assertFalse(form.is_valid())

    def test_invalid_email_invalid(self):
        form = RegisterForm(self._valid_data(email="not-an-email"))
        self.assertFalse(form.is_valid())


class ProfileFormTest(TestCase):
    """Form-level validation tests for ProfileForm."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="pass"
        )

    def test_valid_profile_update(self):
        form = ProfileForm(
            {"first_name": "Alice", "last_name": "Smith", "email": "alice@example.com"},
            instance=self.user,
        )
        self.assertTrue(form.is_valid())

    def test_email_conflict_with_other_user(self):
        User.objects.create_user(username="bob", email="bob@example.com", password="pass")
        form = ProfileForm(
            {"first_name": "", "last_name": "", "email": "bob@example.com"},
            instance=self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_user_can_keep_own_email(self):
        """No conflict when the user submits their own existing email."""
        form = ProfileForm(
            {"first_name": "Alice", "last_name": "", "email": "alice@example.com"},
            instance=self.user,
        )
        self.assertTrue(form.is_valid())


class ProfileViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="testpass123"
        )
        self.client.force_login(self.user)

    def test_profile_page_loads(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Profile")

    def test_profile_update_saves_name(self):
        self.client.post(reverse("accounts:profile"), {
            "first_name": "Alice",
            "last_name": "Wonderland",
            "email": "alice@example.com",
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Alice")
        self.assertEqual(self.user.last_name, "Wonderland")

    def test_profile_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response["Location"])
