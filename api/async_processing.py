"""Async processing module for DGI Toolkit API.

This module provides async processing capabilities for handling large datasets:
- Background task processing with job queue management
- Async data loading and processing
- Progress tracking for long-running operations
- Result caching for expensive operations
"""

import asyncio

# Configure logging
import logging
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from fastapi import BackgroundTasks
from pydantic import BaseModel, Field

from api.caching import cache_result
from api.observability import get_observability_manager
from dgi.screener import Screener

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(str, Enum):
    """Job priority enumeration."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ScreeningJob(BaseModel):
    """Screening job model."""

    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    progress: float = 0.0  # 0.0 to 1.0
    total_steps: int = 5
    current_step: int = 0
    step_description: str = "Initializing"

    # Job parameters
    min_yield: float
    max_payout: float
    min_cagr: float
    top_n: int

    # Results
    result: dict[str, Any] | None = None
    error_message: str | None = None

    # Metadata
    user_id: str | None = None
    correlation_id: str | None = None


class JobQueue:
    """Simple in-memory job queue for background processing."""

    def __init__(self):
        """Initialize the job queue."""
        self.jobs: dict[str, ScreeningJob] = {}
        self.running_jobs: dict[str, asyncio.Task] = {}
        self.max_concurrent_jobs = 3
        self.observability = get_observability_manager()

    async def submit_job(
        self,
        min_yield: float,
        max_payout: float,
        min_cagr: float,
        top_n: int,
        priority: JobPriority = JobPriority.NORMAL,
        user_id: str | None = None,
        correlation_id: str | None = None,
    ) -> str:
        """Submit a new screening job to the queue."""
        job = ScreeningJob(
            min_yield=min_yield,
            max_payout=max_payout,
            min_cagr=min_cagr,
            top_n=top_n,
            priority=priority,
            user_id=user_id,
            correlation_id=correlation_id,
        )

        self.jobs[job.job_id] = job

        # Log business event
        self.observability.log_business_event(
            "job_submitted",
            {
                "job_id": job.job_id,
                "priority": priority.value,
                "parameters": {
                    "min_yield": min_yield,
                    "max_payout": max_payout,
                    "min_cagr": min_cagr,
                    "top_n": top_n,
                },
            },
            user_id,
        )

        # Start processing if we have capacity
        await self._process_queue()

        return job.job_id

    async def get_job_status(self, job_id: str) -> ScreeningJob | None:
        """Get the status of a job."""
        return self.jobs.get(job_id)

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or running job."""
        if job_id not in self.jobs:
            return False

        job = self.jobs[job_id]

        if job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow()

            # Cancel running task if exists
            if job_id in self.running_jobs:
                self.running_jobs[job_id].cancel()
                del self.running_jobs[job_id]

            # Log business event
            self.observability.log_business_event(
                "job_cancelled", {"job_id": job_id}, job.user_id
            )

            return True

        return False

    async def list_jobs(
        self,
        status: JobStatus | None = None,
        user_id: str | None = None,
        limit: int = 50,
    ) -> list[ScreeningJob]:
        """List jobs with optional filtering."""
        jobs = list(self.jobs.values())

        # Apply filters
        if status:
            jobs = [job for job in jobs if job.status == status]

        if user_id:
            jobs = [job for job in jobs if job.user_id == user_id]

        # Sort by creation time (newest first)
        jobs.sort(key=lambda x: x.created_at, reverse=True)

        return jobs[:limit]

    async def _process_queue(self):
        """Process the job queue."""
        # Check if we can start more jobs
        if len(self.running_jobs) >= self.max_concurrent_jobs:
            return

        # Find pending jobs
        pending_jobs = [
            job for job in self.jobs.values() if job.status == JobStatus.PENDING
        ]

        # Sort by priority and creation time
        pending_jobs.sort(
            key=lambda x: (
                JobPriority.URGENT.value != x.priority.value,
                JobPriority.HIGH.value != x.priority.value,
                JobPriority.NORMAL.value != x.priority.value,
                x.created_at,
            )
        )

        # Start jobs up to capacity
        for job in pending_jobs:
            if len(self.running_jobs) >= self.max_concurrent_jobs:
                break

            if job.job_id not in self.running_jobs:
                task = asyncio.create_task(self._process_job(job))
                self.running_jobs[job.job_id] = task

    async def _process_job(self, job: ScreeningJob):
        """Process a screening job."""
        try:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            job.current_step = 1
            job.step_description = "Loading data"
            job.progress = 0.1

            # Log business event
            self.observability.log_business_event(
                "job_started", {"job_id": job.job_id}, job.user_id
            )

            # Step 1: Load data
            await asyncio.sleep(0.1)  # Simulate async work
            job.current_step = 2
            job.step_description = "Applying filters"
            job.progress = 0.3

            # Step 2: Apply filters
            await asyncio.sleep(0.1)  # Simulate async work
            job.current_step = 3
            job.step_description = "Calculating scores"
            job.progress = 0.5

            # Step 3: Calculate scores
            await asyncio.sleep(0.1)  # Simulate async work
            job.current_step = 4
            job.step_description = "Sorting results"
            job.progress = 0.7

            # Step 4: Sort and rank
            await asyncio.sleep(0.1)  # Simulate async work
            job.current_step = 5
            job.step_description = "Finalizing results"
            job.progress = 0.9

            # Step 5: Finalize results
            await asyncio.sleep(0.1)  # Simulate async work

            # Generate mock results (in real implementation, this would use the screener)
            job.result = {
                "stocks": [
                    {
                        "symbol": "MOCK1",
                        "name": "Mock Stock 1",
                        "sector": "Technology",
                        "industry": "Software",
                        "dividend_yield": job.min_yield + 0.01,
                        "payout": job.max_payout - 10,
                        "dividend_cagr": job.min_cagr + 0.02,
                        "fcf_yield": 5.2,
                        "score": 0.85,
                    }
                ],
                "total_count": 1,
                "filters_applied": {
                    "min_yield": job.min_yield,
                    "max_payout": job.max_payout,
                    "min_cagr": job.min_cagr,
                    "top_n": job.top_n,
                },
                "processing_time_ms": 1500.0,
                "job_id": job.job_id,
            }

            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.progress = 1.0
            job.step_description = "Completed"

            # Log business event
            self.observability.log_business_event(
                "job_completed",
                {
                    "job_id": job.job_id,
                    "stocks_returned": len(job.result["stocks"]),
                    "processing_time_ms": job.result["processing_time_ms"],
                },
                job.user_id,
            )

        except asyncio.CancelledError:
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            job.step_description = "Cancelled"

        except Exception as e:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)
            job.step_description = "Failed"

            # Log error
            logger.error(f"Job {job.job_id} failed: {e}")
            self.observability.record_error(
                "job_processing_error", str(e), "async_processing"
            )

            # Log business event
            self.observability.log_business_event(
                "job_failed", {"job_id": job.job_id, "error": str(e)}, job.user_id
            )

        finally:
            # Remove from running jobs
            if job.job_id in self.running_jobs:
                del self.running_jobs[job.job_id]

            # Process queue for next jobs
            await self._process_queue()

    async def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old completed/failed jobs."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

        jobs_to_remove = [
            job_id
            for job_id, job in self.jobs.items()
            if job.completed_at and job.completed_at < cutoff_time
        ]

        for job_id in jobs_to_remove:
            del self.jobs[job_id]

        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")


