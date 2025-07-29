"""Tests for API dependencies module."""

import threading
from unittest.mock import MagicMock, patch

from api.dependencies import (
    DependencyContainer,
    DependencyScope,
    get_data_repository,
    get_dependency_container,
    get_production_screener,
    get_scoped_dependencies,
    get_scoring_strategy,
    get_screener,
    get_settings_dependency,
    get_test_screener,
    get_validator,
)


class TestDependencyFunctions:
    """Test individual dependency functions."""

    def test_get_settings_dependency(self):
        """Test get_settings_dependency function."""
        with patch("api.dependencies.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_get_settings.return_value = mock_settings

            result = get_settings_dependency()

            assert result == mock_settings
            mock_get_settings.assert_called_once()

    def test_get_data_repository(self):
        """Test get_data_repository function."""
        with (
            patch("api.dependencies.get_settings") as mock_get_settings,
            patch("api.dependencies.create_repository") as mock_create_repo,
        ):
            mock_settings = MagicMock()
            mock_settings.data_path = "/test/data.csv"
            mock_get_settings.return_value = mock_settings

            mock_repository = MagicMock()
            mock_create_repo.return_value = mock_repository

            result = get_data_repository()

            assert result == mock_repository
            mock_create_repo.assert_called_once_with("/test/data.csv", "production")

    def test_get_screener(self):
        """Test get_screener function."""
        with patch("api.dependencies.create_screener") as mock_create_screener:
            mock_repository = MagicMock()
            mock_screener = MagicMock()
            mock_create_screener.return_value = mock_screener

            result = get_screener(repository=mock_repository)

            assert result == mock_screener
            mock_create_screener.assert_called_once_with(
                mock_repository, factory_name="production"
            )

    def test_get_validator(self):
        """Test get_validator function."""
        with patch("dgi.factory.create_validator") as mock_create_validator:
            mock_validator = MagicMock()
            mock_create_validator.return_value = mock_validator

            result = get_validator()

            assert result == mock_validator
            mock_create_validator.assert_called_once_with("production")

    def test_get_scoring_strategy(self):
        """Test get_scoring_strategy function."""
        with patch("dgi.factory.create_scoring_strategy") as mock_create_strategy:
            mock_strategy = MagicMock()
            mock_create_strategy.return_value = mock_strategy

            result = get_scoring_strategy()

            assert result == mock_strategy
            mock_create_strategy.assert_called_once_with("production")

    def test_get_production_screener(self):
        """Test get_production_screener function."""
        with (
            patch("api.dependencies.get_settings") as mock_get_settings,
            patch("api.dependencies.create_repository") as mock_create_repo,
            patch("api.dependencies.create_screener") as mock_create_screener,
        ):
            mock_settings = MagicMock()
            mock_settings.data_path = "/prod/data.csv"
            mock_get_settings.return_value = mock_settings

            mock_repository = MagicMock()
            mock_create_repo.return_value = mock_repository

            mock_screener = MagicMock()
            mock_create_screener.return_value = mock_screener

            result = get_production_screener()

            assert result == mock_screener
            mock_create_repo.assert_called_once_with("/prod/data.csv", "production")
            mock_create_screener.assert_called_once_with(
                mock_repository, factory_name="production"
            )

    def test_get_test_screener(self):
        """Test get_test_screener function."""
        with (
            patch("api.dependencies.get_settings") as mock_get_settings,
            patch("api.dependencies.create_repository") as mock_create_repo,
            patch("api.dependencies.create_screener") as mock_create_screener,
        ):
            mock_settings = MagicMock()
            mock_settings.data_path = "/test/data.csv"
            mock_get_settings.return_value = mock_settings

            mock_repository = MagicMock()
            mock_create_repo.return_value = mock_repository

            mock_screener = MagicMock()
            mock_create_screener.return_value = mock_screener

            result = get_test_screener()

            assert result == mock_screener
            mock_create_repo.assert_called_once_with("/test/data.csv", "test")
            mock_create_screener.assert_called_once_with(
                mock_repository, factory_name="test"
            )


class TestDependencyContainer:
    """Test DependencyContainer class."""

    def test_dependency_container_initialization(self):
        """Test DependencyContainer initialization."""
        container = DependencyContainer()

        assert container._screener is None
        assert container._repository is None
        assert container._validator is None
        assert hasattr(container._lock, "acquire")  # Check if it's a lock-like object

    def test_get_screener_singleton(self):
        """Test get_screener singleton pattern."""
        with patch("api.dependencies.get_production_screener") as mock_get_screener:
            mock_screener = MagicMock()
            mock_get_screener.return_value = mock_screener

            container = DependencyContainer()

            # First call should create the screener
            result1 = container.get_screener()
            assert result1 == mock_screener
            mock_get_screener.assert_called_once()

            # Second call should return the same instance
            result2 = container.get_screener()
            assert result2 == mock_screener
            assert result1 is result2
            # Should not call get_production_screener again
            mock_get_screener.assert_called_once()

    def test_get_repository_singleton(self):
        """Test get_repository singleton pattern."""
        with patch("api.dependencies.get_data_repository") as mock_get_repo:
            mock_repository = MagicMock()
            mock_get_repo.return_value = mock_repository

            container = DependencyContainer()

            # First call should create the repository
            result1 = container.get_repository()
            assert result1 == mock_repository
            mock_get_repo.assert_called_once()

            # Second call should return the same instance
            result2 = container.get_repository()
            assert result2 == mock_repository
            assert result1 is result2
            # Should not call get_data_repository again
            mock_get_repo.assert_called_once()

    def test_get_validator_singleton(self):
        """Test get_validator singleton pattern."""
        with patch("api.dependencies.get_validator") as mock_get_validator:
            mock_validator = MagicMock()
            mock_get_validator.return_value = mock_validator

            container = DependencyContainer()

            # First call should create the validator
            result1 = container.get_validator()
            assert result1 == mock_validator
            mock_get_validator.assert_called_once()

            # Second call should return the same instance
            result2 = container.get_validator()
            assert result2 == mock_validator
            assert result1 is result2
            # Should not call get_validator again
            mock_get_validator.assert_called_once()

    def test_reset(self):
        """Test reset method."""
        container = DependencyContainer()

        # Set some dependencies
        container._screener = MagicMock()
        container._repository = MagicMock()
        container._validator = MagicMock()

        # Reset should clear all dependencies
        container.reset()

        assert container._screener is None
        assert container._repository is None
        assert container._validator is None

    def test_cleanup_success(self):
        """Test cleanup method with successful repository cleanup."""
        container = DependencyContainer()

        # Set up repository with cleanup method
        mock_repository = MagicMock()
        mock_repository.cleanup = MagicMock()
        container._repository = mock_repository
        container._screener = MagicMock()
        container._validator = MagicMock()

        # Cleanup should call repository cleanup and clear dependencies
        container.cleanup()

        mock_repository.cleanup.assert_called_once()
        assert container._screener is None
        assert container._repository is None
        assert container._validator is None

    def test_cleanup_with_exception(self):
        """Test cleanup method when repository cleanup raises exception."""
        container = DependencyContainer()

        # Set up repository that raises exception on cleanup
        mock_repository = MagicMock()
        mock_repository.cleanup.side_effect = Exception("Cleanup failed")
        container._repository = mock_repository

        # Cleanup should handle exception and still clear dependencies
        container.cleanup()

        mock_repository.cleanup.assert_called_once()
        assert container._screener is None
        assert container._repository is None
        assert container._validator is None

    def test_thread_safety(self):
        """Test thread safety of dependency container."""
        with patch("api.dependencies.get_production_screener") as mock_get_screener:
            mock_screener = MagicMock()
            mock_get_screener.return_value = mock_screener

            container = DependencyContainer()
            results = []

            def get_screener_thread():
                results.append(container.get_screener())

            # Create multiple threads accessing the same container
            threads = []
            for _ in range(5):
                thread = threading.Thread(target=get_screener_thread)
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # All threads should get the same instance
            assert len(results) == 5
            assert all(result is mock_screener for result in results)
            # get_production_screener should only be called once
            mock_get_screener.assert_called_once()


class TestDependencyContainerGlobal:
    """Test global dependency container functions."""

    def test_get_dependency_container(self):
        """Test get_dependency_container function."""
        from api.dependencies import dependency_container

        result = get_dependency_container()

        assert result is dependency_container
        assert isinstance(result, DependencyContainer)


class TestDependencyScope:
    """Test DependencyScope class."""

    def test_dependency_scope_initialization(self):
        """Test DependencyScope initialization."""
        container = DependencyContainer()
        scope = DependencyScope(container)

        assert scope.container is container
        assert scope._original_screener is None
        assert scope._original_repository is None

    def test_dependency_scope_context_manager(self):
        """Test DependencyScope as context manager."""
        container = DependencyContainer()

        # Set some original dependencies
        original_screener = MagicMock()
        original_repository = MagicMock()
        container._screener = original_screener
        container._repository = original_repository

        scope = DependencyScope(container)

        with scope as scoped_container:
            # Inside scope, dependencies should be reset
            assert scoped_container._screener is None
            assert scoped_container._repository is None
            assert scoped_container is container

        # After scope, original dependencies should be restored
        assert container._screener is original_screener
        assert container._repository is original_repository

    def test_dependency_scope_with_exception(self):
        """Test DependencyScope context manager with exception."""
        container = DependencyContainer()

        # Set some original dependencies
        original_screener = MagicMock()
        original_repository = MagicMock()
        container._screener = original_screener
        container._repository = original_repository

        scope = DependencyScope(container)

        try:
            with scope as scoped_container:
                # Inside scope, dependencies should be reset
                assert scoped_container._screener is None
                assert scoped_container._repository is None
                raise Exception("Test exception")
        except Exception:
            pass

        # After scope (even with exception), original dependencies should be restored
        assert container._screener is original_screener
        assert container._repository is original_repository

    def test_get_scoped_dependencies(self):
        """Test get_scoped_dependencies function."""
        from api.dependencies import dependency_container

        result = get_scoped_dependencies()

        assert isinstance(result, DependencyScope)
        assert result.container is dependency_container


class TestDependencyIntegration:
    """Integration tests for dependency system."""

    def test_dependency_chain(self):
        """Test dependency chain from settings to screener."""
        with (
            patch("api.dependencies.get_settings") as mock_get_settings,
            patch("api.dependencies.create_repository") as mock_create_repo,
            patch("api.dependencies.create_screener") as mock_create_screener,
        ):
            # Mock settings
            mock_settings = MagicMock()
            mock_settings.data_path = "/test/data.csv"
            mock_get_settings.return_value = mock_settings

            # Mock repository
            mock_repository = MagicMock()
            mock_create_repo.return_value = mock_repository

            # Mock screener
            mock_screener = MagicMock()
            mock_create_screener.return_value = mock_screener

            # Test the chain
            repository = get_data_repository()
            screener = get_screener(repository=repository)

            assert repository == mock_repository
            assert screener == mock_screener
            mock_create_repo.assert_called_once_with("/test/data.csv", "production")
            mock_create_screener.assert_called_once_with(
                mock_repository, factory_name="production"
            )

    def test_container_lifecycle(self):
        """Test complete container lifecycle."""
        with (
            patch("api.dependencies.get_production_screener") as mock_get_screener,
            patch("api.dependencies.get_data_repository") as mock_get_repo,
            patch("api.dependencies.get_validator") as mock_get_validator,
            patch("api.dependencies.get_logger") as mock_get_logger,
        ):
            mock_screener = MagicMock()
            mock_get_screener.return_value = mock_screener

            mock_repository = MagicMock()
            mock_get_repo.return_value = mock_repository

            mock_validator = MagicMock()
            mock_get_validator.return_value = mock_validator

            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            container = DependencyContainer()

            # Test initial state
            assert container._screener is None
            assert container._repository is None
            assert container._validator is None

            # Test getting dependencies
            screener = container.get_screener()
            repository = container.get_repository()
            validator = container.get_validator()

            assert screener == mock_screener
            assert repository == mock_repository
            assert validator == mock_validator

            # Test reset
            container.reset()
            assert container._screener is None
            assert container._repository is None
            assert container._validator is None

            # Test cleanup
            container._repository = mock_repository
            container.cleanup()
            assert container._screener is None
            assert container._repository is None
            assert container._validator is None
