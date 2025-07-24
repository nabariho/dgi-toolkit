# syntax=docker/dockerfile:1
FROM --platform=linux/amd64 python:3.12-slim AS builder

WORKDIR /app

# Install only essential build dependencies and clean up aggressively
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Poetry
ENV POETRY_VERSION=1.8.2
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Copy only requirements to cache dependencies
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --only main --no-dev \
    && pip uninstall -y poetry \
    && rm -rf /root/.cache /tmp/* \
    && find /usr/local/lib/python3.12/site-packages -name "*.pyc" -delete \
    && find /usr/local/lib/python3.12/site-packages -name "__pycache__" -exec rm -rf {} + || true

# Copy source (minimal necessary files)
COPY dgi/ ./dgi/
COPY ai_chat/ ./ai_chat/
COPY data/ ./data/

# Final runtime image
FROM --platform=linux/amd64 python:3.12-slim AS runtime
WORKDIR /app

# Copy only the necessary Python packages and source
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/dgi ./dgi
COPY --from=builder /app/ai_chat ./ai_chat
COPY --from=builder /app/data ./data

# Clean up any remaining cache
RUN rm -rf /tmp/* /var/tmp/* /root/.cache \
    && find . -name "*.pyc" -delete \
    && find . -name "__pycache__" -exec rm -rf {} + || true

CMD ["python3"]
