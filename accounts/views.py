"""
accounts/views.py

Handles user registration, login, logout, and profile management.
All views use named URL redirects — no hard-coded paths.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required

from .forms import RegisterForm, StyledAuthenticationForm, ProfileForm


def register(request):
    """
    Display the registration form (GET) or create a new user account (POST).
    Automatically logs in the user upon successful registration.
    """
    if request.user.is_authenticated:
        return redirect("tasks:dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect("tasks:dashboard")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    """
    Display the login form (GET) or authenticate the user (POST).
    Redirects to 'next' parameter if present (standard Django behavior).
    """
    if request.user.is_authenticated:
        return redirect("tasks:dashboard")

    if request.method == "POST":
        form = StyledAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            # Honor the ?next= redirect parameter set by @login_required
            next_url = request.GET.get("next") or request.POST.get("next")
            return redirect(next_url or "tasks:dashboard")
    else:
        form = StyledAuthenticationForm(request)

    return render(request, "accounts/login.html", {
        "form": form,
        "next": request.GET.get("next", ""),
    })


def logout_view(request):
    """Log out the current user (POST only to prevent CSRF logout attacks)."""
    if request.method == "POST":
        logout(request)
        messages.info(request, "You have been logged out successfully.")
    return redirect("accounts:login")


@login_required
def profile(request):
    """
    Display (GET) or update (POST) the user's profile information.
    """
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "accounts/profile.html", {"form": form})
