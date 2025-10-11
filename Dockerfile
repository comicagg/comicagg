ARG TAG

FROM cr.nublar.net/comicagg/python:${TAG:-development}

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install distribution dependencies
RUN mkdir /app && \
    mkdir -p /web/media && \
    mkdir -p /web/static && \
    addgroup -S app && \
    adduser -s /bin/ash -S app -G app && \
    chown -R app:app /app && \
    chown -R app:app /web

COPY --chown=app:app src lib /app/
COPY --chown=app:app --chmod=744 ./entrypoint.sh /entrypoint.sh
COPY --chown=app:app --chmod=744 ./gunicorn.conf.py /gunicorn.conf.py

WORKDIR /app

USER app

# Django
EXPOSE 80
# Celery Flower dashboard
EXPOSE 8001

ENTRYPOINT [ "/entrypoint.sh" ]

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f -A "healthcheck/1" -H "Host:${DJANGO_SITE_DOMAIN}" http://localhost || exit 1
