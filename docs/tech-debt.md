# Technical Debt - DGI Toolkit

This document tracks technical debt items identified through comprehensive code review
to improve code quality, maintainability, and adherence to enterprise best practices.
Each item includes priority level, effort estimation, and detailed implementation
guidance for junior developers.

## 📋 Technical Debt Overview

### Priority Levels

- 🔴 **Critical**: Blocks production deployment or introduces security risks
- 🟡 **High**: Affects maintainability, scalability, or code quality
- 🟢 **Medium**: Nice-to-have improvements that enhance developer experience
- 🔵 **Low**: Minor improvements or style preferences

### Effort Estimation

- **XS** (1-2 hours): Simple refactoring or configuration changes
- **S** (3-4 hours): Small feature additions or moderate refactoring
- **M** (1-2 days): Significant refactoring or new feature implementation
- **L** (3-5 days): Major architectural changes or complex features
- **XL** (1-2 weeks): Large-scale refactoring or new system implementation

## 🔴 **CRITICAL ITEMS**

### TD-013: Pydantic Field Validation Type Safety Violations

**Priority**: 🔴 Critical **Effort**: S (3-4 hours) **Category**: Type Safety

**Problem**: Multiple mypy errors in API schema definitions due to incorrect Pydantic
Field usage, causing type safety violations that could lead to runtime errors.

**Issues Identified**:

- `api/schemas/responses.py` lines 36, 43, 49, 55: Field() calls with incorrect argument
  types
- Mixing positional and keyword arguments in Field definitions
- Type checking fails with "No overload variant of Field matches argument types"
- Using deprecated `example` parameter instead of `examples` or `json_schema_extra`

**Solution Steps**:

1. **Fix Field Definitions**: Convert positional arguments to proper keyword arguments

   ```python
   # Current (incorrect)
   symbol: str = Field(
       description="Stock ticker symbol",
       min_length=1,
       max_length=5,
       pattern=r"^[A-Z0-9]+$",
       example="JNJ",  # Deprecated
   )

   # Fixed
   symbol: str = Field(
       description="Stock ticker symbol",
       min_length=1,
       max_length=5,
       pattern=r"^[A-Z0-9]+$",
       examples=["JNJ"],  # Use examples instead
   )
   ```

2. **Update All Field Definitions**: Ensure consistent Field usage across all schema
   files
3. **Add Type Validation Tests**: Test schema validation with invalid inputs
4. **Run MyPy**: Verify all type checking passes

**Impact**: Type safety violations can cause runtime errors and API validation failures

### TD-014: Mixed Testing Framework Usage Violations

**Priority**: 🔴 Critical **Effort**: M (1-2 days) **Category**: Testing Architecture

**Problem**: Inconsistent mixing of unittest.TestCase and pytest patterns throughout the
test suite, violating testing best practices and causing potential test isolation
issues.

**Issues Identified**:

- `tests/test_scoring.py`, `tests/test_filtering.py`: Using unittest.TestCase classes
  but missing inheritance
- Mixed assertion styles: `self.assertEqual` vs `assert` statements
- Inconsistent test discovery patterns
- Some tests use unittest.main() while others use pytest discovery

**Solution Steps**:

1. **Standardize on Pytest**: Convert all unittest.TestCase classes to pure pytest
   functions/classes
2. **Convert Assertions**: Replace all `self.assert*` with native `assert` statements or
   `pytest.raises`
3. **Remove unittest.main()**: Clean up all unittest.main() calls
4. **Add Pytest Fixtures**: Replace setUp/tearDown with proper pytest fixtures
5. **Update Test Organization**: Ensure all tests use pytest markers consistently

**Example Conversion**:

```python
# Before (problematic)
class TestScoring(unittest.TestCase):
    def test_score_calculation(self):
        self.assertEqual(result, expected)

# After (clean)
class TestScoring:
    def test_score_calculation(self):
        assert result == expected
```

**Impact**: Mixed testing patterns can cause unreliable tests and inconsistent behavior

