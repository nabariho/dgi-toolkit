# Project Scaffolding Guide for Python Projects

This document outlines the recommended steps and best practices to scaffold a new Python project, as exemplified by the setup of `dgi-toolkit`.

## 1. Repository Metadata
- Create a new (private) GitHub repository.
- Add an MIT LICENSE (or your preferred license).
- Add a `README.md` with project pitch, quick-start, and badge placeholders.
- Add a `CODE_OF_CONDUCT.md` (use GitHub template).

## 2. Python Packaging
- Initialize a Poetry project with the `src/` layout:
  ```bash
  poetry new --src <project-name>
  poetry config virtualenvs.in-project true
  ```
- Set Python version constraint (e.g., `^3.12`) in `pyproject.toml`.
- Add runtime dependencies:
  ```bash
  poetry add pandas 'typer[all]' rich
  ```
- Add development dependencies:
  ```bash
  poetry add --group dev pytest pytest-cov ruff black mypy pre-commit langchain openai chromadb
  ```
- Set initial version:
  ```bash
  poetry version 0.1.0
  ```

## 3. Linting & Formatting
- Configure `pyproject.toml` for `ruff` and `black` (e.g., line-length 88).
- Add `.pre-commit-config.yaml` with hooks for ruff, black, mypy (strict).

## 4. Testing
- Add `tests/__init__.py` and a placeholder test file (e.g., `test_sample.py`).
- Add `pytest.ini` with coverage and fail-under settings.

## 5. Dockerization
- Create a multi-stage `Dockerfile` (use `python:3.12-slim`, specify `--platform=linux/amd64`).
- Add `.dockerignore` to exclude tests, notebooks, caches, and large files.

## 6. CI/CD
- Add GitHub Actions workflows for CI and PRs:
  - Matrix for Python 3.12/3.13
  - Steps: checkout, Poetry install, pre-commit, tests, Docker build, image size guard

## 7. Documentation & Contribution
- Add badge slots to `README.md`.
- Add a short `CONTRIBUTING.md`.
- Create a `docs/` folder for project documentation.

## 8. Version Control Hygiene
- Add a `.gitignore` (Poetry + Python + extras).

## 9. Local Validation
- Run:
  ```bash
  poetry run pre-commit install
  poetry run pre-commit run --all-files
  poetry run pytest -q
  docker build -t <project-name>:dev .
  docker images <project-name>:dev
  ```
- Ensure Docker image is <150MB and all tests/linting pass.

---

**Tip:** Keep this file updated as your project evolves to help onboard new contributors and maintain best practices. 