# Study Planner

A web application for university students to create, manage, and track study tasks and assignments in one place.

Built with **Python / Django 4.2**, **Bootstrap 5**, and vanilla **JavaScript**.

---

## Features

- **User accounts** — register, log in/out, edit profile
- **Task management** — create, edit, delete, and filter tasks by course, priority, status, or due date
- **Course organisation** — group tasks by university course with colour labels
- **Dashboard** — statistics overview, progress bar, upcoming and overdue task lists
- **Live countdowns** — due-date timers update every 30 seconds without a page refresh
- **AJAX interactions** — mark tasks done/undone instantly with toast feedback
- **Responsive design** — works on mobile, tablet, and desktop (Bootstrap 5 grid)
- **Accessibility** — WCAG 2.2 AA compliant (skip link, ARIA, focus management, contrast)

---

## Requirements

- Python 3.9+
- pip

---

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd study-plan
```

### 2. Create and activate a virtual environment (recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example and edit as needed:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and set a strong `SECRET_KEY` for any non-local environment.

### 5. Run database migrations

```bash
python manage.py migrate
```

### 6. (Optional) Create a superuser for the admin panel

```bash
python manage.py createsuperuser
```

### 7. Start the development server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000** — you will be redirected to the login page.

---

## Running the Tests

The test suite covers model logic, form validation, view responses, access control, and the AJAX toggle endpoint.

### Run all tests

```bash
python manage.py test tasks accounts
```

### Run with verbose output (recommended)

```bash
python manage.py test tasks accounts --verbosity=2
```

### Run a specific test module

```bash
# Model and view tests for the tasks app only
python manage.py test tasks --verbosity=2

# Form and view tests for the accounts app only
python manage.py test accounts --verbosity=2
```

### Run a single test case or method

```bash
# All tests in one class
python manage.py test tasks.tests.TaskModelTest --verbosity=2

# A single test method
python manage.py test tasks.tests.TaskToggleViewTest.test_toggle_todo_to_done
```

### Expected output

```
Ran 72 tests in ~50s
OK
```

---

## Test Coverage Summary

| Module | Tests | What is covered |
|--------|-------|-----------------|
| `tasks.tests.CourseModelTest` | 5 | `__str__`, default colour, ordering, cascade delete |
| `tasks.tests.TaskModelTest` | 15 | `is_done`, `is_overdue`, `days_until_due`, ordering, user isolation |
| `tasks.tests.DashboardViewTest` | 4 | Auth redirect, stats calculation, cross-user isolation |
| `tasks.tests.TaskListViewTest` | 5 | List loads, own-data isolation, search/status/priority filters |
| `tasks.tests.TaskCreateViewTest` | 4 | Create form, save, validation, anonymous redirect |
| `tasks.tests.TaskEditDeleteViewTest` | 5 | Edit, delete, 404 on other user's tasks |
| `tasks.tests.TaskToggleViewTest` | 5 | AJAX toggle (todo→done, done→todo), JSON response, GET 405, 404 guard |
| `tasks.tests.CourseViewTest` | 4 | List, create, 404 guard, annotation |
| `accounts.tests.RegisterFormTest` | 5 | Valid form, mismatched passwords, duplicate email, blank username |
| `accounts.tests.ProfileFormTest` | 3 | Valid update, email conflict, keep own email |
| `accounts.tests.LoginViewTest` | 5 | Page load, valid login, invalid password, logout |
| `accounts.tests.RegisterViewTest` | 5 | Page load, create user, error cases, auth redirect |
| `accounts.tests.ProfileViewTest` | 3 | Page load, update name, login required |

---

## Project Structure

```
study-plan/
├── studyplanner/          # Django project settings & root URLs
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── tasks/                 # Main app — tasks, courses, dashboard
│   ├── models.py          # Course, Task models
│   ├── views.py           # All task/course/dashboard views
│   ├── forms.py           # TaskForm, CourseForm
│   ├── urls.py            # Named URL patterns
│   ├── admin.py
│   └── tests.py           # 54 tests
├── accounts/              # Authentication app
│   ├── views.py           # register, login, logout, profile
│   ├── forms.py           # RegisterForm, StyledAuthenticationForm, ProfileForm
│   ├── urls.py
│   └── tests.py           # 18 tests
├── templates/
│   ├── base.html          # Global layout (Bootstrap 5, skip link, flash messages)
│   ├── partials/
│   │   ├── navbar.html
│   │   └── footer.html
│   ├── tasks/             # Task & course templates
│   └── accounts/          # Auth templates
├── static/
│   ├── css/main.css       # Design system (tokens, WCAG contrast, animations)
│   └── js/
│       ├── main.js        # CSRF helper, toasts, countdowns, stat counters
│       ├── tasks.js       # AJAX toggle, delete modal, filter auto-submit
│       └── auth.js        # Password match validation
├── .env                   # Local environment variables (not committed)
├── requirements.txt
└── README.md
```

---

## Deployment (Render / Railway)

1. Set `DEBUG=False` and a strong `SECRET_KEY` in environment variables.
2. Add your domain to `ALLOWED_HOSTS`.
3. Switch `DATABASES` to PostgreSQL (install `psycopg2-binary`).
4. Run `python manage.py collectstatic`.
5. Use `gunicorn studyplanner.wsgi` as the start command.
