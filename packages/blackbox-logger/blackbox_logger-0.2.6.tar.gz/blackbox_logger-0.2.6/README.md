# 🕵️‍♂️ BlackBox Logger

![PyPI](https://img.shields.io/pypi/v/blackbox-logger)
![License](https://img.shields.io/github/license/avi9r/blackbox_logger)

A universal request/response logger for **Django**, **Flask**, **FastAPI**, and other Python apps.  
Automatically logs requests and responses, user info, IP address, and more — with **masked sensitive data** — into a log file and SQLite/PostgreSQL database.

---

## 🚀 Features

- ✅ Logs all HTTP requests and responses  
- ✅ Logs to both `blackbox.log` file and SQLite or PostgreSQL DB  
- ✅ Automatically masks sensitive fields (e.g., `password`, `token`, etc.)  
- ✅ Logs user (if available), IP address, user agent, and request duration  
- ✅ Skips HTML/JS or large responses automatically  
- ✅ Supports log rotation  
- ✅ Decorator-based and middleware-based integration  
- ✅ Works out-of-the-box in **Django**, **Flask**, and **FastAPI**

---

## 📦 Installation

```bash
pip install blackbox-logger
# Or install directly from GitHub:
pip install git+https://github.com/avi9r/blackbox_logger.git
```

---

## 📁 Logs

- `log/blackbox.log` — rotating file logs  
- `log/blackbox_logs.db` — SQLite DB (or PostgreSQL if configured)

---

## ⚙️ Usage

### 🟩 Django Middleware

```python
from django.utils.deprecation import MiddlewareMixin
from blackbox_logger.logger import HTTPLogger
import time

logger = HTTPLogger()

class BlackBoxLoggerMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._start_time = time.time()
        logger.log_request(request.method, request.path, dict(request.headers), request.body, request)

    def process_response(self, request, response):
        duration = time.time() - getattr(request, "_start_time", time.time())
        logger.log_response(
            request.method, request.path, dict(response.headers),
            response.content, response.status_code, request, duration
        )
        return response
```

Then in `settings.py`:

```python
MIDDLEWARE = [
    'your_project.middleware.BlackBoxLoggerMiddleware',
    ...
]
```

### 🔵 Django Decorator Usage

```python
from blackbox_logger.logger import HTTPLogger
logger = HTTPLogger()

@logger.decorator
def my_view(request):
    return JsonResponse({"message": "OK"})
```

---

### 🟖 Flask Middleware

```python
from flask import Flask, request
from flask_login import current_user
from blackbox_logger.logger import HTTPLogger
import time

logger = HTTPLogger(get_user=lambda h, r=None: current_user.username if current_user.is_authenticated else "Anonymous")
app = Flask(__name__)

@app.before_request
def log_request():
    request._start_time = time.time()
    logger.log_request(request.method, request.path, dict(request.headers), request.get_data(), request)

@app.after_request
def log_response(response):
    duration = time.time() - getattr(request, '_start_time', time.time())
    logger.log_response(
        request.method, request.path, dict(response.headers),
        response.get_data(), response.status_code, request, duration
    )
    return response
```

### 🟨 Flask Decorator Usage

```python
@logger.decorator
def your_flask_view():
    return jsonify({"msg": "Hello"})
```

---

### 🟘 FastAPI Middleware

```python
from fastapi import FastAPI, Request, Response
from blackbox_logger.logger import HTTPLogger

logger = HTTPLogger()
app = FastAPI()

@app.middleware("http")
async def blackbox_logger_middleware(request: Request, call_next):
    request.state.user = "Anonymous"  # attach user if needed
    body = await request.body()
    sqlite_logger.log("request", request.method, str(request.url), request.state.user, request.client.host, request.headers, body)
    file_logger.info(f"Request: {request.method} {request.url} {request.state.user} {request.client.host} {request.headers} {body}")

    response = await call_next(request)
    response_body = b"".join([chunk async for chunk in response.body_iterator])
    response.body_iterator = iter([response_body])

    sqlite_logger.log("response", request.method, str(request.url), request.state.user, request.client.host, dict(response.headers), response_body, response.status_code)
    file_logger.info(f"Response: {request.method} {request.url} {request.state.user} {request.client.host} {dict(response.headers)} {response_body} {response.status_code}")
    return response
```

### 🟦 FastAPI Decorator Usage

```python
@app.get("/hello")
@logger.decorator
def hello(request: Request):
    return {"hello": "world"}
```

---

## 🔍 Decorator vs Middleware Summary

| Integration Style             | Need Decorator? | Works Without It? |
|------------------------------|------------------|-------------------|
| Django/Flask/FastAPI Middleware | ❌ No            | ✅ Yes             |
| Manual log_request/log_response | ❌ No           | ✅ Yes             |
| Only with `@decorator`       | ✅ Yes (if no middleware) | ✅ Yes     |

---

## 🔐 Masking Sensitive Data

Default masked fields:

```python
["password", "token", "access_token", "secret", "authorization", "csrfmiddlewaretoken"]
```

To add custom fields:

```python
logger = HTTPLogger(custom_mask_fields={"otp", "session_id"})
```

---

## 📃 PostgreSQL Support

Set these environment variables:

```bash
BLACKBOX_DB_TYPE=postgres
BLACKBOX_PG_DB=blackbox_logs
BLACKBOX_PG_USER=postgres
BLACKBOX_PG_PASSWORD=secret
BLACKBOX_PG_HOST=localhost
BLACKBOX_PG_PORT=5432
```

---

## 🔄 Log Rotation

Enable rotating file logs:

```bash
BLACKBOX_LOG_MAX_SIZE=1048576     # 1MB
BLACKBOX_LOG_BACKUP_COUNT=5       # Keep 5 backups
```

---

## 📜 Sample Output

```log
2025-06-19 18:29:15 [INFO] [REQUEST] POST /api/login | User: admin | IP: 127.0.0.1 | Payload: {"username": "admin", "password": "***"}
2025-06-19 18:29:15 [INFO] [RESPONSE] POST /api/login | User: admin | IP: 127.0.0.1 | Status: 200 | Duration: 0.23s | Response: {"status": "ok"}
```

---

## 📓 License

MIT License

<!-- Build commands -->
<!-- rm -rf build dist *.egg-info-->
<!-- python -m build -->
<!-- twine upload dist/* -->