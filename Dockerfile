FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv and cookiecutter
RUN pip install --no-cache-dir uv cookiecutter

# Set working directory
WORKDIR /workspace

# Copy the cookiecutter template
COPY . /template

# Create a test script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Testing cookiecutter template..."\n\
\n\
# Generate project from template using non-interactive mode\n\
cookiecutter /template --no-input --overwrite-if-exists\n\
\n\
# Navigate to the generated project\n\
cd my-awesome-project\n\
\n\
echo "Installing dependencies with uv..."\n\
uv sync --dev\n\
\n\
echo "Running ruff check..."\n\
uv run ruff check .\n\
\n\
echo "Running ruff format check..."\n\
uv run ruff format --check .\n\
\n\
echo "Running pyright..."\n\
uv run pyright\n\
\n\
echo "Running tests..."\n\
uv run pytest\n\
\n\
echo "✅ All tests passed! Cookiecutter template works correctly."\n\
' > /test-template.sh && chmod +x /test-template.sh

CMD ["/test-template.sh"]
