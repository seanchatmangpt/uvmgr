# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS build

ENV UV_PROJECT_ENVIRONMENT=/opt/uvmgr \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

WORKDIR /src

# Native compilation belongs only to the build boundary.
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && \
    apt-get install --no-install-recommends --yes build-essential && \
    rm -rf /var/lib/apt/lists/*

# Lock metadata is copied before source so dependency installation can be cached.
COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync \
      --frozen \
      --no-dev \
      --no-editable \
      --python-preference only-system

FROM python:3.12-slim AS app

ENV PATH="/opt/uvmgr/bin:${PATH}" \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN groupadd --system --gid 10001 uvmgr && \
    useradd --system --create-home --gid 10001 --uid 10001 uvmgr

WORKDIR /home/uvmgr

# The runtime receives only the admitted virtual environment; compilers, uv,
# repository metadata, and build caches remain outside the production image.
COPY --from=build --chown=10001:10001 /opt/uvmgr /opt/uvmgr

USER 10001:10001

ENTRYPOINT ["/opt/uvmgr/bin/uvmgr"]
CMD []
