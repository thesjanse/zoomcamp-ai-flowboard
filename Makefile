API_PORT ?= 5000
FRONTEND_PORT ?= 22152
BUILD_PORT ?= 22153
BASE_PATH ?= /

PACKAGE ?= @workspace/kanban-board

API_SERVER_DIR := backend/api-server

.PHONY: help install dev run dev-backend dev-frontend typecheck build test test-backend test-frontend db-push

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install backend (uv) and frontend (pnpm) dependencies
	pnpm install
	$(MAKE) install-backend

install-backend: ## Install backend dependencies (uv sync)
	cd $(API_SERVER_DIR) && uv sync

dev: ## Run backend and frontend dev servers together
	$(MAKE) dev-backend & \
	trap 'kill 0' INT TERM EXIT; \
	$(MAKE) dev-frontend

run: dev ## Alias for `make dev` (run the full stack)

dev-backend: ## Run the backend (FastAPI) dev server
	cd $(API_SERVER_DIR) && uv run uvicorn app.main:app --host 0.0.0.0 --port $(API_PORT)

dev-frontend: ## Run the frontend (Vite) dev server
	PORT=$(FRONTEND_PORT) BASE_PATH=$(BASE_PATH) pnpm --filter $(PACKAGE) run dev

typecheck: ## Typecheck all packages
	pnpm run typecheck

build: ## Typecheck + build all packages
	PORT=$(BUILD_PORT) BASE_PATH=$(BASE_PATH) pnpm run build

test: ## Run backend and frontend tests
	$(MAKE) test-backend
	$(MAKE) test-frontend

test-backend: ## Run backend tests (pytest)
	cd $(API_SERVER_DIR) && uv run pytest

test-frontend: ## Run frontend tests (vitest)
	pnpm --filter $(PACKAGE) run test

db-push: ## Push DB schema changes (dev only; requires DATABASE_URL)
	pnpm --filter @workspace/db run push