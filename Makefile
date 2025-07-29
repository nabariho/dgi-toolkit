# DGI Toolkit - Makefile for Development and Testing
# Provides simple commands with proper environment isolation

.PHONY: help test test-unit test-integration test-api test-fast test-coverage test-server clean install dev-setup

# Default target
help:
	@echo "DGI Toolkit - Development Commands"
	@echo "=================================="
	@echo ""
	@echo "Testing Commands (with isolation):"
	@echo "  test              Run all tests with isolation"
	@echo "  test-unit         Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-api          Run API tests only"
	@echo "  test-fast         Run fast tests (exclude slow ones)"
	@echo "  test-coverage     Run all tests with coverage report"
	@echo "  test-server       Start test server with isolated data"
	@echo ""
	@echo "Development Commands:"
	@echo "  install           Install dependencies"
	@echo "  dev-setup         Setup development environment"
	@echo "  clean             Clean up generated files"
	@echo "  quality           Run all quality checks"
	@echo ""
	@echo "Environment Isolation:"
	@echo "  - All test commands use isolated test data"
	@echo "  - Production API keys are automatically cleared"
	@echo "  - Test environment variables are set automatically"
	@echo "  - No risk of corrupting production data"

# Testing commands with isolation
test:
	@echo "🧪 Running all tests with isolation..."
	./scripts/run-tests.sh

test-unit:
	@echo "🧪 Running unit tests with isolation..."
	./scripts/run-tests.sh unit

test-integration:
	@echo "🧪 Running integration tests with isolation..."
	./scripts/run-tests.sh integration

test-api:
	@echo "🧪 Running API tests with isolation..."
	./scripts/run-tests.sh api

test-fast:
	@echo "🧪 Running fast tests with isolation..."
	./scripts/run-tests.sh fast

test-coverage:
	@echo "🧪 Running tests with coverage report..."
	./scripts/run-tests.sh -c all

test-server:
	@echo "🚀 Starting test server with isolated data..."
	./scripts/run-tests.sh -s

# Development setup
install:
	@echo "📦 Installing dependencies..."
	poetry install

dev-setup:
	@echo "🔧 Setting up development environment..."
	poetry install
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "✅ Development environment ready!"

# Quality checks
quality:
	@echo "🔍 Running quality checks..."
	./scripts/check-quality.sh

# Cleanup
clean:
	@echo "🧹 Cleaning up generated files..."
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf tests/test_data/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "✅ Cleanup complete!"

# Quick development workflow
dev: install dev-setup
	@echo "🚀 Development environment ready!"
	@echo "Run 'make test' to run tests with isolation"
	@echo "Run 'make test-server' to start test server"
