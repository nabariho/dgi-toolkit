"""Tests for DGI Toolkit exceptions."""

import unittest

from dgi.exceptions import (
    CLIError,
    ConfigurationError,
    DataAccessError,
    DataCorruptionError,
    DataFrameValidationError,
    DataNotFoundError,
    DataValidationError,
    DGIException,
    FactoryError,
    FilterError,
    PathValidationError,
    PerformanceError,
    PortfolioError,
    RepositoryError,
    ResourceError,
    ScoringError,
    ScreeningError,
    SecurityValidationError,
    ServiceError,
    URLValidationError,
    UserInputError,
    ValidationError,
)


class TestDGIException(unittest.TestCase):
    """Tests for base DGIException class."""

    def test_dgi_exception_basic(self) -> None:
        """Test basic DGIException initialization."""
        exception = DGIException("Test error message")

        self.assertEqual(str(exception), "Test error message")
        self.assertEqual(exception.message, "Test error message")
        self.assertEqual(exception.details, {})

    def test_dgi_exception_with_details(self) -> None:
        """Test DGIException with additional details."""
        details = {"field": "test_field", "value": 123}
        exception = DGIException("Test error message", details)

        self.assertEqual(str(exception), "Test error message")
        self.assertEqual(exception.message, "Test error message")
        self.assertEqual(exception.details, details)

    def test_dgi_exception_inheritance(self) -> None:
        """Test that DGIException inherits from Exception."""
        exception = DGIException("Test error message")

        self.assertIsInstance(exception, Exception)
        self.assertIsInstance(exception, DGIException)


class TestDataValidationError(unittest.TestCase):
    """Tests for DataValidationError class."""

    def test_data_validation_error_basic(self) -> None:
        """Test basic DataValidationError initialization."""
        exception = DataValidationError("Validation failed")

        self.assertEqual(str(exception), "Validation failed")
        self.assertEqual(exception.message, "Validation failed")
        self.assertEqual(exception.details, {})

    def test_data_validation_error_with_field(self) -> None:
        """Test DataValidationError with field information."""
        exception = DataValidationError("Invalid value", field="test_field")

        self.assertEqual(str(exception), "Invalid value")
        self.assertEqual(exception.details, {"field": "test_field"})

    def test_data_validation_error_with_value(self) -> None:
        """Test DataValidationError with value information."""
        exception = DataValidationError("Invalid value", value=123)

        self.assertEqual(str(exception), "Invalid value")
        self.assertEqual(exception.details, {"value": 123})

    def test_data_validation_error_with_field_and_value(self) -> None:
        """Test DataValidationError with both field and value."""
        exception = DataValidationError("Invalid value", field="test_field", value=123)

        self.assertEqual(str(exception), "Invalid value")
        self.assertEqual(exception.details, {"field": "test_field", "value": 123})

    def test_data_validation_error_inheritance(self) -> None:
        """Test that DataValidationError inherits from DGIException."""
        exception = DataValidationError("Validation failed")

        self.assertIsInstance(exception, DGIException)
        self.assertIsInstance(exception, DataValidationError)


class TestSecurityValidationError(unittest.TestCase):
    """Tests for SecurityValidationError class."""

    def test_security_validation_error(self) -> None:
        """Test SecurityValidationError initialization."""
        exception = SecurityValidationError("Security validation failed", field="input")

        self.assertEqual(str(exception), "Security validation failed")
        self.assertEqual(exception.details, {"field": "input"})

    def test_security_validation_error_inheritance(self) -> None:
        """Test that SecurityValidationError inherits from DataValidationError."""
        exception = SecurityValidationError("Security validation failed")

        self.assertIsInstance(exception, DataValidationError)
        self.assertIsInstance(exception, SecurityValidationError)


class TestPathValidationError(unittest.TestCase):
    """Tests for PathValidationError class."""

    def test_path_validation_error(self) -> None:
        """Test PathValidationError initialization."""
        exception = PathValidationError(
            "Invalid path", field="file_path", value="/etc/passwd"
        )

        self.assertEqual(str(exception), "Invalid path")
        self.assertEqual(
            exception.details, {"field": "file_path", "value": "/etc/passwd"}
        )

    def test_path_validation_error_inheritance(self) -> None:
        """Test that PathValidationError inherits from DataValidationError."""
        exception = PathValidationError("Invalid path")

        self.assertIsInstance(exception, DataValidationError)
        self.assertIsInstance(exception, PathValidationError)


