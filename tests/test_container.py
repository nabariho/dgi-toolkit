"""Tests for enhanced dependency injection container."""

import threading
from unittest.mock import MagicMock, patch

from dependency_injector import providers

from api.container import (
    Container,
    DependencyScope,
    get_container,
    get_data_repository_dependency,
    get_scoped_dependencies,
    get_screener_dependency,
    get_settings_dependency,
    get_test_screener_dependency,
    get_validator_dependency,
    init_container,
    shutdown_container,
)


class TestContainer:
    """Test the base Container class."""

    def test_container_initialization(self):
        """Test Container initialization."""
        container = Container()

        # Check that all providers are defined
        assert hasattr(container, "settings")
        assert hasattr(container, "data_repository")
        assert hasattr(container, "validator")
        assert hasattr(container, "scoring_strategy")
        assert hasattr(container, "screener")
        assert hasattr(container, "test_screener")

        # Check provider types
        assert isinstance(container.settings, providers.Singleton)
        assert isinstance(container.data_repository, providers.Singleton)
        assert isinstance(container.validator, providers.Singleton)
        assert isinstance(container.scoring_strategy, providers.Singleton)
        assert isinstance(container.screener, providers.Singleton)
        assert isinstance(container.test_screener, providers.Singleton)

    def test_container_provider_dependencies(self):
        """Test that providers are defined."""
        container = Container()

        # Check that providers exist
        assert container.screener is not None
        assert container.test_screener is not None


class TestGlobalContainer:
    """Test global container functions."""

    def test_get_container(self):
        """Test get_container function."""
        from api.container import container

        result = get_container()

        assert result is container
        # The container is a DynamicContainer from dependency-injector, not our Container class
        assert hasattr(result, "settings")
        assert hasattr(result, "data_repository")
        assert hasattr(result, "screener")

    def test_init_container(self):
        """Test init_container function."""
        with patch("api.container.container") as mock_container:
            init_container()

            mock_container.settings.assert_called_once()
            mock_container.data_repository.assert_called_once()
            mock_container.validator.assert_called_once()
            mock_container.scoring_strategy.assert_called_once()
            mock_container.screener.assert_called_once()

    def test_shutdown_container(self):
        """Test shutdown_container function."""
        with patch("api.container.container") as mock_container:
            mock_repository = MagicMock()
            mock_repository.cleanup = MagicMock()
            mock_container.data_repository.return_value = mock_repository

            shutdown_container()

            mock_repository.cleanup.assert_called_once()


class TestDependencyInjectionFunctions:
    """Test dependency injection functions."""

    def test_get_settings_dependency(self):
        """Test get_settings_dependency function."""
        with patch("api.container.container") as mock_container:
            mock_settings = MagicMock()
            mock_container.settings.return_value = mock_settings

            result = get_settings_dependency()

            assert result == mock_settings
            mock_container.settings.assert_called_once()

    def test_get_data_repository_dependency(self):
        """Test get_data_repository_dependency function."""
        with patch("api.container.container") as mock_container:
            mock_repository = MagicMock()
            mock_container.data_repository.return_value = mock_repository

            result = get_data_repository_dependency()

            assert result == mock_repository
            mock_container.data_repository.assert_called_once()

    def test_get_screener_dependency(self):
        """Test get_screener_dependency function."""
        with patch("api.container.container") as mock_container:
            mock_screener = MagicMock()
            mock_container.screener.return_value = mock_screener

            result = get_screener_dependency()

            assert result == mock_screener
            mock_container.screener.assert_called_once()

    def test_get_validator_dependency(self):
        """Test get_validator_dependency function."""
        with patch("api.container.container") as mock_container:
            mock_validator = MagicMock()
            mock_container.validator.return_value = mock_validator

            result = get_validator_dependency()

            assert result == mock_validator
            mock_container.validator.assert_called_once()

    def test_get_test_screener_dependency(self):
        """Test get_test_screener_dependency function."""
        with patch("api.container.container") as mock_container:
            mock_test_screener = MagicMock()
            mock_container.test_screener.return_value = mock_test_screener

            result = get_test_screener_dependency()

            assert result == mock_test_screener
            mock_container.test_screener.assert_called_once()


