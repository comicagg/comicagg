FROM python:3.12-bookworm

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Add entrypoint
COPY --chmod=744 .devcontainer/entrypoint.sh /entrypoint.sh
# Add requirements
COPY src/requirements.txt /
COPY .devcontainer/requirements.txt /requirements-dev.txt
RUN cat /requirements-dev.txt >> /requirements.txt \
    && pip3 --disable-pip-version-check --no-cache-dir install -r /requirements.txt \
# Update entrypoint
    # && sed -i 's/\r$//g' /entrypoint.sh \
    # && chmod +x /entrypoint.sh \
# Install additional OS packages.
    && apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends gettext
