PROJECT_NAME = kagura-ai
PYTHON = python3
VENV_DIR = .venv
BUILD_DIR = dist
LOCK_FILE = uv.lock

.PHONY: all
all: help

.PHONY: help
help:
	@echo "Usage:"
	@echo "  make venv         Create a virtual environment"
	@echo "  make lock         Generate or regenerate uv.lock"
	@echo "  make sync         Sync dependencies using uv"
	@echo "  make test         Run tests using pytest"
	@echo "  make build        Build the package"
	@echo "  make clean        Clean build artifacts"

.PHONY: venv
venv:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip uv
	@echo "Done."

.PHONY: lock
lock: venv
	@echo "Regenerating $(LOCK_FILE)..."
	rm -f $(LOCK_FILE)
	$(VENV_DIR)/bin/uv lock
	@echo "$(LOCK_FILE) regenerated."

.PHONY: sync
sync: lock
	@echo "Syncing dependencies with uv..."
	$(VENV_DIR)/bin/uv sync --frozen --dev
	$(VENV_DIR)/bin/pip install build
	@echo "Done. You can now activate the virtual environment with 'source $(VENV_DIR)/bin/activate'."

.PHONY: test
test: sync
	@echo "Running tests with pytest..."
	$(VENV_DIR)/bin/pytest --maxfail=5 --disable-warnings -q
	@echo "Done."

.PHONY: build
build: sync
	@echo "Building the package..."
	$(VENV_DIR)/bin/python -m build
	@echo "Done. Build artifacts are in $(BUILD_DIR)/"

.PHONY: clean
clean:
	@echo "Cleaning up..."
	rm -rf $(VENV_DIR) $(BUILD_DIR) $(LOCK_FILE) src/*.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Done."