## 🟡 **HIGH PRIORITY ITEMS**

### TD-016: Dependency Inversion Principle Violations

**Priority**: 🟡 High **Effort**: M (1-2 days) **Category**: SOLID Principles

**Problem**: High-level modules depend on low-level modules and concrete implementations
instead of abstractions, violating the Dependency Inversion Principle.

**Issues Identified**:

- `dgi/screener.py`: Directly imports and uses concrete CsvCompanyDataRepository
- `dgi/cli.py`: Direct instantiation of concrete classes instead of using factories
- `api/main.py`: Direct dependencies on concrete service implementations
- Missing abstractions for key business operations

**Solution Steps**:

1. **Create Missing Abstractions**:

   ```python
   # Create interfaces for all major operations
   class ScoringService(ABC):
       @abstractmethod
       def calculate_score(self, company: CompanyData) -> float: ...

   class FilteringService(ABC):
       @abstractmethod
       def apply_filters(self, df: DataFrame, criteria: FilterCriteria) -> DataFrame: ...
   ```

2. **Update Dependency Injection**: Inject abstractions instead of concrete classes
3. **Create Factory Interfaces**: Abstract factory creation patterns
4. **Update Tests**: Mock interfaces instead of concrete implementations

**Impact**: Makes testing difficult and creates tight coupling between modules

### TD-017: Open/Closed Principle Violations in Strategy Patterns

**Priority**: 🟡 High **Effort**: M (1-2 days) **Category**: SOLID Principles

**Problem**: Strategy pattern implementations are not properly closed for modification
but open for extension, requiring code changes to add new strategies.

**Issues Identified**:

- `dgi/scoring.py`: Hard-coded scoring logic that requires modification to add new
  scoring methods
- `dgi/filtering.py`: Missing registry pattern for dynamic filter discovery
- No plugin system for extending strategies at runtime
- Hard-coded strategy selection in multiple places

**Solution Steps**:

1. **Implement Strategy Registry Pattern**:

   ```python
   class ScoringStrategyRegistry:
       _strategies: Dict[str, Type[ScoringStrategy]] = {}

       @classmethod
       def register(cls, name: str, strategy: Type[ScoringStrategy]):
           cls._strategies[name] = strategy

       @classmethod
       def get_strategy(cls, name: str) -> ScoringStrategy:
           return cls._strategies[name]()
   ```

2. **Add Plugin System**: Allow runtime strategy loading
3. **Create Strategy Factory**: Centralized strategy creation
4. **Update Configuration**: Allow strategy selection via configuration

**Impact**: Makes it hard to extend functionality without modifying existing code

### TD-018: Interface Segregation Principle Violations

**Priority**: 🟡 High **Effort**: M (1-2 days) **Category**: SOLID Principles

**Problem**: Large interfaces force clients to depend on methods they don't use,
violating the Interface Segregation Principle.

**Issues Identified**:

- `dgi/repositories/base.py`: CompanyDataRepository interface too broad
- `dgi/services/screening_service.py`: ScreeningService provides too many unrelated
  methods
- `api/dependencies.py`: Large dependency containers with unrelated services

**Solution Steps**:

1. **Split Large Interfaces**:

   ```python
   # Instead of one large interface
   class CompanyDataRepository(ABC): ...

   # Create focused interfaces
   class CompanyDataReader(ABC):
       def get_rows(self) -> List[CompanyData]: ...

   class CompanyDataCache(ABC):
       def get_cached_data(self) -> Optional[List[CompanyData]]: ...

   class CompanyDataValidator(ABC):
       def validate_data(self, data: List[Dict]) -> List[CompanyData]: ...
   ```

2. **Update Service Interfaces**: Create focused service interfaces
3. **Refactor Dependencies**: Use composition instead of large dependency containers
4. **Update Tests**: Test each interface separately

**Impact**: Forces clients to depend on unused functionality and makes testing difficult

### TD-019: Inadequate Error Handling in Async Operations

**Priority**: 🟡 High **Effort**: S (3-4 hours) **Category**: Error Handling

