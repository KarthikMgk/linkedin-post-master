VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help install install-dev run dev test coverage lint lint-fix format format-fix typecheck check-all fix hooks-install clean

help:
	@echo "Available commands:"
	@echo "  make install        Install production dependencies"
	@echo "  make install-dev    Install production + test + dev dependencies"
	@echo "  make run            Run the server (production mode)"
	@echo "  make dev            Run the server (hot reload)"
	@echo "  make test           Run test suite"
	@echo "  make coverage       Run tests with HTML coverage report"
	@echo "  make lint           Check code with ruff (linting)"
	@echo "  make lint-fix       Auto-fix ruff lint violations"
	@echo "  make format         Check code formatting with ruff"
	@echo "  make format-fix     Auto-fix code formatting with ruff"
	@echo "  make typecheck      Check types with mypy"
	@echo "  make check-all      Run lint + format + typecheck + tests (mirrors pre-push hook)"
	@echo "  make fix            Auto-fix all lint and formatting violations"
	@echo "  make hooks-install  Activate git pre-push hooks (run once per clone)"
	@echo "  make clean          Remove venv, cache, and coverage artifacts"

$(VENV)/bin/activate:
	python3 -m venv $(VENV)

install: $(VENV)/bin/activate
	$(PIP) install -r requirements.txt
	git -C .. config core.hooksPath .githooks

install-dev: install
	$(PIP) install -r requirements-test.txt
	$(PIP) install -r requirements-dev.txt

run: $(VENV)/bin/activate
	$(PYTHON) -m uvicorn main:app --host 0.0.0.0 --port 8000

dev: $(VENV)/bin/activate
	$(PYTHON) -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

test: $(VENV)/bin/activate
	$(PYTHON) -m pytest tests/ -q

coverage: $(VENV)/bin/activate
	$(PYTHON) -m pytest tests/ --cov=. --cov-report=html --cov-omit="venv/*,tests/*"
	@echo "Coverage report: htmlcov/index.html"

lint: $(VENV)/bin/activate
	$(PYTHON) -m ruff check .

lint-fix: $(VENV)/bin/activate
	$(PYTHON) -m ruff check . --fix

format: $(VENV)/bin/activate
	$(PYTHON) -m ruff format --check .

format-fix: $(VENV)/bin/activate
	$(PYTHON) -m ruff format .

typecheck: $(VENV)/bin/activate
	$(PYTHON) -m mypy . --exclude venv --exclude tests

check-all: lint format typecheck test
	@echo "All checks passed."

fix: $(VENV)/bin/activate
	$(PYTHON) -m ruff check . --fix
	$(PYTHON) -m ruff format .

hooks-install:
	git -C .. config core.hooksPath .githooks
	@echo "Git hooks activated. Pre-push checks will run on every git push."

clean:
	rm -rf $(VENV) __pycache__ .coverage htmlcov .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
