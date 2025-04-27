import logging
import uvicorn
import os
import time
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

from ..api import (
    subscriptions,
    resource_groups,
    virtual_machines,
    vm_shortcuts,
    vm_hostnames,
    vm_report,
    routes,
    root,  # Import the root router
)
from .config import settings

# Configure main logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Create a dedicated request logger
request_logger = logging.getLogger("azure_rm_proxy.requests")
request_logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
logs_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs"
)
os.makedirs(logs_dir, exist_ok=True)

# Set up the request log file handler
request_log_file = os.path.join(logs_dir, "requests.log")
request_file_handler = logging.FileHandler(request_log_file, mode="w")
request_file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
request_logger.addHandler(request_file_handler)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Get request details
        request_id = str(id(request))
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"

        request_logger.info(
            f"Request {request_id} started: {method} {url} from {client_host}"
        )

        # Process the request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time
        formatted_process_time = f"{process_time:.4f}"
        status_code = response.status_code

        request_logger.info(
            f"Request {request_id} completed: {method} {url} - Status: {status_code} - Time: {formatted_process_time}s"
        )

        return response


app = FastAPI(title="Azure RM Proxy Server", version="0.1.0")

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(subscriptions.router)
app.include_router(resource_groups.router)
app.include_router(virtual_machines.router)
app.include_router(vm_shortcuts.router)
app.include_router(vm_hostnames.router)
app.include_router(vm_report.router)
app.include_router(routes.router)
app.include_router(root.router)  # Include the root router


@app.get("/api/ping")
async def ping():
    logger.info("Ping endpoint called")
    return "pong"


@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    logger.info("Azure RM Proxy Server starting up")
    # You could pre-warm caches or initialize resources here if needed


def run_server():
    """Run the server using uvicorn. Used for Poetry script entry point."""
    uvicorn.run("azure_rm_proxy.app.main:app", host="0.0.0.0", port=8000, reload=True)


def start():
    """Entry point for the Poetry script."""
    run_server()


if __name__ == "__main__":
    # Direct execution
    uvicorn.run(app, host="0.0.0.0", port=8000)
