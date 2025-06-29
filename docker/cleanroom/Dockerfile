# Cleanroom Docker Environment for DoD Validation
# ================================================
# 
# This Dockerfile creates a pristine environment for testing uvmgr's
# Definition of Done automation against external projects without
# any contamination from the host system.

FROM python:3.11-slim

# Set metadata
LABEL maintainer="uvmgr-team"
LABEL description="Cleanroom environment for DoD validation against external projects"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UVMGR_CLEANROOM=true
ENV UVMGR_VALIDATION_MODE=true

# Create non-root user for security
RUN groupadd -r uvmgr && useradd -r -g uvmgr -d /home/uvmgr -s /bin/bash uvmgr
RUN mkdir -p /home/uvmgr && chown -R uvmgr:uvmgr /home/uvmgr

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    build-essential \
    docker.io \
    nodejs \
    npm \
    openjdk-17-jdk \
    golang-go \
    rustc \
    && rm -rf /var/lib/apt/lists/*

# Install uv (Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Install Docker Compose
RUN curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
RUN chmod +x /usr/local/bin/docker-compose

# Create working directories
RUN mkdir -p /workdir/external-projects
RUN mkdir -p /workdir/validation-results
RUN mkdir -p /workdir/reports

# Copy uvmgr source for installation
COPY . /workdir/uvmgr-source/

# Switch to uvmgr user
USER uvmgr
WORKDIR /home/uvmgr

# Install uvmgr in the cleanroom environment
RUN cd /workdir/uvmgr-source && \
    /root/.cargo/bin/uv venv /home/uvmgr/.venv && \
    . /home/uvmgr/.venv/bin/activate && \
    /root/.cargo/bin/uv pip install -e .

# Add uvmgr to PATH
ENV PATH="/home/uvmgr/.venv/bin:$PATH"

# Create validation script
COPY docker/cleanroom/scripts/ /home/uvmgr/scripts/
RUN chmod +x /home/uvmgr/scripts/*.sh

# Set working directory for validation
WORKDIR /workdir

# Default command
CMD ["/home/uvmgr/scripts/run-validation.sh"]