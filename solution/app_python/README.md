# DevOps Info Service (Python / FastAPI)

## Overview

**DevOps Info Service** is an educational web service that present simple simple JSON-based HTTP API.
  

---

## Tech Stack

- **Python:** v3.14
- **Web Framework:** FastAPI v0.128.0
- **ASGI Server:** Uvicorn v0.40.0

---

## Prerequisites

- Python **3.11** or newer
- pip
- (recommended) `virtualenv`

---

## Project Structure

```
app_python/
├── __init__.py
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
├── docs/
│   ├── LAB01.md
│   └── screenshots/
│       ├── 01-main-endpoint.png
│       ├── 02-health-check.png
│       └── 03-formatted-output.png
├── tests/
│   └── __init__.py
```

---

## Installation

1. Clone the repository and navigate to the project directory
    ```bash
    cd solution
    ```
2. Create and activate a virtual environment
    ```bash
    python -m venv .venv
    source venv/bin/activate #.fish # Linux / macOS
    # venv\Scripts\activate         # Windows
    ```
3. Install dependencies
    ```bash
    pip install -r requirements.txt
    ```
---

## Running the Application

### Run with default settings

```bash
python app.py
```

Default configuration:

* HOST: `0.0.0.0`
* PORT: `5000`

### Run with environment variables

```bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
DEBUG=true python app.py
```

---

## API Endpoints

### `GET /` — Service Information

Returns detailed information about the service, system, runtime, and incoming request.

Example response:

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "my-host",
    "platform": "Linux",
    "platform_version": "6.8.0",
    "architecture": "x86_64",
    "cpu_count": 8,
    "python_version": "3.11.6"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hours, 0 minutes",
    "current_time": "2026-01-07 14:30:00",
    "timezone": ""
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "curl/7.81.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {
      "path": "/",
      "method": "GET",
      "description": "System and service info about the server"
    },
    {
      "path": "/health",
      "method": "GET",
      "description": "Service health chek"
    }
  ]
}
```

---

### `GET /health` — Health Check

A lightweight endpoint for monitoring and orchestration systems.

Example response:

```json
{
  "status": "healthy",
  "timestamp": "2026-01-07 14:32:10",
  "uptime_seconds": 3720
}
```

HTTP status: **200 OK**

---

## Configuration

The application is configurable via environment variables:

| Variable | Default   | Description                 |
| -------- | --------- | --------------------------- |
| `HOST`   | `0.0.0.0` | Server bind address         |
| `PORT`   | `5000`    | Server port                 |
| `DEBUG`  | `false`   | Enables debug-level logging |

---

## Logging

* INFO logs on application startup and shutdown
* DEBUG logs for incoming HTTP requests
* Log format:

```
timestamp - logger - level - message
```

Log level is controlled by the `DEBUG` environment variable.
