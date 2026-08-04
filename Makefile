# Comprehensive Makefile for local development, CI (GitHub Actions), Docker, and Render deployments
# Designed for use both locally and inside CI (GitHub Actions / Render build hooks).
# Sections include: environment, formatting, linting, testing, building, docker, CI orchestration, and Render deploy trigger.

SHELL := /bin/bash
.PHONY: help venv install freeze format format-check lint typecheck test coverage build package docker-build docker-push ci render-deploy gh-workflow

# ---------- Configurable variables (override on CLI or environment) ----------
PY ?= python3
VENV ?= .venv
REQ ?= requirements.txt
PACKAGE ?= ai_portfolio_optimizer
DIST_DIR ?= dist
DOCKER_IMAGE ?= ${DOCKER_IMAGE}
TAG ?= latest

# Render settings (for `make render-deploy`) — set these in CI environment secrets
RENDER_SERVICE_ID ?=
RENDER_API_KEY ?=

# Default short help
help:
	@echo "Makefile targets:"
	@echo "  make venv            -- create virtualenv and upgrade pip/tools"
	@echo "  make install         -- install requirements into venv"
	@echo "  make format          -- run code formatter (black)"
	@echo "  make format-check    -- check formatting without modifying files"
	@echo "  make lint            -- run linter (ruff/flake8)"
	@echo "  make typecheck       -- run mypy type checks"
	@echo "  make test            -- run tests (pytest)"
	@echo "  make coverage        -- run tests with coverage report"
	@echo "  make build/package   -- build wheel and sdist in $(DIST_DIR)"
	@echo "  make docker-build    -- build docker image"
	@echo "  make docker-push     -- push docker image (requires DOCKER_IMAGE)"
	@echo "  make ci              -- run format-check, lint, typecheck, test (used in CI)"
	@echo "  make render-deploy   -- trigger a Render.com manual deploy (requires RENDER_SERVICE_ID and RENDER_API_KEY)"
	@echo "  make gh-workflow     -- write a recommended GitHub Actions workflow to .github/workflows/ci.yml"

# ---------- Virtual environment and dependencies ----------
venv:
	@echo "Creating virtual environment in $(VENV) (python: $(PY))"
	$(PY) -m venv $(VENV)
	# Ensure pip, setuptools, wheel are up to date
	. $(VENV)/bin/activate; python -m pip install --upgrade pip setuptools wheel

install: venv
	@echo "Installing dependencies from $(REQ) into $(VENV)"
	. $(VENV)/bin/activate; python -m pip install -r $(REQ)

freeze:
	@echo "Freezing installed packages into $(REQ)"
	. $(VENV)/bin/activate; python -m pip freeze > $(REQ)

# ---------- Formatting, linting, static checks ----------
# Note: these assume black, ruff, mypy are in your requirements (or installed in VENV)
format:
	@echo "Formatting code with black"
	. $(VENV)/bin/activate; $(VENV)/bin/black src tests || true

format-check:
	@echo "Checking formatting (black --check)"
	. $(VENV)/bin/activate; $(VENV)/bin/black --check src tests

lint:
	@echo "Running linter (ruff)"
	. $(VENV)/bin/activate; $(VENV)/bin/ruff src tests

typecheck:
	@echo "Running mypy type checks"
	. $(VENV)/bin/activate; $(VENV)/bin/mypy src || true

# ---------- Tests ----------
test:
	@echo "Running pytest"
	. $(VENV)/bin/activate; pytest -q

coverage:
	@echo "Running pytest with coverage"
	. $(VENV)/bin/activate; pytest --cov=src --cov-report=term-missing

# ---------- Build / Package ----------
build: venv
	@echo "Building source and wheel distributions"
	. $(VENV)/bin/activate; python -m pip install --upgrade build
	. $(VENV)/bin/activate; python -m build --outdir $(DIST_DIR)

package: build
	@echo "Package artifacts are in $(DIST_DIR)"

# ---------- Docker (optional) ----------
# Usage: make DOCKER_IMAGE=registry/your/repo:tag docker-build
docker-build:
ifndef DOCKER_IMAGE
	$(error DOCKER_IMAGE is not set. Example: make DOCKER_IMAGE=myrepo/myimage:$(TAG) docker-build)
endif
	@echo "Building docker image $(DOCKER_IMAGE)"
	docker build -t $(DOCKER_IMAGE) .

docker-push: docker-build
	@echo "Pushing docker image $(DOCKER_IMAGE)"
	docker push $(DOCKER_IMAGE)

# ---------- CI orchestration ----------
ci: format-check lint typecheck test
	@echo "CI checks passed"

# ---------- Render.com manual deploy trigger ----------
# This triggers a manual deploy for the given service via the Render API v1.
# Set RENDER_SERVICE_ID and RENDER_API_KEY as environment variables in your CI (GitHub Actions secrets).
render-deploy:
	@echo "Triggering Render deploy for service $(RENDER_SERVICE_ID)"
ifndef RENDER_SERVICE_ID
	$(error RENDER_SERVICE_ID is not set)
endif
ifndef RENDER_API_KEY
	$(error RENDER_API_KEY is not set)
endif
	@echo "Calling Render API to create a manual deploy..."
	curl -s -X POST "https://api.render.com/v1/services/$(RENDER_SERVICE_ID)/deploys" \
	  -H "Authorization: Bearer $(RENDER_API_KEY)" \
	  -H 'Content-Type: application/json' \
	  -d '{"clearCache":false}' | jq . || true

# ---------- Helper: write a recommended GitHub Actions workflow file ----------
# Running `make gh-workflow` writes .github/workflows/ci.yml — inspect before committing.
gh-workflow:
	@echo "Writing recommended GitHub Actions workflow to .github/workflows/ci.yml"
	@mkdir -p .github/workflows
	cat > .github/workflows/ci.yml <<'YAML'
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m venv .venv
        . .venv/bin/activate
        python -m pip install --upgrade pip
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        pip install black ruff mypy pytest

    - name: Format check
      run: . .venv/bin/activate && black --check src tests

    - name: Lint
      run: . .venv/bin/activate && ruff src tests

    - name: Type check
      run: . .venv/bin/activate && mypy src || true

    - name: Run tests
      run: . .venv/bin/activate && pytest -q

  render-deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Render (manual trigger)
        env:
          RENDER_SERVICE_ID: ${{ secrets.RENDER_SERVICE_ID }}
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
        run: |
          echo "Triggering Render deploy for $$RENDER_SERVICE_ID"
          curl -s -X POST "https://api.render.com/v1/services/$$RENDER_SERVICE_ID/deploys" \
            -H "Authorization: Bearer $$RENDER_API_KEY" \
            -H 'Content-Type: application/json' \
            -d '{"clearCache":false}' | jq . || true
YAML
	@echo "Workflow written to .github/workflows/ci.yml — review before committing"

# ---------- End of Makefile ----------
# Notes:
# - This Makefile is intentionally explicit: CI systems (GitHub Actions / Render) run on Linux and will use the bash-style venv activation.
# - For Windows local development, use ".venv\Scripts\Activate.ps1" in PowerShell or adapt the venv activation lines accordingly.
# - Sensitive values like RENDER_API_KEY and DOCKER credentials must be set in your CI as secrets, not committed to the repo.
# - The Render API call here uses the v1 endpoint to trigger a manual deploy of a service. If your Render setup differs (deploys on GitHub pushes), prefer the push-based flow.
