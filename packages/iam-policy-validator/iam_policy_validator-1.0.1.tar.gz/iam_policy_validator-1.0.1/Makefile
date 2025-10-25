.PHONY: help install dev clean test lint format type-check build publish publish-test version

# Default target
help:
	@echo "IAM Policy Auditor - Makefile Commands"
	@echo ""
	@echo "Development:"
	@echo "  make install          Install production dependencies"
	@echo "  make dev              Install development dependencies"
	@echo "  make clean            Clean build artifacts and cache"
	@echo ""
	@echo "Quality:"
	@echo "  make test             Run tests"
	@echo "  make lint             Run linting checks"
	@echo "  make format           Format code with ruff"
	@echo "  make type-check       Run mypy type checking"
	@echo "  make check            Run all checks (lint + type + test)"
	@echo ""
	@echo "Build & Publish:"
	@echo "  make build            Build distribution packages"
	@echo "  make publish-test     Publish to TestPyPI"
	@echo "  make publish          Publish to PyPI"
	@echo "  make version          Show current version"
	@echo ""
	@echo "Examples:"
	@echo "  make validate-example Run validator on example policies"

# Installation
install:
	uv sync --no-dev

dev:
	uv sync

# Clean
clean:
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info
	@rm -rf .pytest_cache/
	@rm -rf .mypy_cache/
	@rm -rf .ruff_cache/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.orig" -delete

# Testing
test:
	@uv run pytest tests/ -v

# Linting and formatting
lint:
	@uv run ruff check iam_validator/

format:
	@uv run ruff format iam_validator/
	@uv run ruff check --fix iam_validator/

type-check:
	uv run mypy iam_validator/

# Run all checks
check: lint type-check test
	echo "✓ All checks passed!"

# Building
build: clean
	uv build

# Version management
version:
	@grep '^version = ' pyproject.toml | cut -d'"' -f2

# Publishing to TestPyPI (for testing)
publish-test: build
	@echo "Publishing to TestPyPI..."
	uv publish --publish-url https://test.pypi.org/legacy/

# Publishing to PyPI (production)
publish: build
	@echo "Publishing to PyPI..."
	@read -p "Are you sure you want to publish to PyPI? (yes/no): " confirm && \
	if [ "$$confirm" = "yes" ]; then \
		uv publish; \
	else \
		echo "Publish cancelled."; \
	fi

# Example validation
validate-example:
	uv run iam-validator --path examples/sample_policy.json

validate-invalid:
	uv run iam-validator --path examples/invalid_policy.json || true

# CI/CD simulation
ci: check build
	@echo "✓ CI checks complete!"
