"""Tests for async processing module."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.async_processing import (
    JobPriority,
    JobQueue,
    JobStatus,
    ScreeningJob,
    async_screen_stocks,
    get_job_queue,
    submit_background_screening,
)


class TestScreeningJob:
    """Test ScreeningJob model."""

    def test_screening_job_creation(self):
        """Test creating a screening job with default values."""
        job = ScreeningJob(
            min_yield=3.0,
            max_payout=60.0,
            min_cagr=5.0,
            top_n=10,
        )

        assert job.job_id is not None
        assert job.status == JobStatus.PENDING
        assert job.priority == JobPriority.NORMAL
        assert job.created_at is not None
        assert job.started_at is None
        assert job.completed_at is None
        assert job.progress == 0.0
        assert job.total_steps == 5
        assert job.current_step == 0
        assert job.step_description == "Initializing"
        assert job.min_yield == 3.0
        assert job.max_payout == 60.0
        assert job.min_cagr == 5.0
        assert job.top_n == 10
        assert job.result is None
        assert job.error_message is None

    def test_screening_job_with_custom_values(self):
        """Test creating a screening job with custom values."""
        job = ScreeningJob(
            job_id="test-job-123",
            status=JobStatus.RUNNING,
            priority=JobPriority.HIGH,
            min_yield=4.0,
            max_payout=50.0,
            min_cagr=7.0,
            top_n=20,
            user_id="user123",
            correlation_id="corr123",
        )

        assert job.job_id == "test-job-123"
        assert job.status == JobStatus.RUNNING
        assert job.priority == JobPriority.HIGH
        assert job.user_id == "user123"
        assert job.correlation_id == "corr123"


class TestJobQueue:
    """Test JobQueue functionality."""

    @pytest.fixture
    def job_queue(self):
        """Create a job queue instance."""
        with patch("api.async_processing.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                max_concurrent_jobs=3, job_timeout_seconds=300
            )
            with patch("api.async_processing.get_observability_manager") as mock_obs:
                mock_obs.return_value = AsyncMock()
                return JobQueue()

    @pytest.mark.asyncio
    async def test_job_queue_context_manager(self, job_queue):
        """Test job queue as async context manager."""
        async with job_queue as queue:
            assert queue._cleanup_task is not None
            assert not queue._cleanup_task.done()

    @pytest.mark.asyncio
    async def test_submit_job(self, job_queue):
        """Test submitting a job to the queue."""
        job_id = await job_queue.submit_job(
            min_yield=3.0,
            max_payout=60.0,
            min_cagr=5.0,
            top_n=10,
            priority=JobPriority.HIGH,
            user_id="user123",
            correlation_id="corr123",
        )

        assert job_id in job_queue.jobs
        job = job_queue.jobs[job_id]
        assert job.status == JobStatus.PENDING
        assert job.priority == JobPriority.HIGH
        assert job.user_id == "user123"
        assert job.correlation_id == "corr123"

    @pytest.mark.asyncio
    async def test_get_job_status(self, job_queue):
        """Test getting job status."""
        job_id = await job_queue.submit_job(
            min_yield=3.0,
            max_payout=60.0,
            min_cagr=5.0,
            top_n=10,
        )

        job = await job_queue.get_job_status(job_id)
        assert job is not None
        assert job.job_id == job_id
        assert job.status == JobStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self, job_queue):
        """Test getting status of non-existent job."""
        job = await job_queue.get_job_status("non-existent")
        assert job is None

    @pytest.mark.asyncio
    async def test_cancel_job(self, job_queue):
        """Test canceling a job."""
        job_id = await job_queue.submit_job(
            min_yield=3.0,
            max_payout=60.0,
            min_cagr=5.0,
            top_n=10,
        )

        # Mock the job as running
        job_queue.jobs[job_id].status = JobStatus.RUNNING
        mock_task = MagicMock()
        mock_task.cancel.return_value = (
            None  # cancel() should return None, not a coroutine
        )
        job_queue.running_jobs[job_id] = mock_task

        result = await job_queue.cancel_job(job_id)
        assert result is True
        assert job_queue.jobs[job_id].status == JobStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_job_not_found(self, job_queue):
        """Test canceling a non-existent job."""
        result = await job_queue.cancel_job("non-existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_jobs(self, job_queue):
        """Test listing jobs with filters."""
        # Submit multiple jobs
        await job_queue.submit_job(
            min_yield=3.0,
            max_payout=60.0,
            min_cagr=5.0,
            top_n=10,
            user_id="user1",
        )
        await job_queue.submit_job(
            min_yield=4.0,
            max_payout=50.0,
            min_cagr=6.0,
            top_n=15,
            user_id="user2",
        )

        # Test listing all jobs
        all_jobs = await job_queue.list_jobs()
        assert len(all_jobs) == 2

        # Test filtering by user
        user1_jobs = await job_queue.list_jobs(user_id="user1")
        assert len(user1_jobs) == 1
        assert user1_jobs[0].user_id == "user1"

        # Test filtering by status
        pending_jobs = await job_queue.list_jobs(status=JobStatus.PENDING)
        assert len(pending_jobs) == 2

        # Test limit
        limited_jobs = await job_queue.list_jobs(limit=1)
        assert len(limited_jobs) == 1

    @pytest.mark.asyncio
    async def test_process_job_success(self, job_queue):
        """Test successful job processing."""
        job = ScreeningJob(
            min_yield=3.0,
            max_payout=60.0,
            min_cagr=5.0,
            top_n=10,
        )

        with patch("api.async_processing.async_screen_stocks") as mock_screen:
            mock_screen.return_value = {"stocks": [], "metrics": {}}

            await job_queue._process_job(job)

            assert job.status == JobStatus.COMPLETED
            assert job.progress == 1.0
            assert job.current_step == job.total_steps
            assert job.result is not None
            assert job.error_message is None

    @pytest.mark.asyncio
    async def test_process_job_failure(self, job_queue):
        """Test job processing with error."""
        job = ScreeningJob(
            min_yield=3.0,
            max_payout=60.0,
            min_cagr=5.0,
            top_n=10,
        )

        # Mock the observability to raise an exception
        job_queue.observability.log_business_event.side_effect = Exception("Test error")

        # The exception should be caught and the job should be marked as failed
        from contextlib import suppress

        with suppress(Exception):
            await job_queue._process_job(job)

        assert job.status == JobStatus.FAILED
        assert job.error_message is not None
        assert "Test error" in job.error_message

    @pytest.mark.asyncio
    async def test_cleanup_old_jobs(self, job_queue):
        """Test cleaning up old jobs."""
        # Create old job
        old_job = ScreeningJob(
            min_yield=3.0,
            max_payout=60.0,
            min_cagr=5.0,
            top_n=10,
        )
        old_job.created_at = datetime.now(UTC) - timedelta(hours=25)
        old_job.completed_at = datetime.now(UTC) - timedelta(hours=25)
        old_job.status = JobStatus.COMPLETED

        # Create recent job
        recent_job = ScreeningJob(
            min_yield=4.0,
            max_payout=50.0,
            min_cagr=6.0,
            top_n=15,
        )
        recent_job.created_at = datetime.now(UTC) - timedelta(hours=1)
        recent_job.completed_at = datetime.now(UTC) - timedelta(hours=1)
        recent_job.status = JobStatus.COMPLETED

        job_queue.jobs["old"] = old_job
        job_queue.jobs["recent"] = recent_job

        await job_queue.cleanup_old_jobs(max_age_hours=24)

        assert "old" not in job_queue.jobs
        assert "recent" in job_queue.jobs


class TestAsyncScreenStocks:
    """Test async_screen_stocks function."""

    @pytest.mark.asyncio
    async def test_async_screen_stocks(self):
        """Test async screening of stocks."""
        import pandas as pd

        # Create a mock DataFrame that the function expects
        mock_data = {
            "symbol": ["AAPL", "MSFT"],
            "name": ["Apple Inc", "Microsoft Corp"],
            "sector": ["Technology", "Technology"],
            "industry": ["Software", "Software"],
            "dividend_yield": [2.5, 1.8],
            "payout": [25.0, 30.0],
            "dividend_cagr": [5.5, 6.2],
            "fcf_yield": [4.2, 3.8],
            "score": [0.85, 0.78],
        }
        mock_df = pd.DataFrame(mock_data)

        mock_screener = AsyncMock()
        mock_screener.screen_async.return_value = mock_df

        result = await async_screen_stocks(
            screener=mock_screener,
            min_yield=2.0,
            max_payout=40.0,
            min_cagr=5.0,
            top_n=10,
        )

        assert "stocks" in result
        assert "total_count" in result
        assert len(result["stocks"]) == 2
        assert result["total_count"] == 2
        assert result["stocks"][0]["symbol"] == "AAPL"
        assert result["stocks"][1]["symbol"] == "MSFT"

        mock_screener.screen_async.assert_called_once_with(
            min_yield=2.0,
            max_payout=40.0,
            min_cagr=5.0,
            top_n=10,
        )


class TestSubmitBackgroundScreening:
    """Test submit_background_screening function."""

    @pytest.mark.asyncio
    async def test_submit_background_screening(self):
        """Test submitting background screening job."""
        mock_background_tasks = MagicMock()
        mock_job_queue = AsyncMock()
        mock_job_queue.submit_job.return_value = "job-123"

        with patch("api.async_processing.get_job_queue", return_value=mock_job_queue):
            job_id = await submit_background_screening(
                background_tasks=mock_background_tasks,
                min_yield=3.0,
                max_payout=60.0,
                min_cagr=5.0,
                top_n=10,
                priority=JobPriority.HIGH,
                user_id="user123",
                correlation_id="corr123",
            )

            assert job_id == "job-123"
            mock_job_queue.submit_job.assert_called_once_with(
                min_yield=3.0,
                max_payout=60.0,
                min_cagr=5.0,
                top_n=10,
                priority=JobPriority.HIGH,
                user_id="user123",
                correlation_id="corr123",
            )


class TestGetJobQueue:
    """Test get_job_queue function."""

    @pytest.mark.asyncio
    async def test_get_job_queue_singleton(self):
        """Test that get_job_queue returns the same instance."""
        queue1 = await get_job_queue()
        queue2 = await get_job_queue()

        assert queue1 is queue2
        assert isinstance(queue1, JobQueue)


class TestJobStatus:
    """Test JobStatus enumeration."""

    def test_job_status_values(self):
        """Test JobStatus enum values."""
        assert JobStatus.PENDING == "pending"
        assert JobStatus.RUNNING == "running"
        assert JobStatus.COMPLETED == "completed"
        assert JobStatus.FAILED == "failed"
        assert JobStatus.CANCELLED == "cancelled"


class TestJobPriority:
    """Test JobPriority enumeration."""

    def test_job_priority_values(self):
        """Test JobPriority enum values."""
        assert JobPriority.LOW == "low"
        assert JobPriority.NORMAL == "normal"
        assert JobPriority.HIGH == "high"
        assert JobPriority.URGENT == "urgent"


class TestJobQueueIntegration:
    """Integration tests for JobQueue."""

    @pytest.mark.asyncio
    async def test_full_job_lifecycle(self):
        """Test complete job lifecycle from submission to completion."""
        with patch("api.async_processing.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                max_concurrent_jobs=3, job_timeout_seconds=300
            )
            with patch("api.async_processing.get_observability_manager") as mock_obs:
                mock_obs.return_value = AsyncMock()

                async with JobQueue() as job_queue:
                    # Submit job
                    job_id = await job_queue.submit_job(
                        min_yield=3.0,
                        max_payout=60.0,
                        min_cagr=5.0,
                        top_n=10,
                    )

                    # Check initial status
                    job = await job_queue.get_job_status(job_id)
                    assert job.status == JobStatus.PENDING

                    # Process job manually
                    with patch(
                        "api.async_processing.async_screen_stocks"
                    ) as mock_screen:
                        mock_screen.return_value = {"stocks": [], "metrics": {}}
                        await job_queue._process_job(job)

                    # Check final status
                    updated_job = await job_queue.get_job_status(job_id)
                    assert updated_job.status == JobStatus.COMPLETED
                    assert updated_job.result is not None

    @pytest.mark.asyncio
    async def test_concurrent_job_processing(self):
        """Test processing multiple jobs concurrently."""
        with patch("api.async_processing.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                max_concurrent_jobs=2, job_timeout_seconds=300
            )
            with patch("api.async_processing.get_observability_manager") as mock_obs:
                mock_obs.return_value = AsyncMock()

                async with JobQueue() as job_queue:
                    # Submit multiple jobs
                    job_ids = []
                    for i in range(3):
                        job_id = await job_queue.submit_job(
                            min_yield=3.0 + i,
                            max_payout=60.0,
                            min_cagr=5.0,
                            top_n=10,
                        )
                        job_ids.append(job_id)

                    # Check all jobs are pending
                    for job_id in job_ids:
                        job = await job_queue.get_job_status(job_id)
                        assert job.status == JobStatus.PENDING

                    # List all jobs
                    all_jobs = await job_queue.list_jobs()
                    assert len(all_jobs) == 3
