SHELL = /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
.DEFAULT_GOAL := help

# Load environment variables
ifneq (,$(wildcard ./.env))
    include .env
    export $(shell sed 's/=.*//' .env)
endif

export PYTHONPATH

# Tools
UV := uv
DOCKER_COMPOSE := docker compose

# Paths
APP_DIR := backend
POSTGRES_COMMAND := /Applications/Postgres.app/Contents/Versions/latest/bin

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color

.PHONY: help
help: ## Show available targets
	@echo ""
	@echo "$(BLUE)Django REST Boilerplate$(NC)"
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# =============================================================================
# INSTALLATION
# =============================================================================

.PHONY: install
install: ## Install uv and project dependencies
	@echo "$(GREEN)Installing uv...$(NC)"
	@command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh
	@echo "$(GREEN)Installing project dependencies...$(NC)"
	$(UV) sync

.PHONY: install-dev
install-dev: ## Install development dependencies
	@echo "$(GREEN)Installing development dependencies...$(NC)"
	$(UV) sync --all-extras

.PHONY: lock
lock: ## Lock dependencies
	@echo "$(GREEN)Locking dependencies...$(NC)"
	$(UV) lock

.PHONY: update
update: ## Update all dependencies
	@echo "$(GREEN)Updating dependencies...$(NC)"
	$(UV) lock --upgrade
	$(UV) sync --all-extras

.PHONY: copy-env
copy-env: ## Copy environment example file
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)Created .env file$(NC)"; \
	else \
		echo "$(YELLOW).env file already exists$(NC)"; \
	fi

# =============================================================================
# DATABASE (Local)
# =============================================================================

.PHONY: create-db-linux
create-db-linux: ## Create a local database on Linux
	@echo "$(GREEN)Creating database on Linux...$(NC)"
	sudo -u postgres psql -c 'CREATE DATABASE $(DATABASE_NAME);'
	sudo -u postgres psql -c 'GRANT ALL PRIVILEGES ON DATABASE $(DATABASE_NAME) TO $(DATABASE_USERNAME);'

.PHONY: create-db-mac
create-db-mac: ## Create a local database on Mac
	@echo "$(GREEN)Creating database on Mac...$(NC)"
	sudo mkdir -p /etc/paths.d && \
	echo $(POSTGRES_COMMAND) | sudo tee /etc/paths.d/postgresapp
	sudo $(POSTGRES_COMMAND)/psql -U postgres -c 'CREATE DATABASE $(DATABASE_NAME);'
	sudo $(POSTGRES_COMMAND)/psql -U postgres -c 'GRANT ALL PRIVILEGES ON DATABASE $(DATABASE_NAME) TO $(DATABASE_USERNAME);'

.PHONY: drop-db-linux
drop-db-linux: ## Drop a local database on Linux
	@echo "$(RED)Dropping database on Linux...$(NC)"
	sudo -u postgres psql -c 'DROP DATABASE IF EXISTS $(DATABASE_NAME);'

.PHONY: drop-db-mac
drop-db-mac: ## Drop a local database on Mac
	@echo "$(RED)Dropping database on Mac...$(NC)"
	sudo $(POSTGRES_COMMAND)/psql -U postgres -c 'DROP DATABASE IF EXISTS $(DATABASE_NAME);'

# =============================================================================
# LOCAL DEVELOPMENT
# =============================================================================

.PHONY: run
run: ## Run the local development server with uvicorn
	@echo "$(GREEN)Starting development server...$(NC)"
	cd $(APP_DIR) && $(UV) run uvicorn server.asgi:application --host 0.0.0.0 --port 8000 --reload

.PHONY: run-gunicorn
run-gunicorn: ## Run with gunicorn + uvicorn workers locally
	@echo "$(GREEN)Starting gunicorn with uvicorn workers...$(NC)"
	cd $(APP_DIR) && $(UV) run gunicorn server.asgi:application \
		--bind 0.0.0.0:8000 \
		--worker-class uvicorn.workers.UvicornWorker \
		--workers 2 \
		--reload

.PHONY: run-local
run-local: migrate run ## Run migrations and start the local development server

# =============================================================================
# CELERY
# =============================================================================

.PHONY: celery-worker
celery-worker: ## Run Celery worker locally
	@echo "$(GREEN)Starting Celery worker...$(NC)"
	cd $(APP_DIR) && $(UV) run celery -A server worker -l INFO

.PHONY: celery-beat
celery-beat: ## Run Celery beat scheduler locally
	@echo "$(GREEN)Starting Celery beat...$(NC)"
	cd $(APP_DIR) && $(UV) run celery -A server beat -l INFO

.PHONY: celery-flower
celery-flower: ## Run Flower monitoring locally
	@echo "$(GREEN)Starting Flower...$(NC)"
	cd $(APP_DIR) && $(UV) run celery -A server flower --port=5555

.PHONY: celery-all
celery-all: ## Run all Celery services (worker, beat, flower) - requires multiple terminals
	@echo "$(YELLOW)Run these commands in separate terminals:$(NC)"
	@echo "  make celery-worker"
	@echo "  make celery-beat"
	@echo "  make celery-flower"

