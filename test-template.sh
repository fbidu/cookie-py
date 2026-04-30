#!/bin/bash
set -e

echo "Testing Copier template..."

# Generate project from template using non-interactive mode
copier copy --defaults --UNSAFE /template /workspace/my-awesome-project

# Navigate to the generated project
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
pre-commit install -t pre-push
git add .
pre-commit run --all-files

echo "All tests passed! Copier template works correctly."
