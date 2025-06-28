# Dockerfile for testing uvmgr substrate commands in a clean container
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv (required by uvmgr)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Create workspace
WORKDIR /workspace

# Copy uvmgr source
COPY . /uvmgr

# Install uvmgr from source
RUN cd /uvmgr && uv pip install --system .

# Verify installation
RUN uvmgr --help

# Set up test environment
WORKDIR /test-projects

# Default command to show available commands
CMD ["uvmgr", "--help"]