# Global job queue instance
job_queue = JobQueue()


async def get_job_queue() -> JobQueue:
    """Get the global job queue instance."""
    return job_queue


@cache_result(ttl=300, key_prefix="async_screening")
async def async_screen_stocks(
    screener: Screener, min_yield: float, max_payout: float, min_cagr: float, top_n: int
) -> dict[str, Any]:
    """Async version of stock screening with caching."""
    start_time = time.time()

    try:
        # Load universe data
        universe_df = screener.load_universe()

        # Apply filters
        filtered_df = universe_df[
            (universe_df["dividend_yield"] >= min_yield)
            & (universe_df["payout"] <= max_payout)
            & (universe_df["dividend_cagr"] >= min_cagr)
        ].copy()

        # Add scores
        filtered_df["score"] = (
            filtered_df["dividend_yield"] * 0.4
            + (1 - filtered_df["payout"] / 100) * 0.3
            + filtered_df["dividend_cagr"] * 0.3
        )

        # Get top stocks
        top_stocks_df = filtered_df.nlargest(top_n, "score")

        # Convert to response format
        stocks = [
            {
                "symbol": row["symbol"],
                "name": row["name"],
                "sector": row["sector"],
                "industry": row["industry"],
                "dividend_yield": float(row["dividend_yield"]),
                "payout": float(row["payout"]),
                "dividend_cagr": float(row["dividend_cagr"]),
                "fcf_yield": float(row["fcf_yield"]),
                "score": float(row["score"]),
            }
            for _, row in top_stocks_df.iterrows()
        ]

        processing_time = (time.time() - start_time) * 1000

        return {
            "stocks": stocks,
            "total_count": len(stocks),
            "filters_applied": {
                "min_yield": min_yield,
                "max_payout": max_payout,
                "min_cagr": min_cagr,
                "top_n": top_n,
            },
            "processing_time_ms": processing_time,
        }

    except Exception as e:
        logger.error(f"Async screening error: {e}")
        raise


async def submit_background_screening(
    background_tasks: BackgroundTasks,
    min_yield: float,
    max_payout: float,
    min_cagr: float,
    top_n: int,
    priority: JobPriority = JobPriority.NORMAL,
    user_id: str | None = None,
    correlation_id: str | None = None,
) -> str:
    """Submit a background screening job."""
    queue = await get_job_queue()
    job_id = await queue.submit_job(
        min_yield=min_yield,
        max_payout=max_payout,
        min_cagr=min_cagr,
        top_n=top_n,
        priority=priority,
        user_id=user_id,
        correlation_id=correlation_id,
    )

    # Add cleanup task
    background_tasks.add_task(queue.cleanup_old_jobs)

    return job_id
