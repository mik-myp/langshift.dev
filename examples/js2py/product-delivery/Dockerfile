# Teaching baseline tags. Record/review immutable digests before release.
ARG PYTHON_IMAGE=python:3.13.15-slim-bookworm
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.12.13
FROM ${UV_IMAGE} AS uv
FROM ${PYTHON_IMAGE} AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project --no-editable \
    --no-managed-python --python /usr/local/bin/python \
    --default-index https://pypi.org/simple

FROM ${PYTHON_IMAGE} AS runtime
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN groupadd --gid 10001 product \
 && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin product
# Preserve the absolute environment path used by installed entry points.
COPY --from=build /opt/venv /opt/venv
WORKDIR /app
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=3 CMD ["python", "-m", "app.healthcheck"]
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log", "--no-proxy-headers"]
