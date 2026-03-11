"""
accounts/forms.py

Custom forms for user registration and profile editing.
Extends Django's built-in UserCreationForm for consistent validation.
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


class RegisterForm(UserCreationForm):
    """
    Extends UserCreationForm with an email field and styled Bootstrap widgets.
    Email is required here even though Django's User model marks it optional.
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "your@university.edu",
            "autocomplete": "email",
        }),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap classes and helpful placeholders to all fields
        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Choose a username",
            "autocomplete": "username",
            "autofocus": True,
        })
        self.fields["password1"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Create a password",
            "autocomplete": "new-password",
        })
        self.fields["password2"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Confirm your password",
            "autocomplete": "new-password",
        })
        # Remove verbose help texts for a cleaner UI
        self.fields["username"].help_text = "Letters, digits and @/./+/-/_ only."
        self.fields["password1"].help_text = "At least 8 characters."
        self.fields["password2"].help_text = ""

    def clean_email(self):
        """Ensure the email address is not already taken."""
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class StyledAuthenticationForm(AuthenticationForm):
    """Wraps Django's AuthenticationForm with Bootstrap widget classes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Username",
            "autocomplete": "username",
            "autofocus": True,
        })
        self.fields["password"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Password",
            "autocomplete": "current-password",
        })


class ProfileForm(forms.ModelForm):
    """Allows users to update their first name, last name, and email."""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        widgets = {
            "first_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "First name",
            }),
            "last_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Last name",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Email address",
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        # Allow keeping the same email; only check for conflicts with other accounts
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already in use by another account.")
        return email