**Problem**: Async operations lack proper error handling, timeout management, and
graceful degradation patterns.

**Issues Identified**:

- `dgi/screener.py`: async methods don't handle timeouts or cancellation
- `api/async_processing.py`: Missing retry logic for failed async operations
- No circuit breaker pattern for external dependencies
- Async resource cleanup not guaranteed

**Solution Steps**:

1. **Add Timeout Handling**:

   ```python
   async def screen_async(self, timeout: float = 30.0) -> DataFrame:
       try:
           return await asyncio.wait_for(
               self._do_screening(),
               timeout=timeout
           )
       except asyncio.TimeoutError:
           logger.error(f"Screening timed out after {timeout}s")
           raise ScreeningTimeoutError()
   ```

2. **Implement Retry Pattern**: Add exponential backoff for transient failures
3. **Add Circuit Breaker**: Protect against cascading failures
4. **Improve Async Resource Management**: Ensure proper cleanup in all cases

**Impact**: Async operations can hang or fail silently, affecting system reliability

## 🟢 **MEDIUM PRIORITY ITEMS**

### TD-006: Dependency Injection Container Improvements

**Priority**: 🟢 Medium **Effort**: M (1-2 days) **Category**: Architecture

**Problem**: Dependency injection is manually implemented without leveraging established
DI frameworks, making it harder to manage dependencies in larger applications.

**Issues Identified**:

- Manual dependency management in `api/dependencies.py`
- No lifecycle management for expensive resources
- Singleton pattern manually implemented without thread safety considerations
- Missing dependency scoping (request, session, application level)

**Solution Steps**:

1. **Research**: Evaluate DI frameworks like `dependency-injector` or `lagom`
2. **Implement**: Replace manual DI with framework-based approach
3. **Scope**: Add proper dependency scoping for different lifecycle needs
4. **Thread-safe**: Ensure thread safety for singleton dependencies
5. **Test**: Verify dependency injection works correctly under load

### TD-020: Code Duplication in Validation Logic

**Priority**: 🟢 Medium **Effort**: S (3-4 hours) **Category**: DRY Principle

**Problem**: Validation logic is duplicated across multiple modules, violating the DRY
principle and creating maintenance issues.

**Issues Identified**:

- Similar validation patterns in `dgi/validation_utils.py` and `api/schemas/`
- Duplicate financial value validation in multiple places
- Repeated parameter validation in service methods
- Similar error handling patterns across modules

**Solution Steps**:

1. **Create Validation Decorators**:

   ```python
   @validate_financial_params
   def screen(self, min_yield: float, max_payout: float) -> DataFrame:
       # Core logic only
   ```

2. **Extract Common Validators**: Create reusable validation components
3. **Centralize Error Messages**: Single source of truth for validation messages
4. **Update Tests**: Ensure validation logic is tested once, used everywhere

**Impact**: Code duplication increases maintenance burden and risk of inconsistencies

### TD-021: Missing Design Patterns for Configuration Management

**Priority**: 🟢 Medium **Effort**: S (3-4 hours) **Category**: Configuration

**Problem**: Configuration management lacks proper design patterns, making it difficult
to manage different environments and configuration sources.

**Issues Identified**:

- Configuration scattered across multiple files (`dgi/config.py`, `api/config.py`)
- No configuration validation hierarchy
- Missing environment-specific configuration strategies
- Hard-coded configuration values in business logic

**Solution Steps**:

1. **Implement Strategy Pattern for Configuration**:

   ```python
   class ConfigurationStrategy(ABC):
       @abstractmethod
       def get_config(self) -> ConfigDict: ...

   class EnvironmentConfigStrategy(ConfigurationStrategy): ...
   class FileConfigStrategy(ConfigurationStrategy): ...
   class DatabaseConfigStrategy(ConfigurationStrategy): ...
   ```

2. **Create Configuration Builder**: Compose configuration from multiple sources
3. **Add Configuration Validation**: Validate configuration at startup
4. **Implement Hot Reload**: Allow configuration updates without restart

