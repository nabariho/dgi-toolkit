"""Tests for repository base classes."""

import asyncio
import unittest
from unittest.mock import Mock, patch

import pytest

from dgi.models import CompanyData
from dgi.repositories.base import AsyncCompanyDataRepository, CompanyDataRepository


class TestCompanyDataRepository(unittest.TestCase):
    """Tests for CompanyDataRepository base class."""

    def test_company_data_repository_is_abstract(self) -> None:
        """Test that CompanyDataRepository cannot be instantiated directly."""
        with pytest.raises(TypeError):
            CompanyDataRepository()  # type: ignore

    def test_company_data_repository_inheritance(self) -> None:
        """Test that CompanyDataRepository inherits from ABC."""
        assert hasattr(CompanyDataRepository, "__abstractmethods__")
        assert "get_rows" in CompanyDataRepository.__abstractmethods__

    def test_concrete_implementation(self) -> None:
        """Test concrete implementation of CompanyDataRepository."""

        class TestRepository(CompanyDataRepository):
            def get_rows(self) -> list[CompanyData]:
                return [
                    CompanyData(
                        symbol="TEST1",
                        name="Test Company 1",
                        sector="Technology",
                        industry="Software",
                        dividend_yield=2.5,
                        payout_ratio=40.0,
                        dividend_growth_5y=8.0,
                        fcf_yield=5.0,
                    ),
                    CompanyData(
                        symbol="TEST2",
                        name="Test Company 2",
                        sector="Finance",
                        industry="Banking",
                        dividend_yield=3.0,
                        payout_ratio=50.0,
                        dividend_growth_5y=6.0,
                        fcf_yield=4.0,
                    ),
                ]

        repo = TestRepository()
        rows = repo.get_rows()

        assert isinstance(rows, list)
        assert len(rows) == 2
        assert isinstance(rows[0], CompanyData)
        assert rows[0].symbol == "TEST1"
        assert rows[1].symbol == "TEST2"

    @patch("asyncio.get_event_loop")
    def test_get_rows_async_success(self, mock_get_loop) -> None:
        """Test successful async data loading."""
        # Create a mock loop
        mock_loop = Mock()
        mock_get_loop.return_value = mock_loop

        # Create test data
        test_data = [
            CompanyData(
                symbol="TEST1",
                name="Test Company 1",
                sector="Technology",
                industry="Software",
                dividend_yield=2.5,
                payout_ratio=40.0,
                dividend_growth_5y=8.0,
                fcf_yield=5.0,
            )
        ]

        # Create a concrete repository
        class TestRepository(CompanyDataRepository):
            def get_rows(self) -> list[CompanyData]:
                return test_data

        repo = TestRepository()

        # Mock the executor to return our test data
        # Create a future with proper event loop context
        async def create_future():
            future = asyncio.Future()
            future.set_result(test_data)
            return future

        mock_loop.run_in_executor.return_value = asyncio.run(create_future())

        # Test async method
        async def test_async():
            result = await repo.get_rows_async()
            return result

        result = asyncio.run(test_async())

        assert result == test_data
        mock_loop.run_in_executor.assert_called_once_with(None, repo.get_rows)

    @patch("asyncio.get_event_loop")
    @patch("logging.getLogger")
    def test_get_rows_async_exception(self, mock_get_logger, mock_get_loop) -> None:
        """Test async data loading with exception."""
        # Create a mock loop
        mock_loop = Mock()
        mock_get_loop.return_value = mock_loop

        # Create a mock logger
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Create a repository that raises an exception
        class TestRepository(CompanyDataRepository):
            def get_rows(self) -> list[CompanyData]:
                raise ValueError("Test error")

        repo = TestRepository()

        # Mock the executor to raise an exception
        # Create a future with proper event loop context
        async def create_future():
            future = asyncio.Future()
            future.set_exception(ValueError("Test error"))
            return future

        mock_loop.run_in_executor.return_value = asyncio.run(create_future())

        # Test async method
        async def test_async():
            with pytest.raises(ValueError):
                await repo.get_rows_async()

        asyncio.run(test_async())

        # Verify logger was called
        mock_logger.error.assert_called_once()

    @patch("asyncio.get_event_loop")
    def test_get_rows_async_executor_exception(self, mock_get_loop) -> None:
        """Test async data loading when executor raises exception."""
        # Create a mock loop
        mock_loop = Mock()
        mock_get_loop.return_value = mock_loop

        # Create test data
        test_data = [
            CompanyData(
                symbol="TEST1",
                name="Test Company 1",
                sector="Technology",
                industry="Software",
                dividend_yield=2.5,
                payout_ratio=40.0,
                dividend_growth_5y=8.0,
                fcf_yield=5.0,
            )
        ]

        # Create a concrete repository
        class TestRepository(CompanyDataRepository):
            def get_rows(self) -> list[CompanyData]:
                return test_data

        repo = TestRepository()

        # Mock the executor to raise an exception
        mock_loop.run_in_executor.side_effect = RuntimeError("Executor error")

        # Test async method
        async def test_async():
            with pytest.raises(RuntimeError):
                await repo.get_rows_async()

        asyncio.run(test_async())

    def test_get_rows_async_override(self) -> None:
        """Test that get_rows_async can be overridden."""

        class TestRepository(CompanyDataRepository):
            def get_rows(self) -> list[CompanyData]:
                return []

            async def get_rows_async(self) -> list[CompanyData]:
                return [
                    CompanyData(
                        symbol="OVERRIDE",
                        name="Override Test",
                        sector="Technology",
                        industry="Software",
                        dividend_yield=2.5,
                        payout_ratio=40.0,
                        dividend_growth_5y=8.0,
                        fcf_yield=5.0,
                    )
                ]

        repo = TestRepository()

        # Test that sync method returns empty list
        sync_result = repo.get_rows()
        assert len(sync_result) == 0

        # Test that async method returns override data
        async def test_async():
            result = await repo.get_rows_async()
            return result

        async_result = asyncio.run(test_async())
        assert len(async_result) == 1
        assert async_result[0].symbol == "OVERRIDE"


