# (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com>
# SPDX-License-Identifier: Apache-2.0
#
# PaveDB Python SDK — Makefile
#
# Local-first build pipeline. Build/package targets create PyPI-ready
# sdist and wheel files; upload targets are explicit.
#
# VERSION is read from pyproject.toml and is the single source of truth. CI
# publishes from a v$(VERSION) tag; nothing here pushes.

# GNU Make 4+ and bash 4+ required.
ifeq ($(shell uname -s),Darwin)
_MAKE_HINT := . macOS: `brew install make` and invoke as `gmake`
_BASH_HINT := . macOS: `brew install bash`
endif

_MAKE_MAJOR := $(firstword $(subst ., ,$(MAKE_VERSION)))
ifneq ($(filter 1 2 3,$(_MAKE_MAJOR)),)
$(error GNU Make >= 4 required (found $(MAKE_VERSION))$(_MAKE_HINT))
endif

SHELL := $(shell command -v bash)
ifeq ($(SHELL),)
$(error bash not found$(_BASH_HINT))
endif
_BASH_MAJOR := $(shell $(SHELL) -c 'echo $${BASH_VERSINFO[0]}' 2>/dev/null)
ifneq ($(filter 1 2 3,$(_BASH_MAJOR)),)
$(error bash >= 4 required (found bash $(_BASH_MAJOR).x at $(SHELL))$(_BASH_HINT))
endif

PKG_NAME      := pavedb-sdk
PKG_IMPORT    := pavesdk
PYTHON        ?= python3
VENV          ?= .venv
PYTHON_BIN    ?= $(VENV)/bin/python
PIP_BIN       ?= $(VENV)/bin/pip
DIST_DIR      := dist
BUILD_DIR     := build
ART_DIR       := artifacts
CHANGELOG     ?= CHANGELOG.md
RELEASE_REMOTE ?= gitlab
VERSION       ?= $(shell sed -n 's/^version = "\([^"]*\)".*/\1/p' \
	pyproject.toml | head -1)

# -------- help --------
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
	@echo "  docs         Generate API and examples reference"
	@echo "  docs-check   Verify generated docs and example imports"
	@echo "  test         Compile package and run pytest"
	@echo "  check        Run tests, build package artifacts"
	@echo ""
	@echo "Build:"
	@echo "  build        Build sdist (.tar.gz) and wheel into ./dist"
	@echo "  package      Copy built PyPI artifacts into ./artifacts"
	@echo "  pypitest-push Upload dist/* to TestPyPI"
	@echo "  pypi-push     Upload dist/* to PyPI"
	@echo ""
	@echo "Release:"
	@echo "  bump            Set the version in pyproject.toml (VERSION=x.y.z)"
	@echo "  changelog       Preview the $(VERSION) entry (no write)"
	@echo "  changelog-write Prepend the $(VERSION) entry to $(CHANGELOG)"
	@echo "  release         Bump, changelog, check, commit, and tag"
	@echo ""
	@echo "Clean:"
	@echo "  clean        Remove build outputs and caches"
	@echo "  deps-clean   Remove $(VENV)"

# -------- setup --------
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

# -------- docs --------
.PHONY: docs
docs:
	$(PYTHON) docs/generate_reference.py

.PHONY: docs-check
docs-check: install-dev
	PYTHONPATH=. $(PYTHON_BIN) docs/generate_reference.py --check

# -------- verify --------
.PHONY: test
test: docs-check
	PYTHONPATH=. $(PYTHON_BIN) -m compileall -q $(PKG_IMPORT)
	PYTHONPATH=. $(PYTHON_BIN) -m pytest -q

# -------- build / artifacts --------
.PHONY: build
build: docs-check
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

# -------- bump --------
.PHONY: bump
bump:
	@if [ -z "$(VERSION)" ]; then \
	  echo "Error: VERSION is not set. Usage: make bump VERSION=0.1.4"; \
	  exit 1; \
	fi
	@perl -0pi -e 's/^(version = ")[^"]*(")/$${1}$(VERSION)$${2}/m' pyproject.toml
	@echo "Version in pyproject.toml is now $(VERSION)."

# -------- changelog --------
.PHONY: changelog
changelog:
	@CHANGELOG_PATH=- scripts/changelog.sh $(VERSION)

.PHONY: changelog-write
changelog-write:
	@CHANGELOG_PATH=$(CHANGELOG) scripts/changelog.sh $(VERSION)

# -------- release --------
.PHONY: release
release:
	@if [ -n "$$(git status --porcelain)" ]; then \
	  echo "Working tree not clean"; exit 1; \
	fi
	@if git rev-parse "v$(VERSION)" >/dev/null 2>&1; then \
	  echo "Tag v$(VERSION) already exists"; exit 1; \
	fi
	@set -eE; \
	revert_changes() { \
	  echo "Reverting version bump and changelog..."; \
	  git checkout -- pyproject.toml $(CHANGELOG) 2>/dev/null || true; \
	}; \
	trap 'status=$$?; if [ "$$status" -ne 0 ]; then revert_changes; fi; exit $$status' ERR; \
	$(MAKE) bump VERSION=$(VERSION); \
	$(MAKE) changelog-write VERSION=$(VERSION); \
	$(MAKE) check VERSION=$(VERSION); \
	git add pyproject.toml $(CHANGELOG); \
	if git diff --cached --quiet; then \
	  echo "Nothing to commit — release commit already exists."; \
	else \
	  git commit -m "chore(release): v$(VERSION)"; \
	fi; \
	git tag "v$(VERSION)"; \
	echo; \
	echo "Tagged v$(VERSION). Publish with:"; \
	echo "  git push $(RELEASE_REMOTE) $$(git rev-parse --abbrev-ref HEAD) v$(VERSION)"

# -------- clean --------
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