class TestURLValidationError(unittest.TestCase):
    """Tests for URLValidationError class."""

    def test_url_validation_error(self) -> None:
        """Test URLValidationError initialization."""
        exception = URLValidationError(
            "Invalid URL", field="api_url", value="not-a-url"
        )

        self.assertEqual(str(exception), "Invalid URL")
        self.assertEqual(exception.details, {"field": "api_url", "value": "not-a-url"})

    def test_url_validation_error_inheritance(self) -> None:
        """Test that URLValidationError inherits from DataValidationError."""
        exception = URLValidationError("Invalid URL")

        self.assertIsInstance(exception, DataValidationError)
        self.assertIsInstance(exception, URLValidationError)


class TestDataFrameValidationError(unittest.TestCase):
    """Tests for DataFrameValidationError class."""

    def test_dataframe_validation_error(self) -> None:
        """Test DataFrameValidationError initialization."""
        exception = DataFrameValidationError(
            "DataFrame validation failed", field="data"
        )

        self.assertEqual(str(exception), "DataFrame validation failed")
        self.assertEqual(exception.details, {"field": "data"})

    def test_dataframe_validation_error_inheritance(self) -> None:
        """Test that DataFrameValidationError inherits from DataValidationError."""
        exception = DataFrameValidationError("DataFrame validation failed")

        self.assertIsInstance(exception, DataValidationError)
        self.assertIsInstance(exception, DataFrameValidationError)


class TestScreeningError(unittest.TestCase):
    """Tests for ScreeningError class."""

    def test_screening_error_basic(self) -> None:
        """Test basic ScreeningError initialization."""
        exception = ScreeningError("Screening failed")

        self.assertEqual(str(exception), "Screening failed")
        self.assertEqual(exception.message, "Screening failed")
        self.assertEqual(exception.details, {})

    def test_screening_error_with_operation(self) -> None:
        """Test ScreeningError with operation information."""
        exception = ScreeningError("Screening failed", operation="filter")

        self.assertEqual(str(exception), "Screening failed")
        self.assertEqual(exception.details, {"operation": "filter"})

    def test_screening_error_inheritance(self) -> None:
        """Test that ScreeningError inherits from DGIException."""
        exception = ScreeningError("Screening failed")

        self.assertIsInstance(exception, DGIException)
        self.assertIsInstance(exception, ScreeningError)


class TestFilterError(unittest.TestCase):
    """Tests for FilterError class."""

    def test_filter_error(self) -> None:
        """Test FilterError initialization."""
        exception = FilterError("Filter failed", operation="yield_filter")

        self.assertEqual(str(exception), "Filter failed")
        self.assertEqual(exception.details, {"operation": "yield_filter"})

    def test_filter_error_inheritance(self) -> None:
        """Test that FilterError inherits from ScreeningError."""
        exception = FilterError("Filter failed")

        self.assertIsInstance(exception, ScreeningError)
        self.assertIsInstance(exception, FilterError)


class TestScoringError(unittest.TestCase):
    """Tests for ScoringError class."""

    def test_scoring_error(self) -> None:
        """Test ScoringError initialization."""
        exception = ScoringError("Scoring failed", operation="dividend_yield")

        self.assertEqual(str(exception), "Scoring failed")
        self.assertEqual(exception.details, {"operation": "dividend_yield"})

    def test_scoring_error_inheritance(self) -> None:
        """Test that ScoringError inherits from ScreeningError."""
        exception = ScoringError("Scoring failed")

        self.assertIsInstance(exception, ScreeningError)
        self.assertIsInstance(exception, ScoringError)


class TestPortfolioError(unittest.TestCase):
    """Tests for PortfolioError class."""

    def test_portfolio_error_basic(self) -> None:
        """Test basic PortfolioError initialization."""
        exception = PortfolioError("Portfolio operation failed")

        self.assertEqual(str(exception), "Portfolio operation failed")
        self.assertEqual(exception.message, "Portfolio operation failed")
        self.assertEqual(exception.details, {})

    def test_portfolio_error_with_portfolio_id(self) -> None:
        """Test PortfolioError with portfolio ID."""
        exception = PortfolioError(
            "Portfolio operation failed", portfolio_id="portfolio_123"
        )

        self.assertEqual(str(exception), "Portfolio operation failed")
        self.assertEqual(exception.details, {"portfolio_id": "portfolio_123"})

    def test_portfolio_error_inheritance(self) -> None:
        """Test that PortfolioError inherits from DGIException."""
        exception = PortfolioError("Portfolio operation failed")

        self.assertIsInstance(exception, DGIException)
        self.assertIsInstance(exception, PortfolioError)


