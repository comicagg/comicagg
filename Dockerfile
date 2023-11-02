###########
# BUILDER #
###########

# Pull official base image
FROM python:3.11-bookworm as builder

WORKDIR /tmp

COPY ./src/requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

#########
# Final #
#########

# Pull official base image
FROM python:3.11-bookworm as final

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /app

COPY --from=builder /usr/src/app/wheels /wheels

# RUN apt-get update && \
#     export DEBIAN_FRONTEND=noninteractive && \
#     apt-get -y install cron nano && \
#     update-rc.d cron defaults && \
# apt-get upgrade && \
# apt-get full-upgrade \
# Install dependencies from builder
# pip install --upgrade pip && \
RUN pip install --upgrade pip && \
    pip install --no-cache /wheels/* && \
    mkdir /app && \
    mkdir -p /web/media && \
    mkdir -p /web/static && \
    useradd app && \
    chown -R app:app /web

COPY --chown=app:app src lib /app/
COPY --chown=app:app ./entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//g' /entrypoint.sh

WORKDIR /app
USER app

EXPOSE 8000

ENTRYPOINT [ "bash", "/entrypoint.sh" ]
