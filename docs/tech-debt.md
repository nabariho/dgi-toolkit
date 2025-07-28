# Technical Debt - DGI Toolkit

This document tracks technical debt items that need to be addressed to improve code
quality, maintainability, and adherence to enterprise best practices. Each item includes
priority level, effort estimation, and detailed implementation guidance for junior
developers.

## 📋 Technical Debt Overview

### Priority Levels

- 🔴 **Critical**: Blocks production deployment or introduces security risks
- 🟡 **High**: Affects maintainability, scalability, or code quality
- 🟢 **Medium**: Nice-to-have improvements that enhance developer experience
- 🔵 **Low**: Minor improvements or style preferences

### Effort Estimation

- **XS** (1-2 hours): Simple refactoring or configuration changes
- **S** (2-4 hours): Small feature additions or minor architectural changes
- **M** (4-8 hours): Medium complexity changes requiring some design
- **L** (1-2 days): Large changes requiring significant refactoring
- **XL** (2+ days): Major architectural changes

---

## 🚨 **CRITICAL Priority Tasks**

### TD-001: Implement Proper Logging in FastAPI Application 🔴

**Priority**: Critical | **Effort**: S (2-4 hours) | **Component**: API

**Problem**: The FastAPI application in `api/main.py` uses `print()` statements for
error logging instead of proper structured logging. This is not suitable for production
environments.

**Current Code (Line 144 in api/main.py)**:

```python
# Log the error (in production, use proper logging)
print(f"Error in screen_stocks: {e}")
```

**Expected Solution**:

1. Add proper logging configuration to the FastAPI application
2. Replace print statements with structured logging
3. Include request context in error logs
4. Add correlation IDs for tracing

**Implementation Steps**:

1. Create a logger configuration module at `api/logging_config.py`
2. Configure structured JSON logging for production
3. Add middleware to capture request context
4. Replace print statement with proper error logging

**Files to Modify**:

- `api/main.py` (replace print with logger.error)
- `api/logging_config.py` (new file for logging setup)
- `api/__init__.py` (export logging utilities)

**Acceptance Criteria**:

- No print statements in production code
- Structured logging with JSON format
- Request correlation IDs in logs
- Log levels properly configured

---

### TD-002: Add Input Validation and Security Headers 🔴

**Priority**: Critical | **Effort**: S (2-4 hours) | **Component**: API

**Problem**: The FastAPI application lacks comprehensive input validation and security
headers required for enterprise deployment.

**Current Issues**:

- Missing rate limiting
- No CORS configuration
- No security headers (HSTS, CSP, etc.)
- Query parameter validation could be more restrictive

**Implementation Steps**:

1. Add CORS middleware with proper configuration
2. Implement rate limiting using slowapi
3. Add security headers middleware
4. Enhance query parameter validation with custom validators

**Files to Modify**:

- `api/main.py` (add middleware and enhanced validation)
- `pyproject.toml` (add security dependencies)

**Dependencies to Add**:

```toml
slowapi = "^0.1.9"  # Rate limiting
python-multipart = "^0.0.6"  # Form data support
```

**Acceptance Criteria**:

- Rate limiting configured (e.g., 100 requests per minute)
- CORS properly configured for production
- Security headers present in responses
- Enhanced input validation with custom error messages

---

## 🟡 **HIGH Priority Tasks**

### TD-003: Implement Dependency Injection Container 🟡

**Priority**: High | **Effort**: M (4-8 hours) | **Component**: API, Core

**Problem**: The FastAPI application violates the Dependency Inversion Principle by
directly instantiating dependencies in the `get_screener()` function. This makes testing
difficult and coupling tight.

**Current Code (Lines 51-55 in api/main.py)**:

```python
def get_screener() -> Screener:
    """Get configured screener instance."""
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))
    data_path = get_data_path()
    repo = CsvCompanyDataRepository(data_path, validator)
    return Screener(repo, scoring_strategy=DefaultScoring())
```

**Expected Solution**: Implement a proper dependency injection container using FastAPI's
dependency injection system.

**Implementation Steps**:

