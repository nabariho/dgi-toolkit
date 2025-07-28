"""
Performance optimization utilities for DGI Toolkit.

This module provides performance monitoring, optimization utilities,
and vectorized operations for improved computational efficiency.
"""

import cProfile
import functools
import logging
import pstats
import time
from collections.abc import Callable
from contextlib import contextmanager
from io import StringIO
from typing import Any, TypeVar

import numpy as np
import pandas as pd
from numba import jit

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class PerformanceProfiler:
    """Performance profiler for identifying bottlenecks."""

    def __init__(self):
        """Initialize performance profiler."""
        self.profiles: dict[str, pstats.Stats] = {}

    @contextmanager
    def profile(self, name: str):
        """Context manager for profiling code blocks."""
        profiler = cProfile.Profile()
        start_time = time.time()

        try:
            profiler.enable()
            yield
        finally:
            profiler.disable()
            duration = time.time() - start_time

            # Store profile data
            s = StringIO()
            stats = pstats.Stats(profiler, stream=s)
            stats.sort_stats("cumulative")
            self.profiles[name] = stats

            logger.info(f"Profile '{name}' completed in {duration:.3f}s")

    def get_profile_report(self, name: str, top_n: int = 10) -> str:
        """Get profile report for a named profile."""
        if name not in self.profiles:
            return f"Profile '{name}' not found"

        s = StringIO()
        stats = self.profiles[name]
        stats.stream = s
        stats.print_stats(top_n)
        return s.getvalue()

    def print_all_profiles(self):
        """Print all available profiles."""
        for name, stats in self.profiles.items():
            print(f"\n=== Profile: {name} ===")
            stats.print_stats(10)


# Global profiler instance
profiler = PerformanceProfiler()


