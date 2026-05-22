FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy shared package first (dependency)
COPY packages/shared /packages/shared

# Copy service files
COPY apps/ingestion-worker/pyproject.toml apps/ingestion-worker/uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-dev 2>/dev/null || uv sync --no-dev

# Copy application code
COPY apps/ingestion-worker/worker ./worker

CMD ["uv", "run", "python", "-m", "worker.main"]