1. Create dependency providers in `api/dependencies.py`
2. Use FastAPI's `Depends()` for dependency injection
3. Create factory functions for each component
4. Make dependencies configurable through environment variables

**Files to Create/Modify**:

- `api/dependencies.py` (new file for DI container)
- `api/main.py` (use Depends() in endpoints)
- `api/config.py` (new file for API configuration)

**Example Implementation**:

```python
# api/dependencies.py
from fastapi import Depends
from dgi.screener import Screener

async def get_data_repository():
    # Factory for repository
    pass

async def get_screener(repository = Depends(get_data_repository)) -> Screener:
    # Factory for screener
    pass

# api/main.py
@app.get("/api/v1/screen")
async def screen_stocks(
    screener: Screener = Depends(get_screener),
    min_yield: float = Query(...),
    # ... other params
):
    # Use injected screener
    pass
```

**Acceptance Criteria**:

- No direct instantiation in endpoint functions
- Dependencies injected through FastAPI's DI system
- Easy to mock dependencies for testing
- Configuration externalized

---

### TD-004: Add Response Data Transfer Objects (DTOs) 🟡

**Priority**: High | **Effort**: S (2-4 hours) | **Component**: API

**Problem**: The API directly exposes internal data structures and performs manual data
transformation in the endpoint. This violates the separation of concerns and makes the
API brittle to internal changes.

**Current Code (Lines 122-139 in api/main.py)**:

```python
# Convert to response models
results = []
for _, row in top_stocks.iterrows():
    stock = StockResponse(
        symbol=row["symbol"],
        name=row["name"],
        # ... manual field mapping
    )
    results.append(stock)
```

**Expected Solution**: Create proper DTOs and mappers to separate API concerns from
business logic.

**Implementation Steps**:

1. Create comprehensive response DTOs in `api/schemas/`
2. Implement mapper classes for data transformation
3. Add validation and serialization logic
4. Handle edge cases and data type conversions

**Files to Create/Modify**:

- `api/schemas/__init__.py` (new package)
- `api/schemas/responses.py` (response DTOs)
- `api/schemas/requests.py` (request DTOs)
- `api/mappers.py` (transformation logic)
- `api/main.py` (use mappers instead of manual conversion)

**Acceptance Criteria**:

- Clean separation between API and business models
- Centralized data transformation logic
- Proper error handling for data conversion
- Easy to extend with new fields

---

### TD-005: Add Comprehensive Error Handling and Custom Exceptions 🟡

**Priority**: High | **Effort**: M (4-8 hours) | **Component**: API

**Problem**: The API has basic error handling but lacks proper HTTP status codes, custom
exception types, and user-friendly error messages.

**Current Code (Lines 141-148 in api/main.py)**:

```python
except Exception as e:
    # Log the error (in production, use proper logging)
    print(f"Error in screen_stocks: {e}")
    raise HTTPException(
        status_code=500, detail="Internal server error during stock screening"
    ) from e
```

**Expected Solution**: Implement comprehensive error handling with custom exceptions and
proper HTTP status codes.

**Implementation Steps**:

1. Create custom API exception classes
2. Implement global exception handlers
3. Add proper HTTP status codes for different error types
4. Create user-friendly error response models

**Files to Create/Modify**:

- `api/exceptions.py` (custom exception classes)
- `api/error_handlers.py` (global exception handlers)
- `api/schemas/errors.py` (error response models)
- `api/main.py` (register exception handlers)

**Example Implementation**:

```python
# api/exceptions.py
class APIException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code

class ValidationError(APIException):
    def __init__(self, message: str):
        super().__init__(message, 422)

class DataNotFoundError(APIException):
    def __init__(self, message: str = "Data not found"):
        super().__init__(message, 404)
```

**Acceptance Criteria**:

- Proper HTTP status codes for different error types
- User-friendly error messages
- Global exception handling
- Structured error responses

---

### TD-006: Implement Configuration Management 🟡

**Priority**: High | **Effort**: S (2-4 hours) | **Component**: API