class TestAsyncCompanyDataRepository(unittest.TestCase):
    """Tests for AsyncCompanyDataRepository protocol."""

    def test_async_company_data_repository_protocol(self) -> None:
        """Test AsyncCompanyDataRepository protocol implementation."""

        class TestAsyncRepository:
            async def get_rows_async(self) -> list[CompanyData]:
                return [
                    CompanyData(
                        symbol="ASYNC1",
                        name="Async Test 1",
                        sector="Technology",
                        industry="Software",
                        dividend_yield=2.5,
                        payout_ratio=40.0,
                        dividend_growth_5y=8.0,
                        fcf_yield=5.0,
                    )
                ]

        # Test that it implements the protocol
        repo = TestAsyncRepository()

        # Verify it has the required method
        assert hasattr(repo, "get_rows_async")
        assert asyncio.iscoroutinefunction(repo.get_rows_async)

        # Test the method works
        async def test_async():
            result = await repo.get_rows_async()
            return result

        result = asyncio.run(test_async())
        assert len(result) == 1
        assert result[0].symbol == "ASYNC1"

    def test_async_company_data_repository_with_error(self) -> None:
        """Test AsyncCompanyDataRepository with error handling."""

        class TestAsyncRepository:
            async def get_rows_async(self) -> list[CompanyData]:
                raise ValueError("Async error")

        repo = TestAsyncRepository()

        # Test that it raises the expected exception
        async def test_async():
            with pytest.raises(ValueError):
                await repo.get_rows_async()

        asyncio.run(test_async())

    def test_async_company_data_repository_empty_result(self) -> None:
        """Test AsyncCompanyDataRepository with empty result."""

        class TestAsyncRepository:
            async def get_rows_async(self) -> list[CompanyData]:
                return []

        repo = TestAsyncRepository()

        # Test that it returns empty list
        async def test_async():
            result = await repo.get_rows_async()
            return result

        result = asyncio.run(test_async())
        assert result == []

    def test_async_company_data_repository_multiple_rows(self) -> None:
        """Test AsyncCompanyDataRepository with multiple rows."""

        class TestAsyncRepository:
            async def get_rows_async(self) -> list[CompanyData]:
                return [
                    CompanyData(
                        symbol="ASYNC1",
                        name="Async Test 1",
                        sector="Technology",
                        industry="Software",
                        dividend_yield=2.5,
                        payout_ratio=40.0,
                        dividend_growth_5y=8.0,
                        fcf_yield=5.0,
                    ),
                    CompanyData(
                        symbol="ASYNC2",
                        name="Async Test 2",
                        sector="Finance",
                        industry="Banking",
                        dividend_yield=3.0,
                        payout_ratio=50.0,
                        dividend_growth_5y=6.0,
                        fcf_yield=4.0,
                    ),
                ]

        repo = TestAsyncRepository()

        # Test that it returns multiple rows
        async def test_async():
            result = await repo.get_rows_async()
            return result

        result = asyncio.run(test_async())
        assert len(result) == 2
        assert result[0].symbol == "ASYNC1"
        assert result[1].symbol == "ASYNC2"


class TestRepositoryIntegration(unittest.TestCase):
    """Integration tests for repository classes."""

    def test_repository_inheritance_hierarchy(self) -> None:
        """Test that repository classes follow proper inheritance hierarchy."""

        # Test that CompanyDataRepository is abstract
        assert hasattr(CompanyDataRepository, "__abstractmethods__")

        # Test that AsyncCompanyDataRepository is a protocol
        assert callable(AsyncCompanyDataRepository)

    def test_repository_method_signatures(self) -> None:
        """Test that repository methods have correct signatures."""

        # Test sync method signature
        class TestRepository(CompanyDataRepository):
            def get_rows(self) -> list[CompanyData]:
                return []

        repo = TestRepository()

        # Verify method exists and returns correct type
        result = repo.get_rows()
        assert isinstance(result, list)

        # Test async method signature
        async def test_async():
            result = await repo.get_rows_async()
            return result

        async_result = asyncio.run(test_async())
        assert isinstance(async_result, list)

    def test_repository_error_propagation(self) -> None:
        """Test that errors are properly propagated from repositories."""

        class ErrorRepository(CompanyDataRepository):
            def get_rows(self) -> list[CompanyData]:
                raise RuntimeError("Repository error")

        repo = ErrorRepository()

        # Test sync error propagation
        with pytest.raises(RuntimeError):
            repo.get_rows()

        # Test async error propagation
        async def test_async():
            with pytest.raises(RuntimeError):
                await repo.get_rows_async()

        asyncio.run(test_async())


if __name__ == "__main__":
    unittest.main()