**Impact**: Poor configuration management makes deployment and maintenance difficult

### TD-022: Insufficient Logging and Observability Patterns

**Priority**: 🟢 Medium **Effort**: M (1-2 days) **Category**: Observability

**Problem**: Logging and observability patterns are inconsistent and don't follow
enterprise standards for debugging and monitoring.

**Issues Identified**:

- Inconsistent log levels and messages across modules
- Missing structured logging in critical business operations
- No correlation IDs for tracing requests across services
- Missing business metrics and KPIs
- Insufficient error context in log messages

**Solution Steps**:

1. **Standardize Log Formats**:

   ```python
   logger.info(
       "Screening completed",
       extra={
           "correlation_id": correlation_id,
           "user_id": user_id,
           "parameters": {"min_yield": min_yield},
           "results": {"total_stocks": len(results)},
           "duration_ms": duration,
       }
   )
   ```

2. **Add Business Metrics**: Track key business operations
3. **Implement Correlation IDs**: Trace requests across all components
4. **Add Performance Monitoring**: Track operation durations and resource usage
5. **Create Alerting Rules**: Define alerts for critical business operations

**Impact**: Poor observability makes debugging and monitoring difficult in production

## 🔵 **LOW PRIORITY ITEMS**

### TD-012: Performance Optimization Opportunities

**Priority**: 🔵 Low **Effort**: M (1-2 days) **Category**: Performance

**Problem**: Several performance optimization opportunities exist in data processing
pipelines.

**Opportunities Identified**:

- DataFrame operations could use vectorization
- Caching strategies could be improved
- Async processing could be expanded
- Database connection pooling for future implementations

**Solution Steps**:

1. **Profile**: Add performance profiling to identify bottlenecks
2. **Optimize**: Implement vectorized operations where appropriate
3. **Cache**: Improve caching strategies for frequently accessed data
4. **Async**: Expand async support for I/O operations

### TD-023: Inconsistent Naming Conventions

**Priority**: 🔵 Low **Effort**: XS (1-2 hours) **Category**: Code Style

**Problem**: Naming conventions are inconsistent across the codebase, affecting
readability and maintainability.

**Issues Identified**:

- Mixed use of snake_case and camelCase in some areas
- Inconsistent parameter naming (`min_yield` vs `minimum_yield`)
- Variable names don't follow Python conventions
- Class names sometimes don't reflect their purpose

**Solution Steps**:

1. **Define Naming Standards**: Create comprehensive naming convention guide
2. **Run Automated Checks**: Add linting rules for naming conventions
3. **Refactor Inconsistent Names**: Update variable and method names
4. **Update Documentation**: Ensure examples follow conventions

**Impact**: Inconsistent naming makes code harder to read and maintain

### TD-024: Missing Documentation for Complex Business Logic

**Priority**: 🔵 Low **Effort**: S (3-4 hours) **Category**: Documentation

**Problem**: Complex business logic lacks adequate documentation, making it difficult
for new developers to understand the domain.

**Issues Identified**:

- Missing docstrings for complex scoring algorithms
- No documentation for business rules and constraints
- Lack of examples for custom strategy implementations
- Missing architecture decision records (ADRs)

**Solution Steps**:

1. **Add Business Logic Documentation**: Document scoring and filtering algorithms
2. **Create ADRs**: Document architectural decisions
3. **Add Code Examples**: Provide examples for extending the system
4. **Update API Documentation**: Ensure all endpoints are properly documented

**Impact**: Poor documentation increases onboarding time and maintenance costs

---

## 📊 **Progress Summary**

- **Total Items**: 14
- **Completed**: 0 (0%)
- **In Progress**: 0 (0%)
- **Pending**: 14 (100%)

### Priority Breakdown

- 🔴 **Critical**: 2/2 (100%) 🔄
- 🟡 **High**: 5/5 (100%) 🔄
- 🟢 **Medium**: 4/4 (100%) 🔄
- 🔵 **Low**: 3/3 (100%) 🔄