**Problem**: The API lacks proper configuration management. Environment variables are
accessed directly and there's no validation or defaults for API-specific settings.

**Current Code (Lines 45-47 in api/main.py)**:

```python
def get_data_path() -> str:
    """Get the data file path from environment or use default."""
    return os.environ.get("DGI_DATA_PATH", "data/fundamentals_small.csv")
```

**Expected Solution**: Implement a proper configuration management system using Pydantic
settings.

**Implementation Steps**:

1. Create API settings class using Pydantic BaseSettings
2. Add validation for all configuration values
3. Support multiple environment files (.env.local, .env.test, etc.)
4. Add configuration validation on startup

**Files to Create/Modify**:

- `api/config.py` (new file for API configuration)
- `api/main.py` (use settings instead of direct env access)
- `.env.example` (add API-specific environment variables)

**Example Implementation**:

```python
# api/config.py
from pydantic import BaseSettings, validator

class APISettings(BaseSettings):
    # Database/Data settings
    data_path: str = "data/fundamentals_small.csv"

    # API settings
    api_title: str = "DGI Toolkit API"
    api_version: str = "1.0.0"
    debug: bool = False

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    @validator("data_path")
    def validate_data_path(cls, v):
        if not v or not v.strip():
            raise ValueError("data_path cannot be empty")
        return v.strip()

    class Config:
        env_file = ".env"
        env_prefix = "DGI_API_"

settings = APISettings()
```

**Acceptance Criteria**:

- All configuration centralized in settings class
- Validation for all configuration values
- Support for different environments
- Clear documentation of all settings

---

## 🟢 **MEDIUM Priority Tasks**

### TD-007: Add API Versioning Strategy 🟢

**Priority**: Medium | **Effort**: S (2-4 hours) | **Component**: API

**Problem**: The API lacks a proper versioning strategy which will make future changes
difficult without breaking existing clients.

**Current Code**: API endpoints are at `/api/v1/` but there's no formal versioning
system.

**Expected Solution**: Implement proper API versioning with support for multiple
versions.

**Implementation Steps**:

1. Create versioned router structure
2. Implement version-specific schemas
3. Add version negotiation middleware
4. Document versioning strategy

**Files to Create/Modify**:

- `api/v1/__init__.py` (version 1 package)
- `api/v1/routers/` (version-specific routers)
- `api/versioning.py` (versioning utilities)
- `api/main.py` (include versioned routers)

---

### TD-008: Add Request/Response Middleware for Observability 🟢

**Priority**: Medium | **Effort**: M (4-8 hours) | **Component**: API

**Problem**: The API lacks observability features like request timing, response size
tracking, and correlation IDs.

**Expected Solution**: Add middleware for comprehensive request/response observability.

**Implementation Steps**:

1. Create timing middleware
2. Add correlation ID middleware
3. Implement request/response logging middleware
4. Add metrics collection (optional)

**Files to Create/Modify**:

- `api/middleware/` (new package for middleware)
- `api/middleware/timing.py`
- `api/middleware/correlation.py`
- `api/middleware/logging.py`

---

### TD-009: Implement Async Data Processing 🟢

**Priority**: Medium | **Effort**: L (1-2 days) | **Component**: API, Core

**Problem**: The API endpoints are marked as `async` but the underlying data processing
is synchronous, which doesn't provide real async benefits.

**Current Code**:

```python
@app.get("/api/v1/screen")
async def screen_stocks(...):  # Async but calls sync methods
    screener = get_screener()
    df = screener.load_universe()  # Sync call
```

**Expected Solution**: Implement truly async data processing where beneficial.

**Implementation Steps**:

1. Identify I/O bound operations that would benefit from async
2. Create async versions of repository methods
3. Use async file I/O for CSV reading
4. Implement proper async error handling

---

### TD-010: Add Data Caching Layer 🟢

**Priority**: Medium | **Effort**: M (4-8 hours) | **Component**: API

**Problem**: The API reloads and processes data on every request, which is inefficient
for frequently accessed data.

**Expected Solution**: Implement a caching layer for processed data with proper
invalidation.

