#!/bin/bash
# Bootstrap smoke test: exercises the template end-to-end on a minimal
# Python image (no pre-installed tools beyond what the Dockerfile sets up).
# Catches missing system packages and bootstrap issues that the host-based
# pytest integration tests would miss. For configuration-matrix coverage
# (multiple ci_provider / python_version / license combinations), see
# tests/test_copier_integration.py instead.
set -e

echo "Generating project from template..."
copier copy --defaults --UNSAFE /template /workspace/my-awesome-project

cd /workspace/my-awesome-project

echo "Initializing git repository..."
git init

echo "Installing dependencies with uv..."
uv sync --dev

echo "Running ruff check..."
uv run ruff check .

echo "Running ruff format check..."
uv run ruff format --check .

echo "Running pyright..."
uv run pyright

echo "Running tests..."
uv run pytest

echo "Installing and running pre-commit..."
pre-commit install --install-hooks
git add .
pre-commit run --all-files

echo "Smoke test passed."
