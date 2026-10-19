# RepSync Makefile for Backend, Database, QA & DevOps

PYTHON ?= python
VENV_BIN ?= .venv/Scripts
PIP = $(VENV_BIN)/pip
PYTEST = $(VENV_BIN)/pytest
RUFF = $(VENV_BIN)/ruff
UVICORN = $(VENV_BIN)/uvicorn

.PHONY: setup dev test lint migrate seed help

help:
	@echo "Available commands:"
	@echo "  make setup    - Create virtual environment and install dependencies"
	@echo "  make dev      - Start FastAPI backend with live reload"
	@echo "  make test     - Run pytest test suite"
	@echo "  make lint     - Run ruff linter"
	@echo "  make migrate  - Initialize/apply database tables"
	@echo "  make seed     - Seed platform registry, demo user, and demo datasets"

setup:
	$(PYTHON) -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r backend/requirements.txt

dev:
	$(UVICORN) backend.app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	$(PYTEST) backend/tests -v

lint:
	$(RUFF) check backend

migrate:
	$(VENV_BIN)/python -m backend.app.db_init

seed:
	$(VENV_BIN)/python -m backend.app.seed

smoke:
	$(VENV_BIN)/python scripts/smoke.py

audit:
	$(VENV_BIN)/python scripts/audit_secrets.py

