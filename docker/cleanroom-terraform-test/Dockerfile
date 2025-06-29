FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Terraform
RUN wget https://releases.hashicorp.com/terraform/1.6.6/terraform_1.6.6_linux_amd64.zip \
    && unzip terraform_1.6.6_linux_amd64.zip \
    && mv terraform /usr/local/bin/ \
    && rm terraform_1.6.6_linux_amd64.zip

# Set working directory
WORKDIR /app

# Copy uvmgr source code
COPY . /app/

# Install uvmgr and dependencies using pip
RUN pip install --no-cache-dir -e .

# Create test workspace
WORKDIR /test-workspace

# Copy test scripts
COPY docker/cleanroom-terraform-test/scripts/ /test-scripts/
RUN chmod +x /test-scripts/*.sh

# Set environment variables for testing
ENV PYTHONPATH="/app/src"
ENV OTEL_RESOURCE_ATTRIBUTES="service.name=uvmgr-terraform-test,service.version=cleanroom"
ENV OTEL_SERVICE_NAME="uvmgr-terraform-test"

# Default command runs the validation suite
CMD ["/test-scripts/run-cleanroom-tests.sh"]