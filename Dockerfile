# ==========================================
# Stage 1: Builder Stage
# ==========================================
FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Suppress progress bars in build logs
ENV UV_NO_PROGRESS=1
# Compile Python bytecode for faster startup
ENV UV_COMPILE_BYTECODE=1
# Recommended when using cache mounts
ENV UV_LINK_MODE=copy

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-install-project --no-dev

COPY src/ ./src/

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-dev

# ==========================================
# Stage 2: Runtime Stage
# ==========================================
FROM python:3.14-slim AS app

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src"

RUN groupadd --system --gid 999 app \
    && useradd --system --gid 999 --uid 999 --create-home app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

RUN mkdir -p /web/media && \
    mkdir -p /web/static && \
    chown -R app:app /app && \
    chown -R app:app /web

# COPY --chown=app:app src lib /app/
COPY --chown=app:app --chmod=744 ./entrypoint.sh /entrypoint.sh
COPY --chown=app:app --chmod=744 ./gunicorn.conf.py /gunicorn.conf.py

USER app

# Django
EXPOSE 80
# Celery Flower dashboard
EXPOSE 8001

ENTRYPOINT [ "/entrypoint.sh" ]

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f -A "healthcheck/1" -H "Host:${DJANGO_SITE_DOMAIN}" http://localhost || exit 1
