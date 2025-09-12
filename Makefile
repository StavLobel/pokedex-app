.PHONY: help venv install install-prod dev test lint format clean clean-venv docker-build docker-up docker-down setup activate check-venv

# Virtual environment settings
VENV_DIR = backend/venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
PYTEST = $(VENV_DIR)/bin/pytest
BLACK = $(VENV_DIR)/bin/black
ISORT = $(VENV_DIR)/bin/isort
FLAKE8 = $(VENV_DIR)/bin/flake8
MYPY = $(VENV_DIR)/bin/mypy

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

venv: ## Create virtual environment
	cd backend && python3 -m venv venv
	$(PIP) install --upgrade pip setuptools wheel

install: venv ## Install backend dependencies (including dev dependencies)
	$(PIP) install -r backend/requirements.txt
	$(PIP) install -r backend/requirements-dev.txt

install-prod: venv ## Install production dependencies only
	$(PIP) install -r backend/requirements.txt

dev: ## Run development server
	$(PYTHON) backend/run_dev.py

test: ## Run tests
	$(PYTEST)

test-cov: ## Run tests with coverage
	$(PYTEST) --cov=app --cov-report=html

lint: ## Run linting
	$(FLAKE8) backend/app backend/tests
	$(MYPY) backend/app

format: ## Format code
	$(BLACK) backend/app backend/tests
	$(ISORT) backend/app backend/tests

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf backend/htmlcov
	rm -rf backend/.coverage
	rm -rf backend/.pytest_cache

clean-venv: ## Remove virtual environment
	rm -rf $(VENV_DIR)

docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-shell: ## Open shell in backend container
	docker-compose exec backend bash

setup: ## Run initial setup
	./setup.sh

activate: ## Show command to activate virtual environment
	@echo "To activate the virtual environment, run:"
	@echo "source backend/venv/bin/activate"

check-venv: ## Check if virtual environment exists
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "✅ Virtual environment exists at $(VENV_DIR)"; \
	else \
		echo "❌ Virtual environment not found. Run 'make install' to create it."; \
	fi