ARG PY_VERSION="3.12"

###########
# BUILDER #
###########

# Pull official base image
FROM python:${PY_VERSION}-alpine as builder

WORKDIR /tmp

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install deps
RUN apk update && \
    apk add curl gettext && \
    apk add gcc libpq-dev postgresql-dev python3-dev musl-dev

# Install dependencies
COPY ./src/requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt && \
    pip wheel --no-cache-dir --wheel-dir /usr/src/app/wheels psycopg[c]

#########
# Final #
#########

ARG PY_VERSION

# Pull official base image
FROM python:${PY_VERSION}-alpine as final

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY --from=builder /usr/src/app/wheels /wheels

# Install distribution dependencies
RUN apk update && \
    apk add libpq && \
    # Install Python dependencies
    pip install --upgrade pip && \
    pip install --no-cache /wheels/* && \
    # Build filesystem items
    mkdir /app && \
    mkdir -p /web/media && \
    mkdir -p /web/static && \
    addgroup -S app && \
    adduser -s /bin/ash -S app -G app && \
    chown -R app:app /web

COPY --chown=app:app src lib /app/
COPY --chown=app:app ./entrypoint.sh /entrypoint.sh

WORKDIR /app
USER app

EXPOSE 8000

ENTRYPOINT [ "/entrypoint.sh" ]
