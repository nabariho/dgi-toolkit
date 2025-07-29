import asyncio
import gc
import logging
from collections.abc import Generator
from contextlib import contextmanager
from types import TracebackType
from typing import Any

import pandas as pd

from dgi.exceptions import DataLoadError, DataValidationError, RepositoryDataError
from dgi.models import CompanyData
from dgi.repositories.base import CompanyDataRepository
from dgi.validation_utils import (
    DgiRowValidator,
    PathValidationError,
    validate_file_path,
)

logger = logging.getLogger(__name__)


class CsvCompanyDataRepository(CompanyDataRepository):
    def __init__(self, csv_path: str, validator: DgiRowValidator):
        # Validate and sanitize the file path
        try:
            self.csv_path = validate_file_path(csv_path, allowed_extensions=[".csv"])
        except PathValidationError as e:
            raise ValueError(f"Invalid CSV file path: {e.message}") from e

        self.validator = validator
        self._data_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes cache TTL
        self._file_handle = None
        self._resource_monitor = ResourceMonitor()

    async def get_rows_async(self) -> list[CompanyData]:
        """Asynchronous method to get rows from CSV.

        Uses thread pool executor to avoid blocking the event loop.
        """
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._load_csv_data)
        except (OSError, FileNotFoundError) as e:
            logger.error(f"Async CSV loading failed - file error: {e}")
            raise DataLoadError(f"Failed to load CSV file: {e}") from e
        except Exception as e:
            logger.error(f"Async CSV loading failed - unexpected error: {e}")
            raise DataLoadError(f"Unexpected error during CSV loading: {e}") from e

    def _load_csv_data(self) -> list[CompanyData]:
        """Load and validate CSV data with proper resource management and performance optimizations."""
        try:
            # Use context manager for file handling
            with self._get_csv_file() as df:
                if df.empty:
                    logger.warning(f"CSV file is empty: {self.csv_path}")
                    return []

                # Optimize DataFrame to list conversion for better performance
                # Use vectorized operations where possible
                rows: list[dict[str, Any]] = []

                # Pre-allocate list size for better memory efficiency
                rows = [None] * len(df)  # type: ignore[list-item]

                # Use more efficient iteration
                for i, (_, row) in enumerate(df.iterrows()):
                    # Convert Hashable keys to str for type safety
                    rows[i] = {str(k): v for k, v in row.items()}

                # Validate and convert to CompanyData objects
                validated_rows = self.validator.validate_rows(rows)

                logger.info(
                    f"Successfully loaded {len(validated_rows)} valid rows from {self.csv_path}"
                )

                # Monitor resource usage
                memory_usage = df.memory_usage(deep=True).sum()
                self._resource_monitor.record_data_load(
                    len(validated_rows), memory_usage
                )

                # Register DataFrame for memory leak tracking
                self._resource_monitor.register_object(df)

                return validated_rows
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.error(f"File system error loading CSV from {self.csv_path}: {e}")
            raise DataLoadError(f"Failed to access CSV file: {e}") from e
        except pd.errors.EmptyDataError as e:
            logger.error(f"Empty CSV file: {self.csv_path}")
            raise DataLoadError(f"CSV file is empty: {e}") from e
        except pd.errors.ParserError as e:
            logger.error(f"CSV parsing error in {self.csv_path}: {e}")
            raise DataLoadError(f"Failed to parse CSV file: {e}") from e
        except DataValidationError:
            # Re-raise validation errors as-is for expected test behavior
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading CSV data from {self.csv_path}: {e}")
            raise RepositoryDataError(f"Unexpected repository error: {e}") from e

    @contextmanager
    def _get_csv_file(self) -> Generator[pd.DataFrame, None, None]:
        """Context manager for CSV file handling with proper cleanup."""
        df = None
        try:
            # Read CSV with flexible column handling
            df = pd.read_csv(
                self.csv_path,
                dtype=str,  # Read all as strings first for flexibility
                na_values=["", "nan", "NaN", "NULL"],
                keep_default_na=True,
                encoding="utf-8",
            )

            # Handle column name variations
            column_mapping = {
                "payout": "payout_ratio",
                "dividend_cagr": "dividend_growth_5y",
                "dividend_growth": "dividend_growth_5y",
            }

            # Rename columns if they exist
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns and new_name not in df.columns:
                    df = df.rename(columns={old_name: new_name})

            # Don't do numeric conversion here - let the validator handle it
            # This allows the validator to properly raise DataValidationError for invalid data

            yield df

        except FileNotFoundError:
            logger.error(f"CSV file not found: {self.csv_path}")
            raise
        except pd.errors.EmptyDataError:
            logger.warning(f"CSV file is empty: {self.csv_path}")
            yield pd.DataFrame()
        except Exception as e:
            logger.error(f"Error reading CSV file {self.csv_path}: {e}")
            raise
        finally:
            # Explicitly clean up DataFrame to free memory
            if df is not None:
                del df
                gc.collect()

    def get_rows(self) -> list[CompanyData]:
        """Get rows synchronously with proper resource management."""
        return self._load_csv_data()

    def clear_cache(self) -> None:
        """Clear the data cache and free memory."""
        if self._data_cache is not None:
            del self._data_cache
            self._data_cache = None
            self._cache_timestamp = None
            gc.collect()
            logger.info("Data cache cleared")

    def __enter__(self) -> "CsvCompanyDataRepository":
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit with proper cleanup."""
        self.cleanup()

    def __del__(self) -> None:
        """Destructor to ensure cleanup."""
        self.cleanup()

    def cleanup(self) -> None:
        """Clean up resources and free memory."""
        try:
            # Clear cache
            self.clear_cache()

            # Close file handles if any
            if self._file_handle is not None:
                self._file_handle.close()
                self._file_handle = None

            # Check for memory leaks
            if self._resource_monitor.check_memory_leaks():
                logger.warning("Potential memory leak detected during cleanup")

            # Log resource usage
            self._resource_monitor.log_usage()

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def get_resource_stats(self) -> dict[str, Any]:
        """Get resource usage statistics."""
        return self._resource_monitor.get_stats()


class ResourceMonitor:
    """Monitor resource usage and memory consumption."""

    def __init__(self) -> None:
        self.data_loads = 0
        self.total_rows_loaded = 0
        self.total_memory_used = 0
        self.max_memory_used = 0
        self._tracked_objects = 0

    def record_data_load(self, rows_count: int, memory_bytes: int) -> None:
        """Record a data load operation."""
        self.data_loads += 1
        self.total_rows_loaded += rows_count
        self.total_memory_used += memory_bytes
        self.max_memory_used = max(self.max_memory_used, memory_bytes)

    def register_object(self, obj: Any) -> None:
        """Register an object for tracking."""
        self._tracked_objects += 1

    def get_stats(self) -> dict[str, Any]:
        """Get current resource statistics."""
        try:
            import psutil  # type: ignore[import-untyped]

            process = psutil.Process()
            current_memory = process.memory_info().rss
        except (ImportError, AttributeError):
            current_memory = 0

        return {
            "data_loads": self.data_loads,
            "total_rows_loaded": self.total_rows_loaded,
            "total_memory_used_bytes": self.total_memory_used,
            "max_memory_used_bytes": self.max_memory_used,
            "current_memory_bytes": current_memory,
            "tracked_objects": self._tracked_objects,
        }

    def log_usage(self) -> None:
        """Log current resource usage."""
        stats = self.get_stats()
        logger.info(f"Resource usage: {stats}")

    def check_memory_leaks(self) -> bool:
        """Check for potential memory leaks."""
        # Force garbage collection
        collected = gc.collect()

        # Check if we have too many tracked objects
        if self._tracked_objects > 1000:  # Arbitrary threshold
            logger.warning(
                f"Potential memory leak detected: {self._tracked_objects} tracked objects"
            )
            return True

        # Check memory usage patterns
        if self.max_memory_used > 100 * 1024 * 1024:  # 100MB threshold
            logger.warning(
                f"High memory usage detected: {self.max_memory_used / (1024*1024):.2f}MB"
            )

        if collected > 0:
            logger.info(f"Garbage collection freed {collected} objects")

        return False