**Implementation Steps**:

1. Add Redis or in-memory caching
2. Implement cache invalidation strategy
3. Add cache warming on startup
4. Monitor cache hit rates

---

## 🔵 **LOW Priority Tasks**

### TD-011: Add API Documentation Enhancements 🔵

**Priority**: Low | **Effort**: XS (1-2 hours) | **Component**: API

**Problem**: The API documentation could be enhanced with better examples, descriptions,
and response schemas.

**Implementation Steps**:

1. Add comprehensive docstrings with examples
2. Enhance OpenAPI schema with better descriptions
3. Add response examples for different scenarios
4. Include error response documentation

---

### TD-012: Implement Health Check Enhancements 🔵

**Priority**: Low | **Effort**: XS (1-2 hours) | **Component**: API

**Problem**: The health check endpoint is basic and doesn't provide detailed health
information.

**Current Code**:

```python
@app.get("/healthz")
async def health_check() -> HealthResponse:
    return HealthResponse(status="up")
```

**Expected Solution**: Enhance health check with dependency status and detailed
information.

**Implementation Steps**:

1. Check data source availability
2. Add dependency health checks
3. Include version and build information
4. Add readiness vs liveness endpoints

---

### TD-013: Add Performance Optimizations 🔵

**Priority**: Low | **Effort**: M (4-8 hours) | **Component**: API, Core

**Problem**: The data processing could be optimized for better performance with large
datasets.

**Expected Solution**: Implement performance optimizations for data processing.

**Implementation Steps**:

1. Profile current performance bottlenecks
2. Implement DataFrame operations optimization
3. Add parallel processing where beneficial
4. Optimize memory usage for large datasets

---

## 📊 **Implementation Guidelines**

### For Junior Developers

#### Getting Started

1. **Pick a task**: Start with LOW or MEDIUM priority tasks to understand the codebase
2. **Read the context**: Understand the problem and current implementation
3. **Follow TDD**: Write tests first, then implement the solution
4. **Small commits**: Make incremental changes with clear commit messages

#### Code Quality Standards

1. **Type hints**: Add proper type annotations to all new code
2. **Documentation**: Update docstrings and relevant documentation
3. **Error handling**: Implement proper exception handling
4. **Testing**: Ensure >85% test coverage for new code

#### Review Process

1. **Self-review**: Run quality checks before creating PR
2. **Test isolation**: Ensure all tests use isolated test data
3. **Documentation**: Update relevant docs with changes
4. **Breaking changes**: Document any breaking changes

### Task Assignment Strategy

#### Week 1-2: Foundation

- TD-007: API Versioning Strategy
- TD-011: API Documentation Enhancements
- TD-012: Health Check Enhancements

#### Week 3-4: Security & Configuration

- TD-002: Input Validation and Security Headers
- TD-006: Configuration Management
- TD-008: Request/Response Middleware

#### Week 5-6: Architecture

- TD-003: Dependency Injection Container
- TD-004: Response DTOs
- TD-005: Error Handling

#### Week 7-8: Production Readiness

- TD-001: Proper Logging
- TD-009: Async Data Processing
- TD-010: Data Caching Layer

---

## 🔄 **Tracking Progress**

### Task Status

- ⏳ **Not Started**: Task identified but not assigned
- 🔄 **In Progress**: Currently being worked on
- ✅ **Complete**: Implementation done and merged
- 🚫 **Blocked**: Waiting for dependencies or decisions

### Update Process

1. Update status when starting work on a task
2. Add implementation notes and decisions made
3. Update effort estimation if significantly different
4. Mark complete when merged to main branch

---

## 📝 **Notes**

### Dependencies Between Tasks

- TD-001 (Logging) should be completed before TD-005 (Error Handling)
- TD-006 (Configuration) should be completed before TD-002 (Security)
- TD-003 (DI Container) affects multiple other tasks

### Future Considerations

- Monitoring and alerting integration
- API Gateway integration
- Database migration from CSV
- Microservices decomposition
- Event-driven architecture

### Reference Materials

- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/usage/settings/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
