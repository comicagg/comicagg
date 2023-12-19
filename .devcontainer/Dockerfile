FROM python:3.12-bookworm

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# [Optional] If your requirements rarely change, uncomment this section to add them to the image.
COPY src/requirements.txt /
COPY .devcontainer/requirements.txt /requirements-dev.txt
RUN cat /requirements-dev.txt >> /requirements.txt \
    && pip3 --disable-pip-version-check --no-cache-dir install -r /requirements.txt

COPY .devcontainer/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//g' /entrypoint.sh && \
    chmod +x /entrypoint.sh

# [Optional] Uncomment this section to install additional OS packages.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends gettext
