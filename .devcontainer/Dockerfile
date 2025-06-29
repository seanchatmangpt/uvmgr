FROM mcr.microsoft.com/devcontainers/python:3.12

# Install system dependencies for exponential capabilities testing
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    sudo \
    jq \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager as root first
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Use existing vscode user from base image
USER vscode

# Install UV for the user
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/vscode/.local/bin:$PATH"

# Set up workspace
WORKDIR /workspace

# Copy UV config for dependency caching
COPY pyproject.toml uv.lock* ./

# Dependencies will be installed at runtime from mounted workspace
# Activate virtual environment by default  
ENV PATH="/workspace/.venv/bin:/home/vscode/.cargo/bin:$PATH"
ENV VIRTUAL_ENV="/workspace/.venv"

# Set up shell with proper prompt
RUN echo 'export PS1="(uvmgr-dev) \u@\h:\w$ "' >> ~/.bashrc

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import uvmgr; print('uvmgr ready')" || exit 1