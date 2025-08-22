.PHONY: help install dev test format lint clean

help: ## Show this help message
	@echo "Voice Summary - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies using uv
	uv sync

dev: ## Start development server
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8081

test: ## Run tests
	uv run pytest

format: ## Format code using black and isort
	uv run black .
	uv run isort .

lint: ## Run linting checks
	uv run flake8 .

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -delete

db-migrate: ## Run database migrations
	uv run alembic upgrade head

db-revision: ## Create new database migration
	uv run alembic revision --autogenerate -m "$(message)"

setup: ## Initial setup (install deps, run migrations)
	uv sync
	uv run alembic upgrade head