.PHONY: celery-worker-docker
celery-worker-docker: ## View Celery worker logs in Docker
	$(DOCKER_COMPOSE) logs -f celery-worker

.PHONY: celery-beat-docker
celery-beat-docker: ## View Celery beat logs in Docker
	$(DOCKER_COMPOSE) logs -f celery-beat

.PHONY: celery-purge
celery-purge: ## Purge all Celery tasks
	@echo "$(YELLOW)Purging all Celery tasks...$(NC)"
	cd $(APP_DIR) && $(UV) run celery -A server purge -f

.PHONY: celery-inspect
celery-inspect: ## Inspect active Celery workers
	@echo "$(GREEN)Inspecting Celery workers...$(NC)"
	cd $(APP_DIR) && $(UV) run celery -A server inspect active

.PHONY: celery-events
celery-events: ## Monitor Celery events in real-time
	@echo "$(GREEN)Monitoring Celery events...$(NC)"
	cd $(APP_DIR) && $(UV) run celery -A server events

# =============================================================================
# TESTING
# =============================================================================

.PHONY: test
test: ## Run tests
	@echo "$(GREEN)Running tests...$(NC)"
	$(UV) run pytest $(APP_DIR) -v

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	$(UV) run pytest $(APP_DIR) --cov=$(APP_DIR) --cov-report=html --cov-report=term-missing

.PHONY: test-fast
test-fast: ## Run tests without coverage (faster)
	@echo "$(GREEN)Running tests (fast mode)...$(NC)"
	$(UV) run pytest $(APP_DIR) -v -x --tb=short

.PHONY: test-watch
test-watch: ## Run tests in watch mode
	@echo "$(GREEN)Running tests in watch mode...$(NC)"
	$(UV) run pytest-watch $(APP_DIR)

# =============================================================================
# CODE QUALITY
# =============================================================================

.PHONY: format
format: ## Format code with ruff
	@echo "$(GREEN)Formatting code...$(NC)"
	$(UV) run ruff format $(APP_DIR)
	$(UV) run ruff check $(APP_DIR) --fix

.PHONY: format-check
format-check: ## Check code formatting with ruff
	@echo "$(GREEN)Checking code format...$(NC)"
	$(UV) run ruff format $(APP_DIR) --check
	$(UV) run ruff check $(APP_DIR)

.PHONY: lint
lint: ## Lint code with ruff
	@echo "$(GREEN)Linting code...$(NC)"
	$(UV) run ruff check $(APP_DIR)

.PHONY: lint-fix
lint-fix: ## Lint and fix code with ruff
	@echo "$(GREEN)Linting and fixing code...$(NC)"
	$(UV) run ruff check $(APP_DIR) --fix

.PHONY: typecheck
typecheck: ## Run mypy type checking
	@echo "$(GREEN)Running type checks...$(NC)"
	$(UV) run mypy $(APP_DIR)

.PHONY: check
check: format-check lint typecheck ## Run all code quality checks

.PHONY: check-fix
check-fix: format lint-fix ## Format and fix all code issues

.PHONY: pre-commit
pre-commit: ## Run pre-commit hooks on all files
	@echo "$(GREEN)Running pre-commit hooks...$(NC)"
	$(UV) run pre-commit run --all-files

.PHONY: pre-commit-install
pre-commit-install: ## Install pre-commit hooks
	@echo "$(GREEN)Installing pre-commit hooks...$(NC)"
	$(UV) run pre-commit install

# =============================================================================
# DOCKER - DEVELOPMENT
# =============================================================================

.PHONY: up
up: ## Build and start Docker containers
	@echo "$(GREEN)Starting Docker containers...$(NC)"
	$(DOCKER_COMPOSE) up -d --build

.PHONY: watch
watch: ## Start Docker containers with watch mode (auto-reload)
	@echo "$(GREEN)Starting Docker containers with watch mode...$(NC)"
	$(DOCKER_COMPOSE) up --build --watch

.PHONY: down
down: ## Stop and remove Docker containers
	@echo "$(YELLOW)Stopping Docker containers...$(NC)"
	$(DOCKER_COMPOSE) down

.PHONY: down-v
down-v: ## Stop and remove Docker containers with volumes
	@echo "$(RED)Stopping Docker containers and removing volumes...$(NC)"
	$(DOCKER_COMPOSE) down -v

.PHONY: restart
restart: down up ## Restart Docker containers

.PHONY: logs
logs: ## View Docker container logs
	$(DOCKER_COMPOSE) logs -f

.PHONY: logs-backend
logs-backend: ## View backend container logs
	$(DOCKER_COMPOSE) logs -f backend

.PHONY: shell-docker
shell-docker: ## Open a shell in the backend container
	$(DOCKER_COMPOSE) exec backend bash

.PHONY: test-docker
test-docker: ## Run tests inside Docker containers
	@echo "$(GREEN)Running tests in Docker...$(NC)"
	$(DOCKER_COMPOSE) exec backend pytest -v

