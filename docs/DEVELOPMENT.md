# Development Guide

## 🚀 Feature Development Process

This project follows a systematic approach to feature development that ensures quality,
maintainability, and adherence to industry best practices.

### Feature Development Workflow

For each feature in the backlog, we follow this 8-step process:

#### 1. **Feature Selection** 🎯

- Pick a feature from the Planned Features section in `docs/FEATURES.md`
- Prioritize based on business value and technical dependencies
- Ensure feature is well-defined with clear acceptance criteria

#### 2. **Status Update** 📋

- Move the feature from "📋 Planned" to "🔄 In Progress" in `docs/FEATURES.md`
- Update the status table with current date
- Commit the status change

#### 3. **Branch Creation** 🌿

- Create a new feature branch: `git checkout -b feature/DGIT-XXX-feature-name`
- Follow naming convention: `feature/DGIT-XXX-descriptive-name`
- Example: `feature/DGIT-301-fastapi-service-skeleton`

#### 4. **Test-Driven Development (TDD)** 🧪

- Write comprehensive tests first (unit, integration, edge cases)
- Ensure tests cover all acceptance criteria
- Use pytest with proper fixtures and mocking
- Target ≥ 85% test coverage for new code

#### 5. **Feature Implementation** 💻

- Implement the feature behavior following the acceptance criteria
- Use existing architecture patterns (Strategy, Repository, etc.)
- Follow the technical implementation notes from FEATURES.md
- Ensure type safety with mypy compliance

#### 6. **Acceptance Criteria Validation** ✅

- Verify all acceptance criteria are met
- Run the complete test suite
- Validate against business requirements
- Document any deviations or improvements

#### 7. **Code Quality & Best Practices** 🏗️

- Follow SOLID principles (Single Responsibility, Open/Closed, etc.)
- Write clean, readable, and maintainable code
- Use dependency injection and loose coupling
- Ensure proper error handling and logging
- Follow the project's coding standards (Black, Ruff, MyPy)

#### 8. **Code Review & Merge** 🔄

- Push feature branch to repository
- Create pull request with detailed description
- Include:
  - Feature summary and business value
  - Technical implementation details
  - Test coverage report
  - Any breaking changes or migration notes
- Address review feedback
- Merge to main branch
- Update feature status to "✅ Complete" in FEATURES.md

### Quality Gates

Each feature must pass these quality gates before merging:

- ✅ **Tests**: All tests pass with ≥ 85% coverage
- ✅ **Linting**: Ruff, Black, and MyPy checks pass
- ✅ **Security**: Bandit security scan passes
- ✅ **Documentation**: README and docstrings updated
- ✅ **Acceptance Criteria**: All criteria met and validated

### Branch Naming Convention

```
feature/DGIT-XXX-descriptive-name
```

Examples:

- `feature/DGIT-301-fastapi-service-skeleton`
- `feature/DGIT-401-finviz-scraper-tool`
- `feature/DGIT-403-research-agent-orchestrator`

### Commit Message Convention

Follow conventional commits:

```
type(scope): description

- feat: new feature
- fix: bug fix
- docs: documentation changes
- test: adding or updating tests
- refactor: code refactoring
- chore: maintenance tasks
```

### Pull Request Template

```markdown
## Feature Summary

- **Feature ID**: DGIT-XXX
- **Title**: Brief description
- **Business Value**: What problem does this solve?

## Technical Implementation

- **Files Changed**: List of key files
- **Architecture**: How it fits into existing patterns
- **Dependencies**: New dependencies added

## Testing

- **Coverage**: Test coverage percentage
- **Test Types**: Unit, integration, etc.
- **Edge Cases**: Special scenarios tested

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Breaking Changes

- None / List any breaking changes

## Migration Notes

- Any required migration steps
```

---

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
