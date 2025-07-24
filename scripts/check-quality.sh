#!/bin/bash
# Quality check script for DGI Toolkit
# Run this before committing to ensure all quality checks pass

set -e

echo "🔍 DGI Toolkit - Quality Check Suite"
echo "===================================="

# Change to project root if not already there
cd "$(dirname "$0")/.."

echo ""
echo "📦 Checking project structure..."
if [ ! -f "pyproject.toml" ] || [ ! -d "dgi" ]; then
    echo "❌ Not in project root directory"
    exit 1
fi
echo "✅ Project structure OK"

echo ""
echo "🔧 Running code formatters..."
echo "  - Ruff format"
poetry run ruff format .
echo "  - Black (backup)"
poetry run black .
echo "  - isort (import sorting)"
poetry run isort .

echo ""
echo "🧹 Running linters with autofix..."
echo "  - Ruff linter"
poetry run ruff check --fix .

echo ""
echo "🔒 Running security checks..."
echo "  - Bandit security linter"
poetry run bandit -r dgi/ --skip B101,B601 || echo "⚠️  Security warnings found"

echo ""
echo "📏 Running type checking..."
echo "  - MyPy (core business logic)"
if poetry run mypy --config-file mypy.ini dgi/; then
    echo "✅ Core business logic type checking passed"
else
    echo "❌ Type checking failed"
    exit 1
fi

echo ""
echo "🧪 Running tests..."
if poetry run pytest tests/ -v; then
    echo "✅ All tests passed"
else
    echo "❌ Tests failed"
    exit 1
fi

echo ""
echo "📊 Running test coverage..."
poetry run pytest tests/ --cov=dgi --cov-report=term-missing --cov-fail-under=80

echo ""
echo "🎯 Quality Check Summary"
echo "======================="
echo "✅ Code formatting: PASSED"
echo "✅ Linting: PASSED"
echo "✅ Security: CHECKED"
echo "✅ Type checking: PASSED"
echo "✅ Tests: PASSED"
echo "✅ Coverage: CHECKED"
echo ""
echo "🚀 Ready to commit and push!"
echo ""
echo "💡 Tips:"
echo "   - Use 'pre-commit run --all-files' to run pre-commit hooks"
echo "   - Use conventional commit format: 'feat:', 'fix:', 'docs:', etc."
echo "   - Check CI status after pushing"
