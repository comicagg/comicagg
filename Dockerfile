ARG TAG

# Pull official base image
FROM nublar.azurecr.io/comicagg/python:${TAG:-development}

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install distribution dependencies
RUN mkdir /app && \
    mkdir -p /web/media && \
    mkdir -p /web/static && \
    addgroup -S app && \
    adduser -s /bin/ash -S app -G app && \
    chown -R app:app /web

COPY --chown=app:app src lib /app/
COPY --chown=app:app --chmod=744 ./entrypoint.sh /entrypoint.sh
COPY --chown=app:app --chmod=744 ./gunicorn.conf.py /gunicorn.conf.py

WORKDIR /app

USER app

# Django
EXPOSE 8000
# Celery Flower dashboard
EXPOSE 8001

ENTRYPOINT [ "/entrypoint.sh" ]
