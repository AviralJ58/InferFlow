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
COPY apps/monitoring-service/pyproject.toml apps/monitoring-service/uv.lock* /app/apps/monitoring-service/

WORKDIR /app/apps/monitoring-service

# Install dependencies
RUN uv sync --frozen --no-dev 2>/dev/null || uv sync --no-dev

# Copy application code
COPY apps/monitoring-service/app /app/apps/monitoring-service/app

EXPOSE 8001

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