class TestRepositoryError(unittest.TestCase):
    """Tests for RepositoryError class."""

    def test_repository_error_basic(self) -> None:
        """Test basic RepositoryError initialization."""
        exception = RepositoryError("Repository operation failed")

        self.assertEqual(str(exception), "Repository operation failed")
        self.assertEqual(exception.message, "Repository operation failed")
        self.assertEqual(exception.details, {})

    def test_repository_error_with_repository(self) -> None:
        """Test RepositoryError with repository information."""
        exception = RepositoryError(
            "Repository operation failed", repository="csv_repo"
        )

        self.assertEqual(str(exception), "Repository operation failed")
        self.assertEqual(exception.details, {"repository": "csv_repo"})

    def test_repository_error_with_operation(self) -> None:
        """Test RepositoryError with operation information."""
        exception = RepositoryError("Repository operation failed", operation="read")

        self.assertEqual(str(exception), "Repository operation failed")
        self.assertEqual(exception.details, {"operation": "read"})

    def test_repository_error_with_repository_and_operation(self) -> None:
        """Test RepositoryError with both repository and operation."""
        exception = RepositoryError(
            "Repository operation failed", repository="csv_repo", operation="write"
        )

        self.assertEqual(str(exception), "Repository operation failed")
        self.assertEqual(
            exception.details, {"repository": "csv_repo", "operation": "write"}
        )

    def test_repository_error_inheritance(self) -> None:
        """Test that RepositoryError inherits from DGIException."""
        exception = RepositoryError("Repository operation failed")

        self.assertIsInstance(exception, DGIException)
        self.assertIsInstance(exception, RepositoryError)


class TestDataNotFoundError(unittest.TestCase):
    """Tests for DataNotFoundError class."""

    def test_data_not_found_error(self) -> None:
        """Test DataNotFoundError initialization."""
        exception = DataNotFoundError(
            "Data not found", repository="csv_repo", operation="read"
        )

        self.assertEqual(str(exception), "Data not found")
        self.assertEqual(
            exception.details, {"repository": "csv_repo", "operation": "read"}
        )

    def test_data_not_found_error_inheritance(self) -> None:
        """Test that DataNotFoundError inherits from RepositoryError."""
        exception = DataNotFoundError("Data not found")

        self.assertIsInstance(exception, RepositoryError)
        self.assertIsInstance(exception, DataNotFoundError)


class TestDataCorruptionError(unittest.TestCase):
    """Tests for DataCorruptionError class."""

    def test_data_corruption_error(self) -> None:
        """Test DataCorruptionError initialization."""
        exception = DataCorruptionError(
            "Data corrupted", repository="csv_repo", operation="read"
        )

        self.assertEqual(str(exception), "Data corrupted")
        self.assertEqual(
            exception.details, {"repository": "csv_repo", "operation": "read"}
        )

    def test_data_corruption_error_inheritance(self) -> None:
        """Test that DataCorruptionError inherits from RepositoryError."""
        exception = DataCorruptionError("Data corrupted")

        self.assertIsInstance(exception, RepositoryError)
        self.assertIsInstance(exception, DataCorruptionError)


class TestDataAccessError(unittest.TestCase):
    """Tests for DataAccessError class."""

    def test_data_access_error(self) -> None:
        """Test DataAccessError initialization."""
        exception = DataAccessError(
            "Access denied", repository="csv_repo", operation="write"
        )

        self.assertEqual(str(exception), "Access denied")
        self.assertEqual(
            exception.details, {"repository": "csv_repo", "operation": "write"}
        )

    def test_data_access_error_inheritance(self) -> None:
        """Test that DataAccessError inherits from RepositoryError."""
        exception = DataAccessError("Access denied")

        self.assertIsInstance(exception, RepositoryError)
        self.assertIsInstance(exception, DataAccessError)


