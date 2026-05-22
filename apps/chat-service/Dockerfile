FROM python:3.11-slim

# Prevent Python from writing pyc files and buffering stdout
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
COPY apps/chat-service/pyproject.toml apps/chat-service/uv.lock* /app/apps/chat-service/

# Set working directory for dependency installation
WORKDIR /app/apps/chat-service

# Install dependencies (frozen if lock exists)
RUN uv sync --frozen --no-dev 2>/dev/null || uv sync --no-dev

# Copy application code
COPY apps/chat-service/app /app/apps/chat-service/app

EXPOSE 8000

# We use uvicorn for production by default.
# The docker-compose.yml overrides this for local dev with --reload.
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
