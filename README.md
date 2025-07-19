````markdown
# Flask JWT Auth API

This is a minimal and extendable Flask API implementing **JWT Authentication** using `Flask-JWT-Extended`, with access and refresh token support, Redis-powered token revocation, role-based protection possibilities, and essential auth endpoints.

---

## 🚀 Features

- User registration and login
- JWT-based access and refresh tokens
- Logout with token revocation using Redis
- Fresh-token support for sensitive operations
- Profile management with protected routes
- Token verification and refresh flow
- Secure configuration via environment variables

---

## ⚙️ Environment Setup

### 1. Clone this repo:

```bash
git clone https://github.com/yourusername/flask_jwt_auth.git
cd flask_jwt_auth
````

### 2. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Export environment variables

```bash
export USER=user
export PWD=your_password
export HOST=localhost
export DB=your_db_name
export ENV=dev

# JWT secret key (use a strong, secure key!)
export JWT_SECRET_KEY=''

# Flask App Server
export API_HOST=0.0.0.0
export API_PORT=5000
```

---

### 🛠️ Setting the `DATABASE_URL`

Before running the app or applying migrations, you need to set your database connection string as an environment variable called `DATABASE_URL`.

#### Example for MySQL:

```bash
export DATABASE_URL=mysql+mysqldb://username:password@localhost/sentinel_osint
```

#### Example for SQLite (for testing):

```bash
export DATABASE_URL=sqlite:///sentinel.db
```

> This tells both the Flask app and Alembic where to connect for database operations.

#### 📌 Notes:

* Replace `username`, `password`, `localhost`, and `sentinel_osint` with your actual DB config.
* You can add this line to your `.bashrc` or `.zshrc` for persistence.
* If you're using a `.env` file, make sure to load it with `python-dotenv` or something similar.

---

## 🗃️ Database Migrations with Alembic

Once you’ve set up and configured Alembic (as you’ve already done), use these commands to manage migrations:

### 1. Create a Migration Revision

```bash
alembic revision --autogenerate -m "create user and scan tables"
```

> This compares your models to the current database and generates a new migration script.

### 2. Apply Migrations to the Database

```bash
alembic upgrade head
```

> This applies all pending migrations.

### 3. Roll Back (Optional)

```bash
alembic downgrade -1
```

> Reverts the most recent migration.

---

### 🔧 Notes

* Make sure your `alembic.ini` and `env.py` are properly set to use the same DB URI as your Flask app.
* You should **commit your migration scripts** (under `migrations/versions/`) into source control.

---

## 🧪 API Endpoints & CURL Examples

### 🔐 Register a User

```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "ezradev", "email": "ezra@example.com", "password": "securepass"}'
```

### 🔐 Login (Get Access & Refresh Tokens)

```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "ezra@example.com", "password": "securepass"}'
```

### 🔒 Get Authenticated User Profile

```bash
curl -X GET http://localhost:5000/users/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### ✏️ Update Username

```bash
curl -X PUT http://localhost:5000/users/me \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"username": "ezra_updated"}'
```

### 🔄 Refresh Access Token

```bash
curl -X POST http://localhost:5000/auth/token/refresh \
  -H "Authorization: Bearer <REFRESH_TOKEN>"
```

### 🚪 Logout (Invalidate Access Token)