class TestConfigurationError(unittest.TestCase):
    """Tests for ConfigurationError class."""

    def test_configuration_error_basic(self) -> None:
        """Test basic ConfigurationError initialization."""
        exception = ConfigurationError("Configuration error")

        self.assertEqual(str(exception), "Configuration error")
        self.assertEqual(exception.message, "Configuration error")
        self.assertEqual(exception.details, {})

    def test_configuration_error_with_config_key(self) -> None:
        """Test ConfigurationError with config key."""
        exception = ConfigurationError("Configuration error", config_key="api_key")

        self.assertEqual(str(exception), "Configuration error")
        self.assertEqual(exception.details, {"config_key": "api_key"})

    def test_configuration_error_inheritance(self) -> None:
        """Test that ConfigurationError inherits from DGIException."""
        exception = ConfigurationError("Configuration error")

        self.assertIsInstance(exception, DGIException)
        self.assertIsInstance(exception, ConfigurationError)


class TestFactoryError(unittest.TestCase):
    """Tests for FactoryError class."""

    def test_factory_error_basic(self) -> None:
        """Test basic FactoryError initialization."""
        exception = FactoryError("Factory error")

        self.assertEqual(str(exception), "Factory error")
        self.assertEqual(exception.message, "Factory error")
        self.assertEqual(exception.details, {})

    def test_factory_error_with_factory_name(self) -> None:
        """Test FactoryError with factory name."""
        exception = FactoryError("Factory error", factory_name="provider_factory")

        self.assertEqual(str(exception), "Factory error")
        self.assertEqual(exception.details, {"factory_name": "provider_factory"})

    def test_factory_error_inheritance(self) -> None:
        """Test that FactoryError inherits from DGIException."""
        exception = FactoryError("Factory error")

        self.assertIsInstance(exception, DGIException)
        self.assertIsInstance(exception, FactoryError)


class TestServiceError(unittest.TestCase):
    """Tests for ServiceError class."""

    def test_service_error_basic(self) -> None:
        """Test basic ServiceError initialization."""
        exception = ServiceError("Service error")

        self.assertEqual(str(exception), "Service error")
        self.assertEqual(exception.message, "Service error")
        self.assertEqual(exception.details, {})

    def test_service_error_with_service(self) -> None:
        """Test ServiceError with service information."""
        exception = ServiceError("Service error", service="screening_service")

        self.assertEqual(str(exception), "Service error")
        self.assertEqual(exception.details, {"service": "screening_service"})

    def test_service_error_with_operation(self) -> None:
        """Test ServiceError with operation information."""
        exception = ServiceError("Service error", operation="screen")

        self.assertEqual(str(exception), "Service error")
        self.assertEqual(exception.details, {"operation": "screen"})

    def test_service_error_with_service_and_operation(self) -> None:
        """Test ServiceError with both service and operation."""
        exception = ServiceError(
            "Service error", service="screening_service", operation="screen"
        )

        self.assertEqual(str(exception), "Service error")
        self.assertEqual(
            exception.details, {"service": "screening_service", "operation": "screen"}
        )

    def test_service_error_inheritance(self) -> None:
        """Test that ServiceError inherits from DGIException."""
        exception = ServiceError("Service error")

        self.assertIsInstance(exception, DGIException)
        self.assertIsInstance(exception, ServiceError)


class TestCLIError(unittest.TestCase):
    """Tests for CLIError class."""

    def test_cli_error_basic(self) -> None:
        """Test basic CLIError initialization."""
        exception = CLIError("CLI error")

        self.assertEqual(str(exception), "CLI error")
        self.assertEqual(exception.message, "CLI error")
        self.assertEqual(exception.details, {})

    def test_cli_error_with_command(self) -> None:
        """Test CLIError with command information."""
        exception = CLIError("CLI error", command="screen")

        self.assertEqual(str(exception), "CLI error")
        self.assertEqual(exception.details, {"command": "screen"})

    def test_cli_error_inheritance(self) -> None:
        """Test that CLIError inherits from DGIException."""
        exception = CLIError("CLI error")

        self.assertIsInstance(exception, DGIException)
        self.assertIsInstance(exception, CLIError)


