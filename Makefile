# PaveDB Python SDK - Makefile
#
# Local-first build pipeline. Build/package targets create PyPI-ready
# sdist and wheel files; upload targets are explicit.

PKG_NAME      := pavedb-sdk
PKG_IMPORT    := pavesdk
PYTHON        ?= python3
VENV          ?= .venv
PYTHON_BIN    ?= $(VENV)/bin/python
PIP_BIN       ?= $(VENV)/bin/pip
DIST_DIR      := dist
BUILD_DIR     := build
ART_DIR       := artifacts
VERSION       ?= $(shell sed -n 's/^version = "\([^"]*\)".*/\1/p' \
	pyproject.toml | head -1)

.PHONY: help
help:
	@echo "PaveDB Python SDK Make Targets"
	@echo ""
	@echo "Setup:"
	@echo "  venv         Create local virtualenv ($(VENV))"
	@echo "  install      Install package in editable mode"
	@echo "  install-dev  Install test/build tools"
	@echo ""
	@echo "Verify:"
	@echo "  test         Compile package and run pytest"
	@echo "  check        Run tests, build package artifacts"
	@echo ""
	@echo "Build:"
	@echo "  build        Build sdist (.tar.gz) and wheel into ./dist"
	@echo "  package      Copy built PyPI artifacts into ./artifacts"
	@echo "  pypitest-push Upload dist/* to TestPyPI"
	@echo "  pypi-push     Upload dist/* to PyPI"
	@echo ""
	@echo "Clean:"
	@echo "  clean        Remove build outputs and caches"
	@echo "  deps-clean   Remove $(VENV)"

.PHONY: venv
venv:
	@if ! command -v $(PYTHON) >/dev/null 2>&1; then \
	  echo "ERROR: '$(PYTHON)' not found"; \
	  exit 127; \
	fi
	@if [ ! -x "$(PYTHON_BIN)" ] \
	  || ! "$(PIP_BIN)" --version >/dev/null 2>&1; then \
	  echo "Creating virtual environment in $(VENV)"; \
	  rm -rf "$(VENV)"; \
	  $(PYTHON) -m venv "$(VENV)" --prompt $(PKG_NAME); \
	  $(PIP_BIN) install -q --upgrade pip; \
	fi
	@echo "Virtual env ready: $(PYTHON_BIN)"

.PHONY: install
install: venv
	$(PIP_BIN) install -q -e .
	@echo "Runtime package installed."

.PHONY: install-dev
install-dev: venv
	$(PIP_BIN) install -q -U setuptools wheel build twine
	$(PIP_BIN) install -q -e ".[test]"
	@echo "Dev/test/build tools installed."

.PHONY: test
test: install-dev
	PYTHONPATH=. $(PYTHON_BIN) -m compileall -q $(PKG_IMPORT)
	PYTHONPATH=. $(PYTHON_BIN) -m pytest -q

.PHONY: build
build: install-dev
	rm -rf $(DIST_DIR) $(BUILD_DIR)
	$(PYTHON_BIN) -m build --sdist --wheel --outdir $(DIST_DIR) --no-isolation
	$(PYTHON_BIN) -m twine check $(DIST_DIR)/*
	@echo "Built $(PKG_NAME) $(VERSION):"
	@ls -1 $(DIST_DIR)

.PHONY: package
package: build
	rm -rf $(ART_DIR)
	mkdir -p $(ART_DIR)
	cp $(DIST_DIR)/*.tar.gz $(DIST_DIR)/*.whl $(ART_DIR)/
	@echo "PyPI artifacts available in $(ART_DIR)/:"
	@ls -1 $(ART_DIR)

.PHONY: pypitest-push
pypitest-push: package
	$(PYTHON_BIN) -m twine upload --skip-existing --repository testpypi \
		$(DIST_DIR)/*

.PHONY: pypi-push
pypi-push: package
	$(PYTHON_BIN) -m twine upload --skip-existing $(DIST_DIR)/*

.PHONY: check
check: test package

.PHONY: clean
clean:
	rm -rf $(DIST_DIR) $(BUILD_DIR) $(ART_DIR)
	rm -rf .pytest_cache .ruff_cache .mypy_cache
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	find . -name '*.egg-info' -type d -prune -exec rm -rf {} +
	@echo "Cleaned build outputs and caches."

.PHONY: deps-clean
deps-clean:
	rm -rf $(VENV)
	@echo "Removed $(VENV)."
