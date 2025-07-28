"""Resource management service with single responsibility for resource monitoring and cleanup."""

import gc
import logging
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from types import TracebackType
from typing import Any

logger = logging.getLogger(__name__)


class ResourceMonitor(ABC):
    """Abstract base class for resource monitoring."""

    @abstractmethod
    def record_data_load(self, rows_count: int, memory_bytes: int) -> None:
        """Record data loading statistics."""

    @abstractmethod
    def register_object(self, obj: Any) -> None:
        """Register an object for memory leak tracking."""

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """Get current resource statistics."""

    @abstractmethod
    def check_memory_leaks(self) -> bool:
        """Check for potential memory leaks."""


class MemoryResourceMonitor(ResourceMonitor):
    """Memory-focused resource monitor."""

    def __init__(self) -> None:
        """Initialize the memory resource monitor."""
        self._tracked_objects: list[Any] = []
        self._data_load_stats: list[dict[str, Any]] = []
        self._start_time = time.time()

    def record_data_load(self, rows_count: int, memory_bytes: int) -> None:
        """Record data loading statistics.

        Args:
            rows_count: Number of rows loaded
            memory_bytes: Memory usage in bytes
        """
        stats = {
            "timestamp": time.time(),
            "rows_count": rows_count,
            "memory_bytes": memory_bytes,
            "memory_mb": memory_bytes / (1024 * 1024),
        }
        self._data_load_stats.append(stats)

        logger.info(
            f"Data load recorded: {rows_count} rows, {stats['memory_mb']:.2f} MB"
        )

    def register_object(self, obj: Any) -> None:
        """Register an object for memory leak tracking.

        Args:
            obj: Object to track
        """
        self._tracked_objects.append(obj)
        logger.debug(f"Registered object for tracking: {type(obj).__name__}")

    def get_stats(self) -> dict[str, Any]:
        """Get current resource statistics.

        Returns:
            Dictionary containing resource statistics
        """
        current_time = time.time()
        uptime = current_time - self._start_time

        # Calculate memory statistics
        total_memory = sum(stat["memory_bytes"] for stat in self._data_load_stats)
        avg_memory = (
            total_memory / len(self._data_load_stats) if self._data_load_stats else 0
        )

        # Get recent stats (last 10 loads)
        recent_stats = self._data_load_stats[-10:] if self._data_load_stats else []

        return {
            "uptime_seconds": uptime,
            "total_data_loads": len(self._data_load_stats),
            "total_memory_bytes": total_memory,
            "total_memory_mb": total_memory / (1024 * 1024),
            "average_memory_bytes": avg_memory,
            "average_memory_mb": avg_memory / (1024 * 1024),
            "tracked_objects_count": len(self._tracked_objects),
            "recent_loads": recent_stats,
        }

    def check_memory_leaks(self) -> bool:
        """Check for potential memory leaks.

        Returns:
            True if potential memory leak detected, False otherwise
        """
        # Simple heuristic: if we have many tracked objects and recent memory usage is high
        if len(self._tracked_objects) > 100:
            logger.warning(
                f"High number of tracked objects: {len(self._tracked_objects)}"
            )
            return True

        # Check if recent memory usage is significantly higher than average
        if len(self._data_load_stats) >= 2:
            recent_memory = self._data_load_stats[-1]["memory_bytes"]
            avg_memory = sum(
                stat["memory_bytes"] for stat in self._data_load_stats[:-1]
            ) / (len(self._data_load_stats) - 1)

            if recent_memory > avg_memory * 2:  # 2x threshold
                logger.warning(
                    f"Recent memory usage ({recent_memory}) is 2x higher than average ({avg_memory})"
                )
                return True

        return False

    def log_usage(self) -> None:
        """Log current resource usage."""
        stats = self.get_stats()
        logger.info(
            f"Resource usage - Uptime: {stats['uptime_seconds']:.1f}s, "
            f"Loads: {stats['total_data_loads']}, "
            f"Memory: {stats['total_memory_mb']:.2f} MB, "
            f"Objects: {stats['tracked_objects_count']}"
        )


