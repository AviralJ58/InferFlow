.PHONY: run build lint format docker-up docker-down install clean help

# ==========================
# InferFlow — Makefile
# ==========================

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --------------------------
# Development
# --------------------------

install: ## Install all dependencies
	@echo "→ Installing frontend dependencies..."
	cd apps/frontend && npm install
	@echo "→ Installing Python dependencies..."
	cd apps/chat-service && uv sync
	cd apps/ingestion-worker && uv sync
	cd apps/monitoring-service && uv sync
	@echo "✓ All dependencies installed."

run: ## Run all services locally (requires tmux or multiple terminals)
	@echo "Start each service individually:"
	@echo "  make run-frontend"
	@echo "  make run-chat"
	@echo "  make run-ingestion"
	@echo "  make run-monitoring"

run-frontend: ## Run frontend dev server
	cd apps/frontend && npm run dev

run-chat: ## Run chat service
	cd apps/chat-service && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-ingestion: ## Run ingestion worker
	cd apps/ingestion-worker && uv run python -m worker.main

run-monitoring: ## Run monitoring service
	cd apps/monitoring-service && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# --------------------------
# Code Quality
# --------------------------

lint: ## Lint all Python services
	cd apps/chat-service && uv run ruff check .
	cd apps/ingestion-worker && uv run ruff check .
	cd apps/monitoring-service && uv run ruff check .

format: ## Format all Python services
	cd apps/chat-service && uv run ruff format .
	cd apps/ingestion-worker && uv run ruff format .
	cd apps/monitoring-service && uv run ruff format .

# --------------------------
# Build
# --------------------------

build: ## Build all Docker images
	docker compose build

build-frontend: ## Build frontend for production
	cd apps/frontend && npm run build

# --------------------------
# Docker
# --------------------------

docker-up: ## Start all services via Docker Compose
	docker compose up -d

docker-down: ## Stop all Docker Compose services
	docker compose down

docker-logs: ## Tail logs from all services
	docker compose logs -f

docker-restart: ## Restart all services
	docker compose down && docker compose up -d

# --------------------------
# Cleanup
# --------------------------

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf apps/frontend/dist apps/frontend/node_modules
	@echo "✓ Cleaned."