class TestUserInputError(unittest.TestCase):
    """Tests for UserInputError class."""

    def test_user_input_error(self) -> None:
        """Test UserInputError initialization."""
        exception = UserInputError("Invalid input", command="screen")

        self.assertEqual(str(exception), "Invalid input")
        self.assertEqual(exception.details, {"command": "screen"})

    def test_user_input_error_inheritance(self) -> None:
        """Test that UserInputError inherits from CLIError."""
        exception = UserInputError("Invalid input")

        self.assertIsInstance(exception, CLIError)
        self.assertIsInstance(exception, UserInputError)


class TestPerformanceError(unittest.TestCase):
    """Tests for PerformanceError class."""

    def test_performance_error_basic(self) -> None:
        """Test basic PerformanceError initialization."""
        exception = PerformanceError("Performance error")

        self.assertEqual(str(exception), "Performance error")
        self.assertEqual(exception.message, "Performance error")
        self.assertEqual(exception.details, {})

    def test_performance_error_with_metric(self) -> None:
        """Test PerformanceError with metric information."""
        exception = PerformanceError("Performance error", metric="response_time")

        self.assertEqual(str(exception), "Performance error")
        self.assertEqual(exception.details, {"metric": "response_time"})

    def test_performance_error_with_threshold(self) -> None:
        """Test PerformanceError with threshold information."""
        exception = PerformanceError("Performance error", threshold=5000)

        self.assertEqual(str(exception), "Performance error")
        self.assertEqual(exception.details, {"threshold": 5000})

    def test_performance_error_with_metric_and_threshold(self) -> None:
        """Test PerformanceError with both metric and threshold."""
        exception = PerformanceError(
            "Performance error", metric="response_time", threshold=5000
        )

        self.assertEqual(str(exception), "Performance error")
        self.assertEqual(
            exception.details, {"metric": "response_time", "threshold": 5000}
        )

    def test_performance_error_inheritance(self) -> None:
        """Test that PerformanceError inherits from DGIException."""
        exception = PerformanceError("Performance error")

        self.assertIsInstance(exception, DGIException)
        self.assertIsInstance(exception, PerformanceError)


class TestResourceError(unittest.TestCase):
    """Tests for ResourceError class."""

    def test_resource_error_basic(self) -> None:
        """Test basic ResourceError initialization."""
        exception = ResourceError("Resource error")

        self.assertEqual(str(exception), "Resource error")
        self.assertEqual(exception.message, "Resource error")
        self.assertEqual(exception.details, {})

    def test_resource_error_with_resource_type(self) -> None:
        """Test ResourceError with resource type information."""
        exception = ResourceError("Resource error", resource_type="memory")

        self.assertEqual(str(exception), "Resource error")
        self.assertEqual(exception.details, {"resource_type": "memory"})

    def test_resource_error_with_limit(self) -> None:
        """Test ResourceError with limit information."""
        exception = ResourceError("Resource error", limit=1024)

        self.assertEqual(str(exception), "Resource error")
        self.assertEqual(exception.details, {"limit": 1024})

    def test_resource_error_with_resource_type_and_limit(self) -> None:
        """Test ResourceError with both resource type and limit."""
        exception = ResourceError("Resource error", resource_type="memory", limit=1024)

        self.assertEqual(str(exception), "Resource error")
        self.assertEqual(exception.details, {"resource_type": "memory", "limit": 1024})

    def test_resource_error_inheritance(self) -> None:
        """Test that ResourceError inherits from DGIException."""
        exception = ResourceError("Resource error")

        self.assertIsInstance(exception, DGIException)
        self.assertIsInstance(exception, ResourceError)


class TestValidationError(unittest.TestCase):
    """Tests for legacy ValidationError class."""

    def test_validation_error(self) -> None:
        """Test ValidationError initialization."""
        exception = ValidationError(
            "Legacy validation error", field="test_field", value=123
        )

        self.assertEqual(str(exception), "Legacy validation error")
        self.assertEqual(exception.details, {"field": "test_field", "value": 123})

    def test_validation_error_inheritance(self) -> None:
        """Test that ValidationError inherits from DataValidationError."""
        exception = ValidationError("Legacy validation error")

        self.assertIsInstance(exception, DataValidationError)
        self.assertIsInstance(exception, ValidationError)


if __name__ == "__main__":
    unittest.main()
