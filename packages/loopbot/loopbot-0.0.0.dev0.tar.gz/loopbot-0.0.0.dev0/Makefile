
.PHONY: all check test coverage clean install dev-install test-e2e test-all \
	test-e2e-profile test-e2e-report \
	coverage-e2e validate-matrix validate-docs docs docs-build docs-test docs-deploy check-docs test-all-versions

# Default target
all: check test

# Development setup
dev-install:
	uv sync --extra dev

install:
	uv sync

# Run all checks (format, lint, type check)
check:
	@uv run ruff format src/loopbot tests/
	@uv run ruff check --select I --fix src/loopbot tests
	@uv run ruff check --fix src/loopbot tests
	@uv run ruff check src/loopbot tests
	@uv run ty check src/loopbot tests

# Testing
test:
	uv run pytest tests

# Run tests across multiple Python versions using uv (no tox required).
# Configure which versions via `PY_VERSIONS` or pass extra pytest args via `ARGS`.
# Examples:
#   make test-all-versions
#   make test-all-versions ARGS="-k unit -q"
#   PY_VERSIONS="3.12 3.13" make test-all-versions
PY_VERSIONS ?= 3.10 3.11 3.12 3.13 3.14
test-all-versions:
	@set -e; \
	for v in $(PY_VERSIONS); do \
	  echo "👟 Running tests on Python $$v"; \
	  uv run --isolated --python=$$v --extra dev pytest $${ARGS:-tests}; \
	done

coverage: ## Run coverage across unit, integration, and e2e suites
	uv run coverage erase
#LOOPBOT_E2E=1 uv run coverage run -m pytest tests/
	uv run coverage run -m pytest tests/
	uv run coverage html
	uv run coverage xml
	uv run coverage report --fail-under=95

# Documentation
docs: ## Build and serve documentation locally
	@echo "📚 Starting documentation server at http://127.0.0.1:8000"
	@uv run mkdocs serve

docs-build: ## Build static documentation site
	@echo "📚 Building documentation"
	@uv run mkdocs build

docs-test: ## Test documentation build (strict mode)
	@echo "📚 Testing documentation build"
	@uv run mkdocs build --strict

docs-deploy: ## Deploy documentation to GitHub Pages
	@echo "📚 Deploying documentation"
	@uv run mkdocs gh-deploy --force

check-docs: ## Validate all docs are in navigation
	@echo "📚 Checking documentation completeness"
	@uv run python scripts/check_docs_in_mkdocs.py

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf src/*.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Development utilities
shell:
	uv run python

# Release preparation
build:
	uv build

publish-test:
	uv publish --repository testpypi

publish:
	uv publish

# Help
help:
	@echo "Available targets:"
	@echo "  all          - Run check and test (default)"
	@echo "  dev-install  - Install development dependencies"
	@echo "  install      - Install production dependencies"
	@echo "  check        - Run all code quality checks (format + lint + typecheck)"
	@echo "  test         - Run mock tests (excludes E2E)"
	@echo "  test-all-versions - Run tests across Python versions via uv (PY_VERSIONS, ARGS)"
	@echo "  coverage     - Run coverage"
	@echo ""
	@echo "Documentation:"
	@echo "  docs         - Build and serve docs locally (http://127.0.0.1:8000)"
	@echo "  docs-build   - Build static documentation site"
	@echo "  docs-test    - Test documentation build (strict mode)"
	@echo "  docs-deploy  - Deploy documentation to GitHub Pages"
	@echo "  check-docs   - Validate all docs are in navigation"
	@echo ""
	@echo "Utilities:"
	@echo "  shell        - Start Python REPL"
	@echo "  clean        - Remove build artifacts"
	@echo ""
	@echo "Release:"
	@echo "  build        - Build distribution packages"
	@echo "  publish-test - Publish to test PyPI"
	@echo "  publish      - Publish to PyPI"
