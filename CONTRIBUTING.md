# Contributing to dgi-toolkit

Thank you for your interest in contributing!

## Pre-commit Hooks

We use [pre-commit](https://pre-commit.com/) to enforce code style and quality. To set up pre-commit hooks:

```bash
poetry install
poetry run pre-commit install
```

You can run all hooks manually with:

```bash
poetry run pre-commit run --all-files
```

## Commit Message Guidelines

We use [commitlint](https://commitlint.js.org/) to enforce conventional commit messages. Please use the following format:

```
type(scope): subject
```

Examples:
- `feat(cli): add rich table output to screen command`
- `fix(portfolio): handle empty DataFrame edge case`
- `chore: update dependencies`

## Pull Requests
- Ensure all tests pass (`poetry run pytest`)
- Ensure code is formatted (`black`, `ruff`)
- Ensure type checks pass (`mypy --strict`)
- Ensure coverage is ≥ 85%

Thank you for helping make dgi-toolkit better! 