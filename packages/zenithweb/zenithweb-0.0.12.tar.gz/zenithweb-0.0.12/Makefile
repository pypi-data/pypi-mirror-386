# Zenith Framework - Development Commands
# Run 'make help' to see all available commands

.PHONY: help install format lint type-check test clean build publish

# Default target
help:
	@echo "Zenith Framework - Available Commands:"
	@echo ""
	@echo "  make install       Install development dependencies"
	@echo "  make format        Auto-format code with ruff"
	@echo "  make lint          Check code style with ruff"
	@echo "  make type-check    Run ty type checking (alpha)"
	@echo "  make test          Run test suite"
	@echo "  make test-cov      Run tests with coverage"
	@echo "  make clean         Remove build artifacts"
	@echo "  make build         Build distribution packages"
	@echo "  make publish-test  Publish to Test PyPI"
	@echo "  make pre-commit    Install pre-commit hooks"
	@echo "  make ci            Run all CI checks locally"
	@echo ""

# Development setup
install:
	uv pip install -e ".[dev,benchmark]"
	@echo "✅ Development environment ready"

# Code formatting - automatically fixes issues
format:
	@echo "🎨 Formatting code..."
	ruff format .
	ruff check . --fix
	@echo "✅ Code formatted"

# Linting - checks without fixing
lint:
	@echo "🔍 Running linter..."
	ruff format --check zenith/ tests/
	ruff check zenith/ tests/ --ignore B904,F841,B007,PTH108,PTH116,E722,SIM105,RUF006,F821,B017,PTH207,B023,SIM103
	@echo "✅ Linting passed"

# Type checking with ty (Astral's fast type checker - alpha, informational)
type-check:
	@echo "🔍 Running ty type checker (alpha)..."
	-uvx ty check zenith/
	@echo "✅ ty check complete"

# Testing
test:
	@echo "🧪 Running tests..."
	pytest

test-cov:
	@echo "🧪 Running tests with coverage..."
	pytest --cov=zenith --cov-report=term-missing

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleaned build artifacts"

# Build distribution
build: clean
	@echo "📦 Building distribution..."
	uv build
	@echo "✅ Build complete"

# Publish to Test PyPI
publish-test: build
	@echo "📤 Publishing to Test PyPI..."
	python -m twine upload --repository testpypi dist/*
	@echo "✅ Published to Test PyPI"

# Install pre-commit hooks
pre-commit:
	@echo "🔧 Installing pre-commit hooks..."
	uv pip install pre-commit
	pre-commit install
	pre-commit run --all-files
	@echo "✅ Pre-commit hooks installed"

# Run all CI checks locally
ci: format lint type-check test
	@echo "✅ All CI checks passed"

# Quick check before committing
check: format test
	@echo "✅ Ready to commit"