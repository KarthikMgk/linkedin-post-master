VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help install install-dev run dev test coverage lint clean

help:
	@echo "Available commands:"
	@echo "  make install      Install production dependencies"
	@echo "  make install-dev  Install production + test dependencies"
	@echo "  make run          Run the server (production mode)"
	@echo "  make dev          Run the server (hot reload)"
	@echo "  make test         Run test suite"
	@echo "  make coverage     Run tests with HTML coverage report"
	@echo "  make lint         Check code with pyflakes"
	@echo "  make clean        Remove venv, cache, and coverage artifacts"

$(VENV)/bin/activate:
	python3 -m venv $(VENV)

install: $(VENV)/bin/activate
	$(PIP) install -r requirements.txt

install-dev: install
	$(PIP) install -r requirements-test.txt

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
	$(PYTHON) -m pyflakes . || true

clean:
	rm -rf $(VENV) __pycache__ .coverage htmlcov .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
