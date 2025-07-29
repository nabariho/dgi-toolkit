# DGI Toolkit API Usage Guide

This guide provides comprehensive documentation for using the DGI Toolkit API, including
examples, best practices, and integration patterns.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Endpoints](#endpoints)
5. [Error Handling](#error-handling)
6. [Code Examples](#code-examples)
7. [Best Practices](#best-practices)

## Getting Started

### Base URL

```
Development: http://localhost:8000
Production: https://your-domain.com
```

### API Versioning

The API supports versioning through URL prefixes:

- **v1**: `/api/v1/` (current stable version)
- **Legacy**: `/` (deprecated, use v1 endpoints)

### Quick Start

```bash
# Check API health
curl http://localhost:8000/healthz

# Get API information
curl http://localhost:8000/api/v1/

# Screen stocks
curl "http://localhost:8000/api/v1/screen?min_yield=0.02&max_payout=80&min_cagr=0.05&top_n=10"
```

## Authentication

Currently, the API does not require authentication. However, rate limiting is enforced
to ensure fair usage.

## Rate Limiting

- **Limit**: 100 requests per 60 seconds (configurable)
- **Headers**: Rate limit information is included in response headers
- **Exceeded**: Returns 429 status code with retry information

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642234567
```

## Endpoints

### 1. Health Check

#### GET `/healthz` (Legacy)

#### GET `/api/v1/health` (Versioned)

Check the health status of the API and system metrics.

**Response Example:**

```json
{
  "status": "up",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "environment": "production",
  "uptime_seconds": 3600.5,
  "memory_usage_mb": 45.2,
  "cpu_usage_percent": 2.1,
  "data_file_status": "accessible",
  "data_file_size_mb": 1.2
}
```

**Use Cases:**

- Load balancer health checks
- Monitoring system integration
- DevOps pipeline verification

### 2. API Information

#### GET `/` (Legacy)

#### GET `/api/v1/` (Versioned)

Get information about the API and available endpoints.

**Response Example:**

```json
{
  "message": "DGI Toolkit API v1",
  "version": "1.0.0",
  "docs_url": "/docs",
  "health_url": "/api/v1/health",
  "endpoints": ["/api/v1/screen", "/api/v1/health", "/docs", "/redoc"],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 3. Stock Screening

#### GET `/api/v1/screen`

Screen stocks using Dividend Growth Investing (DGI) criteria.

**Parameters:**

- `min_yield` (float, optional): Minimum dividend yield (default: 0.02)
- `max_payout` (float, optional): Maximum payout ratio (default: 80.0)
- `min_cagr` (float, optional): Minimum dividend CAGR (default: 0.05)
- `top_n` (int, optional): Number of top stocks to return (default: 10)

**Example Request:**

```bash
curl "http://localhost:8000/api/v1/screen?min_yield=0.03&max_payout=60&min_cagr=0.08&top_n=5"
```

**Response Example:**

```json
{
  "stocks": [
    {
      "symbol": "JNJ",
      "name": "Johnson & Johnson",
      "sector": "Healthcare",
      "industry": "Drug Manufacturers",
      "dividend_yield": 0.025,
      "payout": 45.2,
      "dividend_cagr": 0.065,
      "fcf_yield": 4.8,
      "score": 0.82
    }
  ],
  "total_count": 1,
  "filters_applied": {
    "min_yield": 0.03,
    "max_payout": 60.0,
    "min_cagr": 0.08,
    "top_n": 5
  },
  "processing_time_ms": 15.23
}
```

## Error Handling

The API uses standard HTTP status codes and provides detailed error information.

### Error Response Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "status_code": 400,
    "details": {
      "additional_info": "value"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "correlation_id": "req-12345"
}
```

### Common Error Codes

| Status | Code                  | Description                |
| ------ | --------------------- | -------------------------- |
| 400    | `VALIDATION_ERROR`    | Invalid request parameters |
| 422    | `VALIDATION_ERROR`    | Request validation failed  |
| 429    | `RATE_LIMIT_EXCEEDED` | Rate limit exceeded        |
| 500    | `INTERNAL_ERROR`      | Internal server error      |

## Code Examples

### Python

```python
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000"

# Health check
def check_health():
    response = requests.get(f"{BASE_URL}/healthz")
    return response.json()

# Screen stocks
def screen_stocks(min_yield=0.02, max_payout=80.0, min_cagr=0.05, top_n=10):
    params = {
        "min_yield": min_yield,
        "max_payout": max_payout,
        "min_cagr": min_cagr,
        "top_n": top_n
    }
    response = requests.get(f"{BASE_URL}/api/v1/screen", params=params)
    return response.json()

# Example usage
if __name__ == "__main__":
    # Check health
    health = check_health()
    print(f"API Status: {health['status']}")

    # Screen for high-yield stocks
    stocks = screen_stocks(min_yield=0.03, max_payout=60, top_n=5)
    print(f"Found {stocks['total_count']} stocks")

    for stock in stocks['stocks']:
        print(f"{stock['symbol']}: {stock['dividend_yield']:.1%} yield")
```

### JavaScript/Node.js

```javascript
const axios = require("axios");

const BASE_URL = "http://localhost:8000";

// Health check
async function checkHealth() {
  try {
    const response = await axios.get(`${BASE_URL}/healthz`);
    return response.data;
  } catch (error) {
    console.error("Health check failed:", error.response?.data);
    throw error;
  }
}

// Screen stocks
async function screenStocks(params = {}) {
  const defaultParams = {
    min_yield: 0.02,
    max_payout: 80.0,
    min_cagr: 0.05,
    top_n: 10,
  };

  const requestParams = { ...defaultParams, ...params };

  try {
    const response = await axios.get(`${BASE_URL}/api/v1/screen`, {
      params: requestParams,
    });
    return response.data;
  } catch (error) {
    console.error("Stock screening failed:", error.response?.data);
    throw error;
  }
}

// Example usage
async function main() {
  try {
    // Check health
    const health = await checkHealth();
    console.log(`API Status: ${health.status}`);

    // Screen for dividend growth stocks
    const stocks = await screenStocks({
      min_yield: 0.02,
      max_payout: 60,
      min_cagr: 0.08,
      top_n: 5,
    });

    console.log(`Found ${stocks.total_count} stocks`);
    stocks.stocks.forEach((stock) => {
      console.log(`${stock.symbol}: ${(stock.dividend_yield * 100).toFixed(1)}% yield`);
    });
  } catch (error) {
    console.error("Error:", error.message);
  }
}

main();
```

### cURL

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"

# Health check
echo "Checking API health..."
curl -s "${BASE_URL}/healthz" | jq '.'

# Screen stocks
echo "Screening stocks..."
curl -s "${BASE_URL}/api/v1/screen?min_yield=0.03&max_payout=60&top_n=3" | jq '.'
```

## Best Practices

### 1. Error Handling

Always implement proper error handling:

```python
try:
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
except json.JSONDecodeError as e:
    print(f"Invalid JSON response: {e}")
```

### 2. Rate Limiting

Respect rate limits and implement exponential backoff:

```python
import time
import random

def make_request_with_retry(url, params, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params)
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                time.sleep(retry_after + random.uniform(0, 1))
                continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt + random.uniform(0, 1))
```

### 3. Parameter Validation

Validate parameters before making requests:

```python
def validate_screening_params(min_yield, max_payout, min_cagr, top_n):
    if not (0 <= min_yield <= 1):
        raise ValueError("min_yield must be between 0 and 1")
    if not (0 <= max_payout <= 200):
        raise ValueError("max_payout must be between 0 and 200")
    if not (-1 <= min_cagr <= 1):
        raise ValueError("min_cagr must be between -1 and 1")
    if not (1 <= top_n <= 100):
        raise ValueError("top_n must be between 1 and 100")
```

### 4. Caching

Implement caching for frequently requested data:

```python
import functools
import time

def cache_result(ttl_seconds=300):
    def decorator(func):
        cache = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(sorted(kwargs.items()))
            now = time.time()

            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl_seconds:
                    return result

            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result

        return wrapper
    return decorator

@cache_result(ttl_seconds=300)  # Cache for 5 minutes
def screen_stocks_cached(**params):
    return screen_stocks(**params)
```

### 5. Monitoring

Monitor API usage and performance:

```python
import time
import logging

logger = logging.getLogger(__name__)

def monitor_api_call(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"API call {func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"API call {func.__name__} failed after {duration:.2f}s: {e}")
            raise
    return wrapper

@monitor_api_call
def screen_stocks_monitored(**params):
    return screen_stocks(**params)
```

## Support

For additional support or questions:

1. **Documentation**: Visit `/docs` for interactive API documentation
2. **Health Check**: Use `/healthz` to verify API status
3. **Error Details**: Check error responses for specific issue information
4. **Rate Limits**: Monitor response headers for rate limit information

## Version History

- **v1.0.0**: Initial release with stock screening and health monitoring
- **v1.1.0**: Added advanced health checks with system metrics
- **v1.2.0**: Enhanced API documentation and examples
