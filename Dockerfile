# syntax=docker/dockerfile:1
FROM --platform=linux/amd64 python:3.12-alpine AS runtime

WORKDIR /app

# Install only essential runtime dependencies (no LangChain bloat)
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev \
    && pip install --no-cache-dir \
        pandas==2.3.1 \
        typer==0.16.0 \
        rich==14.0.0 \
        pydantic==2.11.2 \
        matplotlib==3.10.3 \
    && apk del .build-deps \
    && rm -rf /root/.cache /tmp/* \
    && find /usr/local/lib/python3.12/site-packages -name "*.pyc" -delete \
    && find /usr/local/lib/python3.12/site-packages -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true \
    && find /usr/local/lib/python3.12/site-packages -name "*.pyo" -delete

# Copy only core application files (exclude ai_chat to avoid LangChain)
COPY dgi/ ./dgi/

# Create minimal data directory
RUN mkdir -p ./data
COPY data/fundamentals_small.csv ./data/

# Create non-root user and final cleanup
RUN adduser -D -s /bin/sh appuser \
    && chown -R appuser:appuser /app \
    && rm -rf /tmp/* /var/tmp/* /root/.cache

USER appuser

# Test that core functionality works
CMD ["python3", "-c", "import dgi.screener; import dgi.portfolio; print('DGI Toolkit core ready')"]
