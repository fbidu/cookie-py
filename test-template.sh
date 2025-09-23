#!/bin/bash
set -e

echo "Testing cookiecutter template..."

# Generate project from template using non-interactive mode without hooks
cookiecutter /template --no-input --overwrite-if-exists

# Navigate to the generated project
cd my-awesome-project

echo "Initializing git repository..."
git init

echo "Installing dependencies with uv..."
uv sync --dev

echo "Running ruff check..."
uv run ruff check .

echo "Running ruff format check..."
uv run ruff format --check .

echo "Running pyright..."
pyright

echo "Running tests..."
uv run pytest

echo "Installing and running pre-commit..."
pre-commit install --install-hooks
pre-commit install -t pre-push
git add .
pre-commit run --all-files

echo "✅ All tests passed! Cookiecutter template works correctly."