```bash
curl -X POST http://localhost:5000/auth/logout \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

## 🛠 Requirements

* Python 3.8+
* Redis running locally on `localhost:6379`
* Flask + Flask-JWT-Extended
* dotenv (optional for local `.env` loading)

---

## 📦 Project Structure

```
├── api/
│   └── v1/
│       └── views/
│           ├── __init__.py
│           └── users.py
├── models/
│   └── user.py
├── app.py
├── requirements.txt
└── README.md
```

---

## 🧱 Next Steps

* Add role-based access control
* Add email confirmation (optional)
* Add rate limiting to auth endpoints
* Enable HTTPS and secure cookies for production

---

## 💡 Tips

* Redis is used for blacklisting revoked tokens with TTL set to match the token's expiry.
* Refresh tokens must be kept secure and only used when access tokens expire.
* `@jwt_required(fresh=True)` ensures sensitive endpoints require a recently issued token.

---

---

# 🔧 Extended Features

## ⚙️ Celery Integration with Flask JWT Auth API

This section explains how **Celery** was integrated into the Flask JWT-based authentication system for background task processing using **Redis** as both the **broker** and **result backend**.

---

## 🔧 Why Celery?

Celery is used to run long-running or asynchronous tasks **outside** the main Flask request-response cycle. This makes the API more responsive and scalable — great for OSINT scanning tasks, background emails, analytics, etc.

---

## 🛠 Requirements

* Python 3.8+
* Redis running locally at `localhost:6379` (or configured via `REDIS_URL`)
* Celery 5.x
* Flask 2.x
* Flask-JWT-Extended

---

## 📁 Project Directory Overview (with Celery)

```
backend/
├── api/
│   └── v1/
│       └── app.py  ← Flask app + celery initialized here
├── tasks/
│   └── test_task.py  ← Celery tasks go here
├── extensions/
│   └── celery_utils.py  ← make_celery() function defined here
├── test_celery_task.py  ← test script for calling celery task
├── requirements.txt
└── README.md / CELERY_SETUP.md
```

---

## 🔗 How Flask and Celery Were Integrated

### 1. `make_celery()` Utility

In `extensions/celery_utils.py`:

```python
from celery import Celery

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config["CELERY_RESULT_BACKEND"],
        broker=app.config["CELERY_BROKER_URL"]
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
```

> This ensures tasks have access to Flask context, like `current_app` or database models.

---

### 2. Update Flask App to Initialize Celery

In `api/v1/app.py`, we added:

```python
from extensions.celery_utils import make_celery

app.config["CELERY_BROKER_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/3")
app.config["CELERY_RESULT_BACKEND"] = os.getenv("REDIS_URL", "redis://localhost:6379/3")

celery = make_celery(app)
app.celery = celery
```

---

### 3. Create a Test Task

In `tasks/test_task.py`:

```python
from api.v1.app import app

celery = app.celery

@celery.task(name="test.add")
def add(x, y):
    return x + y
```

> This is a basic task for testing. You can later add actual OSINT scan tasks.

---

### 4. Create a Script to Trigger Task

In `test_celery_task.py`:

```python
from tasks.test_task import add

result = add.delay(3, 4)
print(f"Task submitted. Task ID: {result.id}")
```

---

## 🧪 How to Run Everything (Multi-Terminal Setup)

> You **must activate the virtual environment and export env variables in *each* terminal**.

### 🖥️ Terminal 1: Start Redis

```bash
sudo service redis-server start
```

Or, if Redis is running via Docker or systemctl, ensure it's running.

---

### 🖥️ Terminal 2: Start Celery Worker

```bash
cd backend/
source venv/bin/activate

# Set env variables
export JWT_SECRET_KEY='your_secret_key'
export REDIS_URL='redis://localhost:6379/3'

celery -A tasks.test_task.celery worker --loglevel=info
```

Expected output:

```
[tasks]
  . test.add
[INFO/MainProcess] celery@yourhostname ready.
```

---

### 🖥️ Terminal 3: Trigger Task

```bash
cd backend/
source venv/bin/activate

# Export same environment variables
export JWT_SECRET_KEY='your_secret_key'
export REDIS_URL='redis://localhost:6379/3'

python3 test_celery_task.py
```

Expected output:

```bash
Task submitted. Task ID: abc123-def456...
```

Then check **Terminal 2** for:

```bash
Task test.add[abc123] received
Task test.add[abc123] succeeded: 7
```

---

## 🧱 Tips for Using Celery with Flask

* **Always export required variables in every shell**.
* Use `delay()` to call tasks asynchronously: `task.delay(*args)`.
* Use `apply_async()` if you want to schedule or customize task calls.
* You can inspect task status with:

  ```python
  result = task.delay(...)
  result.ready()
  result.get(timeout=5)
  ```

---

## 🧰 Additional Suggestions

* You can group tasks using `@shared_task`.
* Add Celery Beat for scheduled tasks (periodic scans).
* Use separate task files per module (like `domain_scan.py`, `email_scan.py`).
* Monitor using [Flower](https://flower.readthedocs.io/en/latest/):

  ```bash
  pip install flower
  celery -A tasks.test_task.celery flower
  ```

---

## 📌 Summary

✅ Celery was integrated by:

* Creating `make_celery()` for Flask context support
* Setting Celery config in Flask `app.config`
* Writing and testing a simple async task
* Running Redis, Celery, and Flask in **parallel terminals** with environment setup

You now have a **production-ready background worker** setup started. You can later add queues, routing, or Celery Beat as needed.```