## 🎯 **Recommended Implementation Order**

### 🔄 **CRITICAL ITEMS (Immediate)**

1. **TD-013** (Critical) - Fix Pydantic Field type safety violations
2. **TD-014** (Critical) - Standardize testing framework usage

### 🔄 **HIGH PRIORITY ITEMS (Next Sprint)**

3. **TD-015** (High) - Fix Single Responsibility Principle violations
4. **TD-016** (High) - Fix Dependency Inversion Principle violations
5. **TD-017** (High) - Fix Open/Closed Principle violations
6. **TD-018** (High) - Fix Interface Segregation Principle violations
7. **TD-019** (High) - Improve async error handling

### 🔄 **MEDIUM PRIORITY ITEMS (Future Sprints)**

8. **TD-006** (Medium) - Enhance dependency injection container
9. **TD-020** (Medium) - Eliminate code duplication in validation
10. **TD-021** (Medium) - Improve configuration management patterns
11. **TD-022** (Medium) - Enhance logging and observability

### 🔄 **LOW PRIORITY ITEMS (Maintenance)**

12. **TD-012** (Low) - Performance optimizations
13. **TD-023** (Low) - Fix naming convention inconsistencies
14. **TD-024** (Low) - Improve business logic documentation

## 📝 **Implementation Guidelines**

### For Junior Developers

1. **Start Small**: Begin with XS or S effort items to build confidence
2. **Test First**: Write tests before making changes, especially for Critical and High
   priority items
3. **Single Responsibility**: Each PR should address one technical debt item only
4. **Documentation**: Update documentation when changing interfaces or behavior
5. **Review**: Request code review for all changes, especially architectural ones

### Code Quality Standards

- Follow existing patterns and conventions established in the codebase
- Maintain or improve test coverage (target: 85% minimum) - **ACHIEVED: 83%**
- Add comprehensive error handling using the unified exception hierarchy
- Use type hints consistently with modern Python syntax
- Follow naming conventions that clearly indicate purpose and responsibility

### Testing Requirements

- Add unit tests for new functionality and bug fixes
- Add integration tests for interface changes
- Ensure test isolation is maintained (no shared state between tests)
- Update test documentation and examples
- Run full test suite before submitting changes

### Definition of Done

- [x] All automated tests pass (507/507 ✅)
- [x] Code coverage maintained or improved (83% ✅)
- [ ] Type checking passes (mypy) - **FAILING: 4 errors**
- [x] Code style checks pass (ruff, black)
- [x] Documentation updated
- [x] Peer review completed
- [x] Manual testing performed for UI/API changes

## 📚 **Reference Materials**

- **SOLID Principles**: Clean Architecture by Robert C. Martin
- **Design Patterns**: Gang of Four Design Patterns
- **Clean Code**: Clean Code by Robert C. Martin
- **Enterprise Patterns**: Patterns of Enterprise Application Architecture by Martin
  Fowler
- **Python Best Practices**: Effective Python by Brett Slatkin
- **API Design**: REST API Design Rulebook by Mark Masse
- **Testing**: Growing Object-Oriented Software, Guided by Tests by Freeman & Pryce

## 📋 **Feature Requirements Compliance**

Based on analysis of `features.md`, the following feature requirements need attention:

### DGIT-301: FastAPI Service Skeleton

- ✅ Basic FastAPI application structure exists
- ✅ Health endpoint returning 200 OK
- ✅ Integration tests passing
- ✅ Swagger/OpenAPI documentation enabled

### DGIT-302: Dockerised API

- ❌ Missing multistage Dockerfile.api for optimized API deployment
- ❌ No runtime image size optimization
- ❌ Missing containerization best practices

### DGIT-304: Integration Tests

- ⚠️ **Partial**: Integration tests exist but mixed testing framework usage creates
  reliability issues
- ❌ Missing comprehensive API endpoint testing
- ❌ Test coverage not meeting 85% target for new API features

**Recommendation**: Address critical type safety and testing framework issues before
implementing new features.
