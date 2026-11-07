FROM python:3.14-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.12.12 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Add entrypoint
COPY --chmod=744 .devcontainer/entrypoint.sh /entrypoint.sh
COPY pyproject.toml uv.lock /opt/comicagg/
WORKDIR /opt/comicagg
ENV PATH="/opt/comicagg/.venv/bin:$PATH"
RUN uv sync --locked --no-install-project --group debug \
    && apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y dist-upgrade \
    && apt-get -y install --no-install-recommends gettext gnupg2
