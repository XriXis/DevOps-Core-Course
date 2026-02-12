import platform
import os
import logging
from contextlib import asynccontextmanager
from starlette.exceptions import HTTPException
from datetime import datetime

from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from uvicorn import run

START_TIME = datetime.now()
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    yield
    logger.info("Shutting down...")


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


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> HTMLResponse:
    """Default page for error display"""
    logger.debug(f"Error occurs {exc.detail}. Answer with code {exc.status_code}")
    return HTMLResponse(
        content=f"<h1>Error {exc.status_code}</h1><p>{exc.detail}</p>",
        status_code=exc.status_code
    )


@app.get("/", description="System and service info about the server")
async def root(request: Request) -> JSONResponse:
    """System and service info about the server"""
    logger.debug(f'Request: {request.method} {request.url.path}')
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
    logger.debug(f'Request: {request.method} {request.url.path}')
    return JSONResponse(status_code=200, content={
        "status": "healthy",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "uptime_seconds": get_uptime()["seconds"],
    })


if __name__ == "__main__":
    run(app, port=PORT, host=HOST)
