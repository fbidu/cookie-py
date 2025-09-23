# Modern Python Dockerfile using uv
# Based on uv's official Docker guidance: https://docs.astral.sh/uv/guides/integration/docker/

FROM python:{{cookiecutter.python_version}}-slim as python-base

# Python configuration
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# `builder` stage - install dependencies
FROM python-base as builder

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies in a virtual environment
RUN uv sync --frozen --no-dev

# `development` stage - includes dev dependencies and tools
FROM python-base as development

# Install system dependencies that might be needed for development
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dev dependencies
RUN uv sync --frozen

# Make sure we use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Default command for development
CMD ["uv", "run", "ipython"]

# `production` stage - minimal runtime image
FROM python-base as production

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy the application code
COPY . /app
WORKDIR /app

# Make sure we use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Run the application
CMD ["python", "-m", "{{cookiecutter.pkg_name}}"]
