SHELL := /bin/bash

PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python
STREAMLIT := $(VENV)/bin/streamlit
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff
BLACK := $(VENV)/bin/black
MYPY := $(VENV)/bin/mypy

APP ?= frontend/app.py
FRONTEND_REQUIREMENTS ?= requirements-frontend.txt
DEV_REQUIREMENTS ?= requirements-dev.txt
COMPOSE ?= docker compose
SERVICE ?= frontend
STACK_NAME ?= portfolio-optimizer
AWS_REGION ?= ap-south-1

.PHONY: help venv install install-dev check-env run api format format-check lint typecheck compile test coverage check docker-build docker-up docker-down docker-restart docker-ps docker-logs docker-health aws-validate aws-outputs clean

help:
	@echo "AXIOM Portfolio Intelligence"
	@echo ""
	@echo "Local development:"
	@echo "  make venv           Create .venv and upgrade packaging tools"
	@echo "  make install        Install Streamlit/runtime dependencies"
	@echo "  make install-dev    Install runtime and development dependencies"
	@echo "  make check-env      Verify .env exists without printing secrets"
	@echo "  make run            Start the Streamlit dashboard on port 8501"
	@echo "  make api            Start the optional FastAPI service on port 8000"
	@echo ""
	@echo "Quality:"
	@echo "  make format         Format frontend, src, backend, and tests"
	@echo "  make format-check   Check formatting without editing"
	@echo "  make lint           Run Ruff"
	@echo "  make typecheck      Run mypy"
	@echo "  make compile        Compile-check Python source"
	@echo "  make test           Run pytest"
	@echo "  make coverage       Run pytest with coverage"
	@echo "  make check          Run compile, format-check, lint, typecheck, and tests"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   Build the frontend image"
	@echo "  make docker-up      Start/recreate frontend in the background"
	@echo "  make docker-down    Stop containers without deleting named volumes"
	@echo "  make docker-ps      Show container status"
	@echo "  make docker-logs    Show recent frontend logs"
	@echo "  make docker-health  Check Streamlit health endpoint"
	@echo ""
	@echo "AWS:"
	@echo "  make aws-validate   Validate deploy/aws/ec2-stack.yaml"
	@echo "  make aws-outputs    Display CloudFormation stack outputs"

venv:
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install --upgrade pip setuptools wheel

install: venv
	$(PIP) install -r $(FRONTEND_REQUIREMENTS)

install-dev: install
	@if [ -f "$(DEV_REQUIREMENTS)" ]; then $(PIP) install -r $(DEV_REQUIREMENTS); else $(PIP) install pytest pytest-cov ruff black mypy; fi

check-env:
	@test -f .env || (echo "Missing .env. Copy .env.example to .env and add the required keys." && exit 1)
	@echo ".env exists. Secret values were not displayed."

run: check-env
	$(STREAMLIT) run $(APP) --server.port 8501

api: check-env
	@if [ -f backend/app/main.py ]; then $(PY) -m uvicorn backend.app.main:app --reload --port 8000; else echo "Optional FastAPI entry point backend/app/main.py was not found."; exit 1; fi

format:
	$(BLACK) frontend src backend tests

format-check:
	$(BLACK) --check frontend src backend tests

lint:
	$(RUFF) check frontend src backend tests

typecheck:
	$(MYPY) frontend src backend

compile:
	$(PY) -m compileall -q frontend src backend

test:
	$(PYTEST) tests -v

coverage:
	$(PYTEST) tests --cov=src --cov=frontend --cov-report=term-missing

check: compile format-check lint typecheck test

docker-build:
	$(COMPOSE) build $(SERVICE)

docker-up: check-env
	$(COMPOSE) up -d --build --force-recreate $(SERVICE)

docker-down:
	$(COMPOSE) down

docker-restart: docker-down docker-up

docker-ps:
	$(COMPOSE) ps

docker-logs:
	$(COMPOSE) logs --tail=200 $(SERVICE)

docker-health:
	curl -fsS http://localhost:8501/_stcore/health

aws-validate:
	aws cloudformation validate-template --region $(AWS_REGION) --template-body file://deploy/aws/ec2-stack.yaml

aws-outputs:
	aws cloudformation describe-stacks --region $(AWS_REGION) --stack-name $(STACK_NAME) --query 'Stacks[0].Outputs' --output table

clean:
	find . -type d -name '__pycache__' -prune -exec rm -r {} +
	find . -type f -name '*.py[co]' -delete
	@echo "Removed Python cache files. Docker volumes and application data were not deleted."
