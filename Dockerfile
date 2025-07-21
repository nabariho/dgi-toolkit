# syntax=docker/dockerfile:1
FROM --platform=linux/amd64 python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.8.2
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Copy only requirements to cache dependencies
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --only main

# Copy source
COPY dgi/ ./dgi/
COPY ai_chat/ ./ai_chat/
COPY notebooks/ ./notebooks/
COPY data/ ./data/
COPY docs/ ./docs/

# Final image
FROM --platform=linux/amd64 python:3.12-slim AS runtime
WORKDIR /app

COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"

CMD ["python3"] 