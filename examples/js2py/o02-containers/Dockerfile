# Runtime gate: actual image availability/build are not verified without an engine.
FROM python:3.13.15-slim-bookworm AS build
ENV UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /app
RUN python -m pip install --no-cache-dir --index-url https://pypi.org/simple uv==0.12.13
COPY .python-version pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-managed-python --python /usr/local/bin/python --default-index https://pypi.org/simple

FROM python:3.13.15-slim-bookworm AS runtime
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OPS_DATA_DIR=/data
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin app && mkdir /data && chown 10001:10001 /data
COPY --from=build /opt/venv /opt/venv
WORKDIR /app
COPY app.py config.py volume_probe.py healthcheck.py ./
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=3 CMD ["python", "healthcheck.py"]
CMD ["python", "-m", "uvicorn", "app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log", "--no-proxy-headers"]
