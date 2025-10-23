"""Integration tests and usage examples for aimd_limiter."""

from __future__ import annotations

import asyncio

import pytest

from aimd_limiter import AIMDAsyncLimiter


@pytest.mark.asyncio
async def test_concurrent_requests() -> None:
    """Test handling of concurrent requests."""
    limiter = AIMDAsyncLimiter(max_rate=10.0, initial_rate=5.0)
    results = []

    async def worker(worker_id: int) -> None:
        async with limiter.acquire():
            results.append(worker_id)
            await asyncio.sleep(0.01)

    # Launch 20 concurrent tasks
    tasks = [worker(i) for i in range(20)]
    await asyncio.gather(*tasks)

    assert len(results) == 20
    assert set(results) == set(range(20))


@pytest.mark.asyncio
async def test_mixed_success_and_failure() -> None:
    """Test rate adaptation with mixed success and failure."""
    limiter = AIMDAsyncLimiter(
        max_rate=20.0,
        initial_rate=5.0,
        slow_start_threshold=10.0,
    )

    # Successful requests should increase rate
    for _ in range(3):
        async with limiter.acquire():
            pass

    rate_after_success = limiter.current_rate
    assert rate_after_success > 5.0

    # Failed request should decrease rate
    permit = await limiter.acquire()
    await permit.mark_failure()

    assert limiter.current_rate < rate_after_success
    assert limiter.in_fast_recovery is True


@pytest.mark.asyncio
async def test_rate_limiting_timing() -> None:
    """Test that requests are properly spaced according to rate."""
    limiter = AIMDAsyncLimiter(max_rate=5.0, initial_rate=5.0, slow_start_threshold=5.0)

    start_time = asyncio.get_running_loop().time()
    request_times = []

    for _ in range(5):
        async with limiter.acquire():
            request_times.append(asyncio.get_running_loop().time() - start_time)

    # Verify requests are spaced at least 0.2 seconds apart (1/5.0)
    for i in range(1, len(request_times)):
        interval = request_times[i] - request_times[i - 1]
        assert interval >= 0.15  # Allow some tolerance


@pytest.mark.asyncio
async def test_error_handling_in_context() -> None:
    """Test that errors in context manager are properly handled."""
    limiter = AIMDAsyncLimiter(max_rate=10.0, initial_rate=5.0)

    initial_rate = limiter.current_rate

    # First, increase rate with successes
    for _ in range(3):
        async with limiter.acquire():
            pass

    increased_rate = limiter.current_rate
    assert increased_rate > initial_rate

    # Error should trigger failure recording
    with pytest.raises(ValueError):
        async with limiter.acquire():
            raise ValueError("test error")

    assert limiter.in_fast_recovery is True
    assert limiter.current_rate < increased_rate


@pytest.mark.asyncio
async def test_reaching_max_rate() -> None:
    """Test that rate never exceeds max_rate."""
    limiter = AIMDAsyncLimiter(
        max_rate=10.0,
        initial_rate=2.0,
        additive_increase=5.0,  # Large increase to test ceiling
    )

    # Make many successful requests
    for _ in range(10):
        async with limiter.acquire():
            pass

    assert limiter.current_rate <= 10.0


@pytest.mark.asyncio
async def test_manual_permit_control() -> None:
    """Test manual control of permit success/failure."""
    limiter = AIMDAsyncLimiter(max_rate=10.0, initial_rate=5.0)

    # Manual success
    permit1 = await limiter.acquire()
    initial_rate = limiter.current_rate
    await permit1.mark_success()
    assert limiter.current_rate >= initial_rate

    # Manual failure
    permit2 = await limiter.acquire()
    rate_before_failure = limiter.current_rate
    await permit2.mark_failure()
    assert limiter.current_rate < rate_before_failure

    # Idempotency - repeated calls should not change rate
    current = limiter.current_rate
    await permit2.mark_failure()
    assert limiter.current_rate == current
