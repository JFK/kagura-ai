PROJECT_NAME = kagura-ai
PYTHON = python3
VENV_DIR = .venv
BUILD_DIR = dist

.PHONY: all
all: help

.PHONY: help
help:
	@echo "Usage:"
	@echo "  make venv         Create a virtual environment"
	@echo "  make sync         Sync dependencies using uv"
	@echo "  make right        Run static type checking using pyright"
	@echo "  make test         Run tests using pytest"
	@echo "  make ruff         Run code formatting using ruff"
	@echo "  make build        Build the package"
	@echo "  make clean        Clean build artifacts"

.PHONY: venv
venv:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip uv
	@echo "Done."

.PHONY: sync
sync: venv
	@echo "Syncing dependencies with uv..."
	$(VENV_DIR)/bin/uv sync --frozen --all-extras --dev

.PHONY: right
right: sync
	@echo "Running tests with pytest..."
	$(VENV_DIR)/bin/pyright
	@echo "Done."

.PHONY: test
test: right
	@echo "Running tests with pytest..."
	$(VENV_DIR)/bin/flake8 tests/ src/
	$(VENV_DIR)/bin/pytest --maxfail=5 --disable-warnings -q
	$(VENV_DIR)/bin/pytest --cov=src --cov-report=term-missing
	@echo "Done."

.PHONY: ruff
ruff: test
	@echo "Running tests with pytest..."
	$(VENV_DIR)/bin/ruff format
	@echo "Done."

.PHONY: build
build: ruff
	@echo "Building the package..."
	$(VENV_DIR)/bin/uv build
	@echo "Done. Build artifacts are in $(BUILD_DIR)/"

.PHONY: clean
clean:
	@echo "Cleaning up..."
	rm -rf $(BUILD_DIR) src/*.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Done."

.PHONY: docs
docs:
	@echo "Building documentation..."
	$(VENV_DIR)/bin/pip install --upgrade sphinx sphinx-rtd-theme
	$(VENV_DIR)/bin/sphinx-build -b html docs/ docs/_build
	@echo "Done. Documentation is in docs/_build/"