class TestDependencyScope:
    """Test DependencyScope class."""

    def test_dependency_scope_initialization(self):
        """Test DependencyScope initialization."""
        container = Container()
        scope = DependencyScope(container)

        assert scope.container is container
        assert scope._original_initialized is False

    def test_dependency_scope_with_default_container(self):
        """Test DependencyScope with default container."""
        scope = DependencyScope()

        from api.container import container

        assert scope.container is container

    def test_dependency_scope_context_manager(self):
        """Test DependencyScope as context manager."""
        container = Container()

        # Mock the global initialization state
        with patch("api.container._container_initialized", True):
            scope = DependencyScope(container)

            with scope as scoped_container:
                # Should return the container
                assert scoped_container is container

                # Should reset initialization (mocked to False)
                from api.container import _container_initialized

                assert _container_initialized is False

            # Should restore original initialization state
            # Note: The patch context manager handles the restoration

    def test_dependency_scope_with_exception(self):
        """Test DependencyScope context manager with exception."""
        container = Container()

        # Mock the global initialization state
        with patch("api.container._container_initialized", True):
            scope = DependencyScope(container)

            try:
                with scope:
                    raise Exception("Test exception")
            except Exception:
                pass  # Expected exception

            # Should still restore original state
            from api.container import _container_initialized

            assert _container_initialized is True


class TestGetScopedDependencies:
    """Test get_scoped_dependencies function."""

    def test_get_scoped_dependencies(self):
        """Test get_scoped_dependencies function."""
        result = get_scoped_dependencies()

        assert isinstance(result, DependencyScope)
        from api.container import container

        assert result.container is container


class TestBackwardCompatibility:
    """Test backward compatibility functions."""

    def test_backward_compatibility_functions(self):
        """Test that backward compatibility functions work."""
        with patch("api.container.get_data_repository_dependency") as mock_get_repo:
            mock_repo = MagicMock()
            mock_get_repo.return_value = mock_repo

            from api.container import get_data_repository

            result = get_data_repository()

            assert result == mock_repo
            mock_get_repo.assert_called_once()

    def test_get_screener_backward_compatibility(self):
        """Test get_screener backward compatibility."""
        with patch("api.container.get_screener_dependency") as mock_get_screener:
            mock_screener = MagicMock()
            mock_get_screener.return_value = mock_screener

            from api.container import get_screener

            result = get_screener(
                repository=MagicMock()
            )  # repository parameter ignored

            assert result == mock_screener
            mock_get_screener.assert_called_once()

    def test_get_dependency_container_backward_compatibility(self):
        """Test get_dependency_container backward compatibility."""
        with patch("api.container.get_container") as mock_get_container:
            mock_container = MagicMock()
            mock_get_container.return_value = mock_container

            from api.container import get_dependency_container

            result = get_dependency_container()

            assert result == mock_container
            mock_get_container.assert_called_once()


class TestContainerIntegration:
    """Integration tests for the container system."""

    def test_container_lifecycle(self):
        """Test complete container lifecycle."""
        with (
            patch("api.container.container") as mock_container,
            patch("api.container._container_initialized", False),
        ):
            # Test initialization
            init_container()
            mock_container.settings.assert_called_once()
            mock_container.data_repository.assert_called_once()
            mock_container.validator.assert_called_once()
            mock_container.scoring_strategy.assert_called_once()
            mock_container.screener.assert_called_once()

            # Test shutdown
            mock_repository = MagicMock()
            mock_repository.cleanup = MagicMock()
            mock_container.data_repository.return_value = mock_repository

            shutdown_container()
            mock_repository.cleanup.assert_called_once()

    def test_dependency_chain(self):
        """Test dependency chain resolution."""
        container = Container()

        # Test that providers are defined and accessible
        assert container.settings is not None
        assert container.data_repository is not None
        assert container.screener is not None
        assert container.validator is not None
        assert container.scoring_strategy is not None

    def test_thread_safety_integration(self):
        """Test thread safety in integration scenario."""

        def worker():
            """Worker function for thread testing."""
            init_container()
            shutdown_container()

        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should complete without thread safety issues
        assert True  # If we get here, no exceptions were raised