def profile_function(name: str | None = None):
    """Decorator to profile function execution."""

    def decorator(func: F) -> F:
        profile_name = name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with profiler.profile(profile_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


class VectorizedOperations:
    """Vectorized operations for improved performance."""

    @staticmethod
    @jit(nopython=True)
    def calculate_yield_score_vectorized(yields: np.ndarray) -> np.ndarray:
        """Vectorized dividend yield score calculation."""
        scores = np.zeros_like(yields)

        for i, yield_val in enumerate(yields):
            if yield_val < 0.02:
                scores[i] = yield_val / 0.04
            elif yield_val <= 0.04:
                scores[i] = 0.5 + (yield_val - 0.02) / 0.04
            elif yield_val <= 0.08:
                scores[i] = 1.0 - (yield_val - 0.04) * 5.0
            else:
                scores[i] = max(0.8 - (yield_val - 0.08) * 2.0, 0.0)

        return scores

    @staticmethod
    @jit(nopython=True)
    def calculate_payout_score_vectorized(payouts: np.ndarray) -> np.ndarray:
        """Vectorized payout ratio score calculation."""
        scores = np.zeros_like(payouts)

        for i, payout in enumerate(payouts):
            if payout < 0.0:
                scores[i] = 0.0
            elif payout <= 0.40:
                scores[i] = 0.5 + payout * 1.25
            elif payout <= 0.60:
                scores[i] = 1.0
            elif payout <= 0.80:
                scores[i] = 1.0 - (payout - 0.60) * 2.5
            else:
                scores[i] = max(0.5 - (payout - 0.80) * 1.25, 0.0)

        return scores

    @staticmethod
    @jit(nopython=True)
    def calculate_growth_score_vectorized(growth_rates: np.ndarray) -> np.ndarray:
        """Vectorized dividend growth score calculation."""
        scores = np.zeros_like(growth_rates)

        for i, growth in enumerate(growth_rates):
            if growth < 0.0:
                scores[i] = 0.0
            elif growth <= 0.05:
                scores[i] = growth * 10.0
            elif growth <= 0.15:
                scores[i] = 0.5 + (growth - 0.05) * 5.0
            else:
                scores[i] = max(1.0 - (growth - 0.15) * 2.0, 0.0)

        return scores

    @staticmethod
    @jit(nopython=True)
    def calculate_fcf_score_vectorized(fcf_yields: np.ndarray) -> np.ndarray:
        """Vectorized FCF yield score calculation."""
        scores = np.zeros_like(fcf_yields)

        for i, fcf in enumerate(fcf_yields):
            if fcf <= 0.0:
                scores[i] = 0.0
            elif fcf <= 0.10:
                scores[i] = fcf * 10.0
            else:
                scores[i] = 1.0

        return scores

    @classmethod
    def calculate_composite_scores_vectorized(
        cls,
        yields: np.ndarray,
        payouts: np.ndarray,
        growth_rates: np.ndarray,
        fcf_yields: np.ndarray,
    ) -> np.ndarray:
        """Calculate composite DGI scores using vectorized operations."""
        yield_scores = cls.calculate_yield_score_vectorized(yields)
        payout_scores = cls.calculate_payout_score_vectorized(payouts)
        growth_scores = cls.calculate_growth_score_vectorized(growth_rates)
        fcf_scores = cls.calculate_fcf_score_vectorized(fcf_yields)

        # Weighted combination
        composite_scores = (
            yield_scores * 0.40
            + payout_scores * 0.20
            + growth_scores * 0.30
            + fcf_scores * 0.10
        )

        return composite_scores


class DataFrameOptimizer:
    """Optimization utilities for DataFrame operations."""

    @staticmethod
    def optimize_dataframe_dtypes(df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage by choosing appropriate dtypes."""
        optimized_df = df.copy()

        for col in optimized_df.columns:
            col_type = optimized_df[col].dtype

            if col_type == "object":
                # Try to convert to category if cardinality is low
                unique_ratio = len(optimized_df[col].unique()) / len(optimized_df)
                if unique_ratio < 0.5:
                    optimized_df[col] = optimized_df[col].astype("category")

            elif col_type == "float64":
                # Try to downcast to float32 if precision allows
                if (
                    optimized_df[col].min() >= np.finfo(np.float32).min
                    and optimized_df[col].max() <= np.finfo(np.float32).max
                ):
                    optimized_df[col] = pd.to_numeric(
                        optimized_df[col], downcast="float"
                    )

            elif col_type == "int64":
                # Try to downcast to smaller integer types
                optimized_df[col] = pd.to_numeric(optimized_df[col], downcast="integer")

        return optimized_df

    @staticmethod
    def batch_process_dataframe(
        df: pd.DataFrame,
        func: Callable[[pd.DataFrame], pd.DataFrame],
        batch_size: int = 1000,
    ) -> pd.DataFrame:
        """Process large DataFrames in batches to manage memory."""
        if len(df) <= batch_size:
            return func(df)

        results = []
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i : i + batch_size]
            batch_result = func(batch)
            results.append(batch_result)

        return pd.concat(results, ignore_index=True)

    @staticmethod
    def vectorized_filtering(
        df: pd.DataFrame, conditions: dict[str, dict[str, float]]
    ) -> pd.DataFrame:
        """Apply multiple filtering conditions using vectorized operations."""
        mask = pd.Series(True, index=df.index)

        for column, condition in conditions.items():
            if column not in df.columns:
                continue

            if "min" in condition:
                mask &= df[column] >= condition["min"]
            if "max" in condition:
                mask &= df[column] <= condition["max"]
            if "equals" in condition:
                mask &= df[column] == condition["equals"]
            if "not_equals" in condition:
                mask &= df[column] != condition["not_equals"]

        return df[mask]


class CacheOptimizer:
    """Advanced caching strategies for improved performance."""

    def __init__(self, max_size: int = 100):
        """Initialize cache optimizer."""
        self.max_size = max_size
        self._cache: dict[str, Any] = {}
        self._access_order: list[str] = []
        self._hit_stats: dict[str, int] = {"hits": 0, "misses": 0}

    def _evict_lru(self):
        """Evict least recently used item."""
        if self._access_order:
            lru_key = self._access_order.pop(0)
            del self._cache[lru_key]

    def get(self, key: str) -> Any | None:
        """Get item from cache with LRU tracking."""
        if key in self._cache:
            # Move to end (most recently used)
            self._access_order.remove(key)
            self._access_order.append(key)
            self._hit_stats["hits"] += 1
            return self._cache[key]

        self._hit_stats["misses"] += 1
        return None

    def put(self, key: str, value: Any):
        """Put item in cache with size management."""
        if key in self._cache:
            # Update existing item
            self._access_order.remove(key)
        elif len(self._cache) >= self.max_size:
            # Evict LRU item
            self._evict_lru()

        self._cache[key] = value
        self._access_order.append(key)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hit_stats["hits"] + self._hit_stats["misses"]
        hit_rate = self._hit_stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hit_stats["hits"],
            "misses": self._hit_stats["misses"],
            "hit_rate": hit_rate,
        }


class AsyncOptimizer:
    """Async optimization utilities."""

    @staticmethod
    async def parallel_dataframe_processing(
        df: pd.DataFrame,
        func: Callable[[pd.DataFrame], pd.DataFrame],
        n_workers: int = 4,
    ) -> pd.DataFrame:
        """Process DataFrame in parallel using async workers."""
        import asyncio
        import concurrent.futures

        # Split DataFrame into chunks
        chunk_size = len(df) // n_workers
        chunks = [df.iloc[i : i + chunk_size] for i in range(0, len(df), chunk_size)]

        # Process chunks in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
            loop = asyncio.get_event_loop()
            tasks = [loop.run_in_executor(executor, func, chunk) for chunk in chunks]
            results = await asyncio.gather(*tasks)

        # Combine results
        return pd.concat(results, ignore_index=True)


def performance_benchmark(iterations: int = 1000):
    """Benchmark different implementation approaches."""

    # Generate test data
    np.random.seed(42)
    n_stocks = 1000

    data = {
        "dividend_yield": np.random.uniform(0.0, 0.15, n_stocks),
        "payout": np.random.uniform(0.0, 1.5, n_stocks),
        "dividend_cagr": np.random.uniform(-0.1, 0.3, n_stocks),
        "fcf_yield": np.random.uniform(-0.05, 0.2, n_stocks),
    }

    df = pd.DataFrame(data)

    # Benchmark vectorized vs non-vectorized operations
    vectorized_ops = VectorizedOperations()

    # Non-vectorized approach (simulation)
    start_time = time.time()
    for _ in range(iterations):
        # Simulate row-by-row processing
        scores = []
        for _, row in df.iterrows():
            # Simple scoring (not the actual algorithm)
            score = (
                row["dividend_yield"] * 0.4
                + (1 - row["payout"]) * 0.2
                + row["dividend_cagr"] * 0.3
                + row["fcf_yield"] * 0.1
            )
            scores.append(score)
    non_vectorized_time = time.time() - start_time

    # Vectorized approach
    start_time = time.time()
    for _ in range(iterations):
        scores = vectorized_ops.calculate_composite_scores_vectorized(
            df["dividend_yield"].values,
            df["payout"].values,
            df["dividend_cagr"].values,
            df["fcf_yield"].values,
        )
    vectorized_time = time.time() - start_time

    speedup = non_vectorized_time / vectorized_time

    print("Performance Benchmark Results:")
    print(f"Non-vectorized time: {non_vectorized_time:.3f}s")
    print(f"Vectorized time: {vectorized_time:.3f}s")
    print(f"Speedup: {speedup:.2f}x")

    return {
        "non_vectorized_time": non_vectorized_time,
        "vectorized_time": vectorized_time,
        "speedup": speedup,
    }


# Convenience functions
def optimize_scoring_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Apply performance optimizations to scoring operations."""
    # Optimize dtypes
    df_optimized = DataFrameOptimizer.optimize_dataframe_dtypes(df)

    # Use vectorized operations for scoring
    vectorized_ops = VectorizedOperations()
    scores = vectorized_ops.calculate_composite_scores_vectorized(
        df_optimized["dividend_yield"].values,
        df_optimized["payout"].values,
        df_optimized["dividend_cagr"].values,
        df_optimized["fcf_yield"].values,
    )

    df_optimized["dgi_score"] = scores
    return df_optimized


def apply_fast_filtering(df: pd.DataFrame, criteria: dict[str, Any]) -> pd.DataFrame:
    """Apply filtering using optimized vectorized operations."""
    # Convert criteria to vectorized format
    conditions = {}

    if "min_yield" in criteria:
        conditions["dividend_yield"] = {"min": criteria["min_yield"]}
    if "max_payout" in criteria:
        conditions["payout"] = {"max": criteria["max_payout"]}
    if "min_cagr" in criteria:
        conditions["dividend_cagr"] = {"min": criteria["min_cagr"]}

    return DataFrameOptimizer.vectorized_filtering(df, conditions)


if __name__ == "__main__":
    # Run performance benchmark
    performance_benchmark()