class ResourceManager:
    """Resource manager for coordinating resource lifecycle."""

    def __init__(self, monitor: ResourceMonitor | None = None):
        """Initialize with optional resource monitor.

        Args:
            monitor: Resource monitor instance
        """
        self._monitor = monitor or MemoryResourceMonitor()
        self._managed_resources: list[Any] = []

    def track_resource(self, resource: Any) -> None:
        """Track a resource for lifecycle management.

        Args:
            resource: Resource to track
        """
        self._managed_resources.append(resource)
        self._monitor.register_object(resource)
        logger.debug(f"Tracking resource: {type(resource).__name__}")

    def cleanup(self) -> None:
        """Clean up managed resources."""
        logger.info(f"Cleaning up {len(self._managed_resources)} managed resources")

        # Clear tracked objects
        self._managed_resources.clear()

        # Force garbage collection
        gc.collect()

        logger.info("Resource cleanup completed")

    def get_resource_stats(self) -> dict[str, Any]:
        """Get resource statistics.

        Returns:
            Dictionary containing resource statistics
        """
        return self._monitor.get_stats()

    def check_health(self) -> bool:
        """Check resource health.

        Returns:
            True if resources are healthy, False otherwise
        """
        has_leaks = self._monitor.check_memory_leaks()
        return not has_leaks

    @contextmanager
    def managed_resource(self, resource: Any):
        """Context manager for automatic resource cleanup.

        Args:
            resource: Resource to manage

        Yields:
            The managed resource
        """
        try:
            self.track_resource(resource)
            yield resource
        finally:
            # Note: We don't automatically remove from managed_resources here
            # as the resource might still be in use
            pass

    def __enter__(self) -> "ResourceManager":
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager with cleanup."""
        self.cleanup()


class FileResourceManager(ResourceManager):
    """Specialized resource manager for file-based resources."""

    def __init__(self, monitor: ResourceMonitor | None = None):
        """Initialize file resource manager.

        Args:
            monitor: Resource monitor instance
        """
        super().__init__(monitor)
        self._file_handles: list[Any] = []

    def track_file_handle(self, file_handle: Any) -> None:
        """Track a file handle specifically.

        Args:
            file_handle: File handle to track
        """
        self._file_handles.append(file_handle)
        self.track_resource(file_handle)
        logger.debug(f"Tracking file handle: {type(file_handle).__name__}")

    def cleanup(self) -> None:
        """Clean up file resources specifically."""
        logger.info(f"Cleaning up {len(self._file_handles)} file handles")

        # Close file handles
        for handle in self._file_handles:
            try:
                if hasattr(handle, "close"):
                    handle.close()
                    logger.debug("Closed file handle")
            except Exception as e:
                logger.warning(f"Error closing file handle: {e}")

        self._file_handles.clear()

        # Call parent cleanup
        super().cleanup()


class CacheResourceManager(ResourceManager):
    """Specialized resource manager for cache resources."""

    def __init__(self, monitor: ResourceMonitor | None = None):
        """Initialize cache resource manager.

        Args:
            monitor: Resource monitor instance
        """
        super().__init__(monitor)
        self._caches: list[dict[str, Any]] = []

    def track_cache(self, cache: dict[str, Any]) -> None:
        """Track a cache specifically.

        Args:
            cache: Cache dictionary to track
        """
        self._caches.append(cache)
        self.track_resource(cache)
        logger.debug(f"Tracking cache with {len(cache)} entries")

    def clear_all_caches(self) -> None:
        """Clear all tracked caches."""
        logger.info(f"Clearing {len(self._caches)} caches")

        for cache in self._caches:
            cache.clear()
            logger.debug("Cleared cache")

        logger.info("All caches cleared")

    def cleanup(self) -> None:
        """Clean up cache resources."""
        self.clear_all_caches()
        super().cleanup()
