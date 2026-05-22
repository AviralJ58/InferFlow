FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy workspace config
COPY pyproject.toml uv.lock* /app/

# Copy all packages for workspace members
COPY packages /app/packages

# Copy service dependencies
COPY apps/ingestion-worker/pyproject.toml apps/ingestion-worker/uv.lock* /app/apps/ingestion-worker/

WORKDIR /app/apps/ingestion-worker

# Install dependencies
RUN uv sync --frozen --no-dev 2>/dev/null || uv sync --no-dev

# Copy application code
COPY apps/ingestion-worker/worker /app/apps/ingestion-worker/worker

CMD ["uv", "run", "python", "-m", "worker.main"]
