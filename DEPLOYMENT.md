# Deploying Study Planner to Replit

This guide walks you through deploying the application on Replit with a **permanent PostgreSQL database**.

---

## Prerequisites

- A free [Replit](https://replit.com) account
- The project files uploaded to a Replit Repl (or imported from GitHub)

---

## Step 1 — Create a new Repl and upload the project

**Option A — Import from GitHub (recommended):**
1. On Replit, click **+ Create Repl**
2. Choose **Import from GitHub**
3. Paste your repository URL
4. Replit detects Python automatically

**Option B — Upload manually:**
1. Click **+ Create Repl** → select **Python** template
2. Delete the default `main.py`
3. Drag-and-drop the entire project folder into the Replit file panel
4. Make sure the top-level structure matches:
   ```
   manage.py
   studyplanner/
   tasks/
   accounts/
   templates/
   static/
   requirements.txt
   .replit
   replit.nix
   ```

---

## Step 2 — Create a PostgreSQL database (persistent storage)

1. In the left sidebar, click **Tools** → **Database** (or the database icon)
2. Click **Create a database** → choose **PostgreSQL**
3. Replit automatically creates the database and adds a `DATABASE_URL` secret to your Repl
4. Verify: go to **Secrets** (lock icon in sidebar) and confirm `DATABASE_URL` exists — it will look like:
   ```
   postgresql://user:password@host:port/dbname
   ```

> **This is the key step for permanent data.** SQLite data is lost whenever the Repl restarts; PostgreSQL data persists indefinitely.

---

## Step 3 — Add the required Secrets

In the **Secrets** panel (lock icon), add the following key-value pairs:

| Key | Value | Notes |
|-----|-------|-------|
| `SECRET_KEY` | A long random string | Generate one at [djecrety.ir](https://djecrety.ir) |
| `DEBUG` | `False` | Must be False in production |
| `DATABASE_URL` | *(already added by Replit in Step 2)* | Do not change |

**To generate a secure SECRET_KEY**, run this in the Replit Shell:
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```
Copy the output and paste it as the value for `SECRET_KEY`.

---

## Step 4 — Install dependencies

In the Replit **Shell** tab, run:

```bash
pip install -r requirements.txt
```

This installs Django, Gunicorn, WhiteNoise, psycopg2-binary, and all other dependencies.

---

## Step 5 — Run database migrations

Still in the Shell:

```bash
python manage.py migrate
```

This creates all the necessary tables in your PostgreSQL database. You should see output like:
```
Applying tasks.0001_initial... OK
Applying accounts.0001_initial... OK
...
```

---

## Step 6 — Collect static files

```bash
python manage.py collectstatic --noinput
```

This copies all CSS/JS/icon files into the `staticfiles/` folder, which WhiteNoise will serve in production.

---

## Step 7 — Create a superuser (optional, for admin panel)

```bash
python manage.py createsuperuser
```

Follow the prompts to set a username and password. The admin panel is available at `/admin/`.

---

## Step 8 — Test with the Run button

Click the green **Run** button. Replit will start the Django development server on port 8080. You should see your app at the URL shown at the top of the preview panel.

---

## Step 9 — Deploy for production (Always-On / Deployment)

For a **public, always-available URL**:

1. Click **Deploy** in the top-right corner (or the rocket icon)
2. Replit will use the command in `.replit` → `[deployment]` section:
   ```
   python manage.py collectstatic --noinput
   python manage.py migrate --noinput
   gunicorn studyplanner.wsgi:application --bind 0.0.0.0:$PORT --workers 2
   ```
3. After deployment, you receive a permanent URL like:
   ```
   https://study-planner.yourusername.repl.co
   ```
4. Copy this URL — you will need it for the report (Module 1).

---

## Environment Variables Summary

| Variable | Where set | Purpose |
|----------|-----------|---------|
| `SECRET_KEY` | Replit Secrets | Django cryptographic signing |
| `DEBUG` | Replit Secrets | Set to `False` in production |
| `DATABASE_URL` | Auto-set by Replit PostgreSQL | Points Django to the persistent DB |

---

## Troubleshooting

### `DisallowedHost` error
Your Replit URL is not in `ALLOWED_HOSTS`. The `settings.py` already accepts all `*.replit.app` and `*.repl.co` domains — if you see this error, confirm `DEBUG=False` is set in Secrets.

### `OperationalError: relation does not exist`
The migrations have not been run yet. Execute `python manage.py migrate` in the Shell.

### Static files (CSS/JS) not loading
Run `python manage.py collectstatic --noinput` and redeploy. WhiteNoise serves the `staticfiles/` directory automatically.

### `psycopg2` import error
The `psycopg2-binary` wheel needs the PostgreSQL client libraries. These are provided by `replit.nix`. If the error persists, run:
```bash
pip install psycopg2-binary --force-reinstall
```

---

## Data Persistence Explained

| Storage | Persistence | Used for |
|---------|------------|---------|
| PostgreSQL (via `DATABASE_URL`) | ✅ Permanent | All user accounts, courses, tasks |
| `staticfiles/` directory | ✅ Permanent (part of Repl) | CSS, JS, icons |
| `media/` directory | ⚠️ Repl disk (persistent on paid plans) | Uploaded files (none in current version) |
| `db.sqlite3` | ❌ Not used on Replit | Local development only |

Your PostgreSQL database on Replit is backed up automatically and **will not be lost** when the Repl sleeps, restarts, or is redeployed.
