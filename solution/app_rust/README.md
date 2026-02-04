# DevOps Info Service (Python / FastAPI)

## Overview

**DevOps Info Service** is an educational web service that present simple simple JSON-based HTTP API.


---

## Tech Stack

- **Rust:** v0.4.1
- **Web Framework:** actix-web v4.3

---

## Prerequisites

- Rust toolchain installed

---

## Project Structure

```
.
├── Cargo.lock
├── Cargo.toml
├── Dockerfile
├── .dockerignore
├── docs
│   ├── LAB01.md
│   ├── Rust.md
│   └── screenshots
│       └── curl-output.png
├── README.md
├── src
│   ├── config.rs
│   ├── main.rs
│   ├── routes.rs
│   └── system.rs
```

---
## Run options
### Run on host
1. Install the rust-toolchain (rust-up). Installation guide provided at https://rustup.rs/
2. Clone the repository and navigate to the project directory
    ```bash
    cd solution/app_rust
    ```
3. Compile the project
    ```bash
    cargo build      # for dev version
    # cargo build -r # for release version with optimizations
    ```
4. Run the compiled binary at 
    ```bash
    ./target/debug/devops-info-service # or .\target\debug\devops-info-service.exe on Windows
    ```
---

### Running the Application

#### Run with default settings

```bash
./target/debug/devops-info-service
```

Default configuration:

* HOST: `0.0.0.0`
* PORT: `5000`

#### Run with environment variables

```bash
PORT=8080 ./target/debug/devops-info-service
HOST=127.0.0.1 PORT=3000 ./target/debug/devops-info-service
DEBUG=true python ./target/debug/devops-info-service
```

---

### Local Docker build
1. Be sure docker instance is installed and daemon is running ([`docker.io`](https://docs.docker.com/get-started/get-docker/) or [`docker desktop`](https://docs.docker.com/desktop/))
2. Clone the repository and navigate to the project directory
   ```bash
   cd solution/app_rust
   ```
3. Build the image
   ```bash 
   docker build -t devops-i-lobazov-rust:0.1.0 
   ```
4. Run the container with port specification (and optionally environment variables)
   ```bash 
   docker run -p 5000:80 -e DEBUG=true devops-i-lobazov-rust:0.1.0 
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
    "framework": "ActixWeb"
  },
  "system": {
    "hostname": "my-host",
    "platform": "Linux",
    "platform_version": "6.8.0",
    "architecture": "x86_64",
    "cpu_count": 8,
    "rust_version": "0.4.1"
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
timestamp - level - logger - message
```

Log level is controlled by the `DEBUG` environment variable.
