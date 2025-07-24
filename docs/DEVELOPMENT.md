# Development Guide

## Quality Assurance Workflow

This project maintains high code quality standards through automated checks and
validations.

### Pre-commit Hooks

Pre-commit hooks automatically run on every commit to ensure code quality:

```bash
# Install pre-commit hooks (one-time setup)
pre-commit install
pre-commit install --hook-type commit-msg
```

**What gets checked automatically:**

1. **Code Formatting** 📝
   - `ruff format` - Modern Python formatter
   - `black` - Backup formatter
   - `isort` - Import sorting

2. **Linting & Auto-fixes** 🔧
   - `ruff` - Fast linter with 100+ rules
   - Auto-fixes: unused imports, syntax issues, style violations

3. **Type Checking** 🔍
   - `mypy` - Static type checking (core business logic only)
   - Ensures type safety in `dgi/` package

4. **Security** 🔒
   - `bandit` - Security vulnerability scanner
   - Checks for common security issues

5. **File Quality** 📄
   - Trailing whitespace removal
   - End-of-file newlines
   - YAML/TOML validation
   - Merge conflict detection

6. **Commit Messages** 💬
   - Conventional commit format validation
   - Examples: `feat:`, `fix:`, `docs:`, `refactor:`

### Manual Quality Checks

Run comprehensive quality checks before pushing:

```bash
# Run all quality checks
./scripts/check-quality.sh

# Or run individual tools
poetry run ruff check --fix .        # Linting with autofix
poetry run ruff format .             # Formatting
poetry run mypy --config-file mypy.ini dgi/  # Type checking
poetry run pytest tests/ --cov=dgi   # Tests with coverage
poetry run bandit -r dgi/            # Security scan
```

### Development Workflow

1. **Make Changes** ✏️

   ```bash
   # Create feature branch
   git checkout -b feature/your-feature

   # Make your changes
   # ... edit files ...
   ```

2. **Auto-fix Issues** 🔧

   ```bash
   # Run quality check script
   ./scripts/check-quality.sh

   # Or let pre-commit handle it
   git add .
   git commit -m "feat: your feature description"
   # Pre-commit hooks run automatically
   ```

3. **Commit & Push** 🚀
   ```bash
   # If pre-commit fixes files, add them and commit again
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature
   ```

### Configuration Files

- **`.pre-commit-config.yaml`** - Pre-commit hook configuration
- **`pyproject.toml`** - Tool configurations (ruff, isort, bandit, mypy)
- **`mypy.ini`** - MyPy type checking configuration

### Quality Standards

**Core Business Logic (`dgi/` package):**

- ✅ 100% type safety (strict mypy)
- ✅ Comprehensive test coverage
- ✅ Security scanning
- ✅ Consistent formatting

**Test Files:**

- ✅ Proper type annotations
- ✅ Clear test documentation
- ✅ Security scanning excluded

**Documentation:**

- ✅ Auto-formatted with Prettier
- ✅ Consistent markdown style

### Troubleshooting

**Pre-commit failing?**

```bash
# Run hooks manually to see issues
pre-commit run --all-files

# Skip hooks temporarily (NOT recommended)
git commit --no-verify
```

**Type checking errors?**

```bash
# Check specific files
poetry run mypy --config-file mypy.ini dgi/models.py

# Focus on core business logic first
poetry run mypy --config-file mypy.ini dgi/ --no-error-summary
```

**Import organization issues?**

```bash
# Fix import sorting
poetry run isort .

# Check import configuration
poetry run isort --diff .
```

### Best Practices

1. **Commit Often** - Small, focused commits are easier to review
2. **Use Conventional Commits** - `feat:`, `fix:`, `docs:`, `refactor:`
3. **Run Quality Checks** - Use `./scripts/check-quality.sh` before pushing
4. **Focus on Core Logic** - Business logic in `dgi/` has highest standards
5. **Document Changes** - Update relevant documentation

### CI/CD Integration

The same quality checks run in CI:

- All formatting and linting checks
- Type checking on core business logic
- Full test suite with coverage
- Security scanning

**CI will fail if:**

- Type checking fails on `dgi/` package
- Tests fail or coverage drops below threshold
- Security vulnerabilities detected
- Code formatting inconsistencies found