.PHONY: migrate-docker
migrate-docker: ## Run migrations in Docker
	$(DOCKER_COMPOSE) exec backend python $(APP_DIR)/manage.py migrate

.PHONY: makemigrations-docker
makemigrations-docker: ## Create migrations in Docker
	$(DOCKER_COMPOSE) exec backend python $(APP_DIR)/manage.py makemigrations

# =============================================================================
# DOCKER - DEBUG
# =============================================================================

.PHONY: debug-up
debug-up: ## Start debug Docker containers with watch mode
	@echo "$(GREEN)Starting debug containers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose-debug.yml up --build --watch

.PHONY: debug-down
debug-down: ## Stop debug Docker containers
	@echo "$(YELLOW)Stopping debug containers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose-debug.yml down -v

# =============================================================================
# DOCKER - PRODUCTION
# =============================================================================

.PHONY: prod-up
prod-up: ## Build and start production Docker containers
	@echo "$(GREEN)Starting production containers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml up -d --build

.PHONY: prod-down
prod-down: ## Stop and remove production Docker containers
	@echo "$(YELLOW)Stopping production containers...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml down

.PHONY: prod-down-v
prod-down-v: ## Stop production containers and remove volumes
	@echo "$(RED)Stopping production containers and removing volumes...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml down -v

.PHONY: prod-logs
prod-logs: ## View production Docker container logs
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml logs -f

.PHONY: prod-migrate
prod-migrate: ## Run migrations in production
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml exec backend python $(APP_DIR)/manage.py migrate

.PHONY: prod-shell
prod-shell: ## Open a shell in production backend container
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml exec backend bash

.PHONY: prod-restart
prod-restart: prod-down prod-up ## Restart production containers

# =============================================================================
# SSL / CERTBOT
# =============================================================================

.PHONY: ssl-init
ssl-init: ## Initialize Let's Encrypt SSL certificates
	@echo "$(GREEN)Initializing SSL certificates...$(NC)"
	chmod +x scripts/init-letsencrypt.sh
	./scripts/init-letsencrypt.sh

.PHONY: ssl-renew
ssl-renew: ## Manually renew SSL certificates
	@echo "$(GREEN)Renewing SSL certificates...$(NC)"
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml run --rm certbot renew

# =============================================================================
# AWS DEPLOYMENT
# =============================================================================

.PHONY: aws-login
aws-login: ## Login to AWS ECR
	@echo "$(GREEN)Logging into AWS ECR...$(NC)"
	aws ecr get-login-password --region $(AWS_REGION) | docker login \
		--username AWS --password-stdin \
		$(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com

.PHONY: aws-build
aws-build: ## Build Docker image for AWS
	@echo "$(GREEN)Building Docker image for AWS...$(NC)"
	docker build -t $(AWS_ACCOUNT_URI):latest -f docker/backend/Dockerfile.prod .

.PHONY: aws-push
aws-push: aws-login aws-build ## Build and push Docker image to AWS ECR
	@echo "$(GREEN)Pushing Docker image to AWS ECR...$(NC)"
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/django-app:latest

# =============================================================================
# UTILITIES
# =============================================================================

.PHONY: clean
clean: ## Clean up cache and build files
	@echo "$(YELLOW)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete$(NC)"

.PHONY: clean-docker
clean-docker: ## Remove all Docker containers, images, and volumes
	@echo "$(RED)Cleaning Docker resources...$(NC)"
	docker system prune -af --volumes

.PHONY: status
status: ## Show status of Docker containers
	$(DOCKER_COMPOSE) ps

.PHONY: health
health: ## Check health of services
	@echo "$(GREEN)Checking service health...$(NC)"
	@echo "\n$(BLUE)Docker containers:$(NC)"
	@$(DOCKER_COMPOSE) ps
	@echo "\n$(BLUE)Database:$(NC)"
	@$(DOCKER_COMPOSE) exec db pg_isready -U $(DATABASE_USERNAME) || echo "$(RED)Database not ready$(NC)"
	@echo "\n$(BLUE)Valkey:$(NC)"
	@$(DOCKER_COMPOSE) exec valkey valkey-cli ping || echo "$(RED)Valkey not ready$(NC)"

.PHONY: info
info: ## Show project info
	@echo ""
	@echo "$(BLUE)Project Information$(NC)"
	@echo "===================="
	@echo "Python version: $$(python --version 2>&1)"
	@echo "uv version: $$(uv --version 2>&1)"
	@echo "Docker version: $$(docker --version 2>&1)"
	@echo "Docker Compose version: $$(docker compose version 2>&1)"
	@echo ""
	@echo "$(BLUE)Environment$(NC)"
	@echo "===================="
	@echo "DATABASE_NAME: $(DATABASE_NAME)"
	@echo "DATABASE_HOST: $(DATABASE_HOST)"
	@echo "DEBUG: $(DEBUG)"
	@echo ""
