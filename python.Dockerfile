ARG PY_VERSION="3.14"

###########
# BUILDER #
###########

# Pull official base image
FROM python:${PY_VERSION}-alpine AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.12 /uv /uvx /bin/

WORKDIR /tmp

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install deps
RUN apk update && \
    apk add gcc libpq-dev postgresql-dev python3-dev musl-dev

# Export the locked runtime and debug dependencies, then build wheels.
COPY ./pyproject.toml ./uv.lock ./
RUN uv export --locked --no-dev --no-default-groups --group debug --group postgres \
    --no-emit-project --format requirements-txt --output-file requirements.txt && \
    pip wheel --no-cache-dir --wheel-dir /usr/src/app/wheels -r requirements.txt

#########
# Final #
#########

ARG PY_VERSION

# Pull official base image
FROM python:${PY_VERSION}-alpine AS final

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --from=builder /usr/src/app/wheels /wheels

# Install distribution dependencies
RUN apk update && \
    apk add libpq curl gettext envsubst && \
    # Install Python dependencies
    pip install --upgrade pip && \
    pip install --no-cache /wheels/*
