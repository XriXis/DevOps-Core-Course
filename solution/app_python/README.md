# DevOps Info Service (Python / FastAPI)

[![Python CI](https://github.com/XriXis/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/XriXis/DevOps-Core-Course/actions/workflows/python-ci.yml)
[![Python CD](https://github.com/XriXis/DevOps-Core-Course/actions/workflows/python-cd.yml/badge.svg)](https://github.com/XriXis/DevOps-Core-Course/actions/workflows/python-cd.yml)

## Overview

**DevOps Info Service** is an educational web service that present simple simple JSON-based HTTP API.
  

---

## Tech Stack

- **Python:** v3.12
- **Web Framework:** FastAPI v0.128.0
- **ASGI Server:** Uvicorn v0.40.0

---

## Prerequisites

- `Python 3.11` or newer
- `pip`
- `docker` or `virtualenv` 

---

## Project Structure

```
app_python/
├── __init__.py
├── app.py
├── requirements.txt
├── .gitignore
├── Dockerfile
├── .dockerignore
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
## Run options 
### Run on host

1. Clone the repository and navigate to the project directory
    ```bash
    cd solution/app_python
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

#### Run with default settings

```bash
python app.py
```

Default configuration:

* HOST: `0.0.0.0`
* PORT: `5000`

#### Run with environment variables

```bash
PORT=8080 python app.py
HOST=127.0.0.1 PORT=3000 python app.py
DEBUG=true python app.py
```

#### Run Tests Locally

1. Navigate to project directory
    ```bash
    cd solution/app_python
    ```

2. Install development dependencies (if not already installed)
    ```bash
    pip install -r requirements.dev.txt
    ```

3. Run all tests with coverage
    ```bash
    pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing
    ```

4. View coverage report
    ```bash
    # HTML report will be generated in htmlcov/index.html
    open htmlcov/index.html  # macOS/Linux
    start htmlcov/index.html # Windows
    ```

**Testing Framework:** pytest  
**Coverage Target:** 70%+ of code  
**Test Location:** `tests/test_app.py`

---

### Local Docker build
1. Be sure docker instance is installed and daemon is running ([`docker.io`](https://docs.docker.com/get-started/get-docker/) or [`docker desktop`](https://docs.docker.com/desktop/))
2. Clone the repository and navigate to the project directory
   ```bash
   cd solution/app_python
   ```
3. Build the image
   ```bash 
   docker build -t devops-i-lobazov:0.1.0 
   ```
4. Run the container with port specification (and optionally environment variables)
   ```bash 
   docker run -p 5000:80 -e DEBUG=true devops-i-lobazov:0.1.0 
   ```
### Obtain built image from docker hub
1. Be sure docker instance is installed and daemon is running ([`docker.io`](https://docs.docker.com/get-started/get-docker/) or [`docker desktop`](https://docs.docker.com/desktop/))
2. Login in the `Docker hub`
   ```bash 
   docker login # follow the instructions if any
   ```
3. Pull the image
   ```bash 
   docker pull xrixis/devops-i-lobazov:0.1.0 
   ```
4. Run the container with port specification (and optionally environment variables)
   ```bash 
   docker run -p 5000:80 -e DEBUG=true devops-i-lobazov:0.1.0 
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
