import logging
import os
import platform
from datetime import datetime, timezone
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from uvicorn import run

START_TIME = datetime.now()
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'


class JSONFormatter(logging.Formatter):
    """Render application logs as JSON for Loki/Grafana ingestion."""

    _reserved_fields = {
        'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
        'funcName', 'levelname', 'levelno', 'lineno', 'module', 'msecs',
        'message', 'msg', 'name', 'pathname', 'process', 'processName',
        'relativeCreated', 'stack_info', 'thread', 'threadName', 'taskName',
    }

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in self._reserved_fields:
                payload[key] = value

        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


def setup_logging() -> logging.Logger:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    return logging.getLogger(__name__)


logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Application startup",
        extra={
            'event': 'startup',
            'host': HOST,
            'port': PORT,
            'debug': DEBUG,
            'service': 'devops-info-service',
        },
    )
    yield
    logger.info("Application shutdown", extra={'event': 'shutdown'})


app = FastAPI(lifespan=lifespan)


def get_uptime():
    delta = datetime.now() - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return {
        'seconds': seconds,
        'human': f"{hours} hours, {minutes} minutes"
    }


@app.middleware("http")
async def log_requests(request: Request, call_next):
    client_ip = request.client.host if request.client else 'unknown'
    extra = {
        'event': 'http_request',
        'method': request.method,
        'path': request.url.path,
        'client_ip': client_ip,
        'user_agent': request.headers.get('user-agent', ''),
    }

    logger.info("HTTP request started", extra=extra)

    try:
        response = await call_next(request)
    except Exception:
        logger.exception("HTTP request failed", extra=extra)
        raise

    logger.info(
        "HTTP request completed",
        extra={**extra, 'status_code': response.status_code},
    )
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> HTMLResponse:
    """Default page for error display"""
    logger.warning(
        "HTTP exception handled",
        extra={
            'event': 'http_exception',
            'method': request.method,
            'path': request.url.path,
            'status_code': exc.status_code,
            'client_ip': request.client.host if request.client else 'unknown',
            'error': exc.detail,
        },
    )
    return HTMLResponse(
        content=f"<h1>Error {exc.status_code}</h1><p>{exc.detail}</p>",
        status_code=exc.status_code
    )


@app.get("/", description="System and service info about the server")
async def root(request: Request) -> JSONResponse:
    """System and service info about the server"""
    return JSONResponse(status_code=200, content={
        "service": {
            "name": "devops-info-service",
            "version": "1.0.0",
            "description": "DevOps course info service",
            "framework": "FastAPI"
        },
        "system": {
            "hostname": platform.node(),
            "platform": platform.system(),
            "platform_version": platform.release(),
            "architecture": platform.machine(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version()
        },
        "runtime": {
            "uptime_seconds": get_uptime()["seconds"],
            "uptime_human": get_uptime()["human"],
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": datetime.now().strftime("%Z"),
        },
        "request": {
            "client_ip": request.client.host,
            "user_agent": request.headers.get('user-agent'),
            "method": request.method,
            "path": request.url.path,
        },
        "endpoints": [
            {
                "path": route.path,
                "method": method,
                "description": route.endpoint.__doc__ or ""
            }
            for route in request.app.routes
            for method in route.methods
        ]
    })


@app.get("/health", description="Service health chek")
async def health(request: Request) -> JSONResponse:
    """Service health-chek"""
    return JSONResponse(status_code=200, content={
        "status": "healthy",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "uptime_seconds": get_uptime()["seconds"],
    })


if __name__ == "__main__":
    run(app, port=PORT, host=HOST)
