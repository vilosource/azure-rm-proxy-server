# Use Python 3.12 slim as the base image for smaller size
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Install Azure Developer CLI
RUN curl -fsSL https://aka.ms/install-azd.sh | bash

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Copy pyproject.toml and poetry.lock first for better layer caching
COPY pyproject.toml poetry.lock* ./

# Install dependencies only (without the project)
RUN poetry install --no-root --no-dev --no-interaction

# Copy the rest of the application
COPY . .

# Install the project itself
RUN poetry install --no-dev --no-interaction

# Set default environment variables for Redis caching
ENV CACHE_TYPE=redis \
    REDIS_URL=redis://redis:6379/0 \
    REDIS_PREFIX=azure_rm_proxy:

# Expose the port the app runs on
EXPOSE $PORT

# Add a healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/ping || exit 1

# Create a non-root user and switch to it for security
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /app
USER appuser

# Command to run the application
CMD poetry run gunicorn azure_rm_proxy.app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120