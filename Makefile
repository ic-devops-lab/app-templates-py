# Makefile for Python projects using 'uv' for dependency management
# Adjust the parameters below to fit your project.

# ---------- Environment ----------
# include .env 				# uncomment if the file present
ENV_FILE            := .env

# ---------- Project parameters ----------
# Here you can set app-specific parameters, e.g.:
# APP_MODULE					:= py_app_tmpl.main:app
# HOST                := 0.0.0.0
# PORT                := $(or $(APP_PORT),8000)

# Tools
UV                  := uv
RUN                 := $(UV) run          # <— use the project's venv
RUN_LOCKED          := $(RUN) --locked		# run with locked dependencies
RUFF                := $(RUN_LOCKED) ruff	# ruff
MYPY                := $(RUN_LOCKED) mypy	# mypy
PYTEST              := $(RUN_LOCKED) pytest	# pytest
BANDIT              := $(RUN_LOCKED) bandit	# bandit

# ---------- Housekeeping ----------
.PHONY: help

SHELL := bash

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "• \033[36m%-18s\033[0m %s\n", $$1, $$2}'

env: ## Create .env from .env.example if missing
	@if [ ! -f $(ENV_FILE) ]; then cp .env.example $(ENV_FILE); echo "Created $(ENV_FILE)"; else echo "$(ENV_FILE) already exists"; fi

check: ## Quick sanity checks
	@command -v uv >/dev/null || { echo "Missing 'uv'"; exit 1; }
	@command -v uv ruff >/dev/null || { echo "Missing 'ruff'"; exit 1; }
	@command -v uv mypy >/dev/null || { echo "Missing 'mypy'"; exit 1; }
	@command -v uv pytest >/dev/null || { echo "Missing 'pytest'"; exit 1; }
	@command -v uv bandit >/dev/null || { echo "Missing 'bandit'"; exit 1; }
	@echo "Tools OK."

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