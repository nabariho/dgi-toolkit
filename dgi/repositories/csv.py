import asyncio
import gc
import logging
import weakref
from collections.abc import Generator
from contextlib import contextmanager

import pandas as pd

from dgi.models import CompanyData
from dgi.repositories.base import CompanyDataRepository
from dgi.validation import DgiRowValidator
from dgi.validation_utils import PathValidationError, validate_file_path

logger = logging.getLogger(__name__)


class CsvCompanyDataRepository(CompanyDataRepository):
    def __init__(self, csv_path: str, validator: DgiRowValidator):
        # Validate and sanitize the file path
        try:
            self.csv_path = validate_file_path(csv_path, allowed_extensions=[".csv"])
        except PathValidationError as e:
            raise ValueError(f"Invalid CSV file path: {e.message}")

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
        except Exception as e:
            logger.error(f"Async CSV loading failed: {e}")
            raise

    def _load_csv_data(self) -> list[CompanyData]:
        """Load and validate CSV data with proper resource management."""
        try:
            # Use context manager for file handling
            with self._get_csv_file() as df:
                # Validate and convert to CompanyData objects
                rows = self.validator.validate_rows(df.to_dict("records"))
                logger.info(
                    f"Successfully loaded {len(rows)} valid rows from {self.csv_path}"
                )

                # Monitor resource usage
                self._resource_monitor.record_data_load(
                    len(rows), df.memory_usage(deep=True).sum()
                )

                return rows
        except Exception as e:
            logger.error(f"Failed to load CSV data from {self.csv_path}: {e}")
            raise

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

            # Convert numeric columns with error handling
            numeric_columns = [
                "dividend_yield",
                "payout_ratio",
                "dividend_growth_5y",
                "fcf_yield",
            ]
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            # Clean up any remaining NaN values for required columns
            required_columns = ["symbol", "dividend_yield", "payout_ratio"]
            available_columns = [col for col in required_columns if col in df.columns]
            if available_columns:
                df = df.dropna(subset=available_columns)

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

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with proper cleanup."""
        self.cleanup()

    def __del__(self):
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

            # Log resource usage
            self._resource_monitor.log_usage()

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def get_resource_stats(self) -> dict:
        """Get resource usage statistics."""
        return self._resource_monitor.get_stats()


class ResourceMonitor:
    """Monitor resource usage and memory consumption."""

    def __init__(self):
        self.data_loads = 0
        self.total_rows_loaded = 0
        self.total_memory_used = 0
        self.max_memory_used = 0
        self._weak_refs = weakref.WeakSet()

    def record_data_load(self, rows_count: int, memory_bytes: int) -> None:
        """Record a data load operation."""
        self.data_loads += 1
        self.total_rows_loaded += rows_count
        self.total_memory_used += memory_bytes
        self.max_memory_used = max(self.max_memory_used, memory_bytes)

    def register_object(self, obj) -> None:
        """Register an object for weak reference tracking."""
        self._weak_refs.add(obj)

    def get_stats(self) -> dict:
        """Get current resource statistics."""
        return {
            "data_loads": self.data_loads,
            "total_rows_loaded": self.total_rows_loaded,
            "total_memory_used_bytes": self.total_memory_used,
            "max_memory_used_bytes": self.max_memory_used,
            "tracked_objects": len(self._weak_refs),
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
        if len(self._weak_refs) > 1000:  # Arbitrary threshold
            logger.warning(
                f"Potential memory leak detected: {len(self._weak_refs)} tracked objects"
            )
            return True

        if collected > 0:
            logger.info(f"Garbage collection freed {collected} objects")

        return False
