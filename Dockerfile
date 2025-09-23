FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install uv, cookiecutter, pre-commit, and pyright
RUN pip install --no-cache-dir uv cookiecutter pre-commit pyright

# Set git config for Docker environment
RUN git config --global user.email "test@example.com" && \
    git config --global user.name "Test User" && \
    git config --global init.defaultBranch main

# Set working directory
WORKDIR /workspace

# Copy the cookiecutter template
COPY . /template

# Copy and setup the test script
COPY test-template.sh /test-template.sh
RUN chmod +x /test-template.sh

CMD ["/test-template.sh"]
