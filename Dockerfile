FROM python:3.14-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv, copier, prek, and pyright
RUN pip install --no-cache-dir uv copier prek pyright

# Set git config for Docker environment
RUN git config --global user.email "test@example.com" && \
    git config --global user.name "Test User" && \
    git config --global init.defaultBranch main

# Set working directory
WORKDIR /workspace

# Copy the template
COPY . /template

# Copy and setup the smoke test script
COPY smoke-test.sh /smoke-test.sh
RUN chmod +x /smoke-test.sh

CMD ["/smoke-test.sh"]
