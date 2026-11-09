# Makefile for Python projects using 'uv' for dependency management
# Adjust the parameters below to fit your project.

# ---------- Environment ----------
# include .env 				# uncomment if the file present
ENV_FILE            := .env
# Load optional .env configuration
ifneq (,$(wildcard $(ENV_FILE)))
include $(ENV_FILE)
endif

# ---------- Project parameters ----------
# Here you can set app-specific parameters, e.g.:
# APP_MODULE					:= py_app_tmpl.main:app
# HOST                := 0.0.0.0
# PORT                := $(or $(APP_PORT),8000)

IMAGE_NAME       		?= py-app-tmpl
IMAGE_TAG        		?= dev
IMAGE            		:= $(IMAGE_NAME):$(IMAGE_TAG)

TRIVY_SEVERITY   		?= HIGH,CRITICAL

# Tools
UV                  := uv
RUN                 := $(UV) run          	# <— use the project's venv
RUN_LOCKED          := $(RUN) --locked			# run with locked dependencies
RUFF                := $(RUN_LOCKED) ruff		# ruff
MYPY                := $(RUN_LOCKED) mypy		# mypy
PYTEST              := $(RUN_LOCKED) pytest	# pytest
BANDIT              := $(RUN_LOCKED) bandit	# bandit
COMPOSE							:= docker compose				# docker compose
TRIVY               := trivy								# trivy

# ---------- Housekeeping ----------
.PHONY: help

SHELL := bash

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "• \033[36m%-18s\033[0m %s\n", $$1, $$2}'

env: ## Create .env from .env.example if missing
	@if [ ! -f $(ENV_FILE) ]; then cp .env.example $(ENV_FILE); echo "Created $(ENV_FILE)"; else echo "$(ENV_FILE) already exists"; fi

check: ## Check local Python development prerequisites
	@command -v uv >/dev/null || { echo "Missing 'uv'"; exit 1; }
	@$(UV) run --locked ruff --version >/dev/null
	@$(UV) run --locked mypy --version >/dev/null
	@$(UV) run --locked pytest --version >/dev/null
	@$(UV) run --locked bandit --version >/dev/null
	@echo "Python development tools OK."

check-container: ## Check container development prerequisites
	@command -v docker >/dev/null || { echo "Missing 'docker'"; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "Docker daemon unavailable"; exit 1; }
	@docker compose version >/dev/null || { echo "Docker Compose unavailable"; exit 1; }
	@command -v trivy >/dev/null || { echo "Missing 'trivy'"; exit 1; }
	@echo "Container tools OK."

check-all: ## Check all development prerequisites
	@$(MAKE) check
	@$(MAKE) check-container

# ---------- Build ----------
build: ## build wheel and source distributions
	@$(UV) build

# ---------- Code quality ----------
fmt: ## Auto-format with ruff
	@$(RUFF) format

fmt-check: ## Check code style with ruff
	@$(RUFF) format --check .

lint: ## Lint with ruff
	@$(RUFF) check .

type: ## Static type-check of the whole project with mypy
	@$(MYPY) .

type-app: ## Static type-check of the app code with mypy
	@$(MYPY) src/py_app_tmpl

test: ## Run unit tests
	@$(PYTEST) -v

cov: ## Run tests with coverage
	@$(PYTEST) --cov=py_app_tmpl --cov-report=term-missing -v

sast: ## Run static analysis (bandit)
	@$(RUN_LOCKED) bandit -rv src/py_app_tmpl

ci: ## run local CI pipeline
	@$(MAKE) check
	@$(MAKE) fmt-check
	@$(MAKE) lint
	@$(MAKE) type
	@$(MAKE) sast
	@$(MAKE) cov
	@$(MAKE) build

# ---------- Run (local code) ----------
# Define run command for your app in the Makefile here
run: ## Run the app
	@$(RUN_LOCKED) py-app-tmpl


# ---------- Docker Compose ----------

docker-build: ## Build the application image
	@$(COMPOSE) build app

docker-run: ## Run the application in a temporary container
	@$(COMPOSE) run --rm app

docker-down: ## Stop and remove Compose-managed containers
	@$(COMPOSE) down

# ---------- Container security ----------
docker-scan: ## Scan image for HIGH and CRITICAL vulnerabilities
	@$(TRIVY) image \
		--scanners vuln \
		--severity $(TRIVY_SEVERITY) \
		--exit-code 1 \
		$(IMAGE)
# add `--exit-code 1` option to fail the test if vulnerabilities are found


docker-ci: check-container ## Build and scan the application image
	@$(MAKE) docker-build
	@$(MAKE) docker-scan