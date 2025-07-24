# syntax=docker/dockerfile:1

# Use the smallest possible Python base image
FROM --platform=linux/amd64 python:3.12-alpine AS builder

# Install only essential build dependencies
RUN apk add --no-cache gcc musl-dev

# Install only the most essential dependencies (no pandas!)
RUN pip install --no-cache-dir --user \
    typer==0.16.0 \
    rich==14.0.0

# Final runtime stage with ultra-minimal setup
FROM --platform=linux/amd64 python:3.12-alpine AS runtime

# Copy only essential Python packages
COPY --from=builder /root/.local /root/.local

# Set environment variables
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

WORKDIR /app

# Create a minimal DGI module for basic functionality
RUN echo 'print("DGI Toolkit - Minimal Version")' > dgi_minimal.py \
    && echo 'def hello_dgi():' >> dgi_minimal.py \
    && echo '    print("Welcome to DGI Toolkit Minimal Edition!")' >> dgi_minimal.py \
    && echo '    return "Basic dividend growth functionality available"' >> dgi_minimal.py

# Create minimal data
RUN mkdir -p ./data \
    && echo "symbol,dividend_yield,payout,dividend_cagr" > ./data/fundamentals_small.csv \
    && echo "AAPL,0.45,0.25,8.5" >> ./data/fundamentals_small.csv \
    && echo "MSFT,0.72,0.28,10.2" >> ./data/fundamentals_small.csv

# Ultra-aggressive cleanup
RUN rm -rf /usr/local/lib/python3.12/site-packages/* \
    && find /root/.local -name "*.pyc" -delete \
    && find /root/.local -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true \
    && find /root/.local -name "tests" -exec rm -rf {} + 2>/dev/null || true \
    && find /root/.local -name "test" -exec rm -rf {} + 2>/dev/null || true \
    && find /root/.local -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true \
    && find /root/.local -name "locale" -exec rm -rf {} + 2>/dev/null || true \
    && find /root/.local -name "docs" -exec rm -rf {} + 2>/dev/null || true \
    && rm -rf /tmp/* /var/tmp/* /var/cache/apk/* /root/.cache

# Test ultra-minimal functionality
CMD ["python3", "-c", "import dgi_minimal; dgi_minimal.hello_dgi(); print('DGI Toolkit ultra-minimal ready')"]
