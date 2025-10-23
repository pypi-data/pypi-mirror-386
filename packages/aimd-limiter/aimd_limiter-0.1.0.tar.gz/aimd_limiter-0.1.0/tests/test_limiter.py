from __future__ import annotations

import asyncio

import pytest

from aimd_limiter import AIMDAsyncLimiter


class DummyClock:
    """Controlled clock for deterministic testing."""

    def __init__(self) -> None:
        self._now = 0.0
        self.sleep_calls: list[float] = []

    def time(self) -> float:
        """Return the virtual time in seconds."""

        return self._now

    async def sleep(self, delay: float) -> None:
        """Advance time without blocking the event loop."""

        self.sleep_calls.append(delay)
        self._now += max(delay, 0.0)
        await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_parameter_validation() -> None:
    with pytest.raises(ValueError):
        AIMDAsyncLimiter(max_rate=0.0)
    with pytest.raises(ValueError):
        AIMDAsyncLimiter(max_rate=5.0, initial_rate=6.0)
    with pytest.raises(ValueError):
        AIMDAsyncLimiter(max_rate=5.0, slow_start_threshold=10.0)
    with pytest.raises(ValueError):
        AIMDAsyncLimiter(max_rate=5.0, additive_increase=0.0)
    with pytest.raises(ValueError):
        AIMDAsyncLimiter(max_rate=5.0, multiplicative_decrease=1.5)
    with pytest.raises(ValueError):
        AIMDAsyncLimiter(max_rate=5.0, min_rate=0.0)


@pytest.mark.asyncio
async def test_slow_start_then_additive_growth() -> None:
    clock = DummyClock()
    limiter = AIMDAsyncLimiter(
        max_rate=16.0,
        initial_rate=1.0,
        slow_start_threshold=8.0,
        additive_increase=1.0,
        multiplicative_decrease=0.5,
        clock=clock.time,
        sleep=clock.sleep,
    )

    assert limiter.max_rate == pytest.approx(16.0)
    assert limiter.slow_start_threshold == pytest.approx(8.0)
    assert limiter.in_slow_start is True

    for expected in (2.0, 4.0, 8.0):
        async with limiter.acquire():
            pass
        assert limiter.current_rate == pytest.approx(expected)

    async with limiter.acquire():
        pass
    assert limiter.in_slow_start is False
    assert limiter.current_rate == pytest.approx(9.0)  # type: ignore[unreachable]


@pytest.mark.asyncio
async def test_fast_recovery_after_failure() -> None:
    clock = DummyClock()
    limiter = AIMDAsyncLimiter(
        max_rate=20.0,
        initial_rate=5.0,
        slow_start_threshold=10.0,
        additive_increase=1.0,
        multiplicative_decrease=0.5,
        clock=clock.time,
        sleep=clock.sleep,
    )

    # Leave slow start phase quickly.
    while limiter.in_slow_start:
        async with limiter.acquire():
            pass

    steady_state = limiter.current_rate

    permit = await limiter.acquire()
    await permit.mark_failure()

    assert limiter.in_fast_recovery is True
    assert limiter.current_rate == pytest.approx(steady_state * 0.5)
    assert limiter.slow_start_threshold == pytest.approx(limiter.current_rate)

    # Gradually recover to previous steady state.
    while limiter.current_rate < steady_state:
        async with limiter.acquire():
            pass

    assert limiter.in_fast_recovery is False
    assert limiter.current_rate >= steady_state  # type: ignore[unreachable]


@pytest.mark.asyncio
async def test_context_manager_records_failure_on_exception() -> None:
    clock = DummyClock()
    limiter = AIMDAsyncLimiter(
        max_rate=10.0,
        initial_rate=2.0,
        clock=clock.time,
        sleep=clock.sleep,
    )

    with pytest.raises(RuntimeError):
        async with limiter.acquire():
            raise RuntimeError("boom")

    assert limiter.in_fast_recovery is True


@pytest.mark.asyncio
async def test_acquire_spacing_respects_rate() -> None:
    clock = DummyClock()
    limiter = AIMDAsyncLimiter(
        max_rate=10.0,
        initial_rate=5.0,
        clock=clock.time,
        sleep=clock.sleep,
    )

    permit = await limiter.acquire()
    await permit.mark_success()

    permit_two = await limiter.acquire()
    assert clock.sleep_calls
    assert clock.time() == pytest.approx(0.2)
    await permit_two.mark_success()


@pytest.mark.asyncio
async def test_mark_success_idempotent() -> None:
    clock = DummyClock()
    limiter = AIMDAsyncLimiter(
        max_rate=10.0,
        initial_rate=3.0,
        clock=clock.time,
        sleep=clock.sleep,
    )

    permit = await limiter.acquire()
    await permit.mark_success()
    previous_rate = limiter.current_rate
    await permit.mark_success()
    assert limiter.current_rate == pytest.approx(previous_rate)


@pytest.mark.asyncio
async def test_permit_direct_context_usage() -> None:
    clock = DummyClock()
    limiter = AIMDAsyncLimiter(
        max_rate=8.0,
        initial_rate=2.0,
        clock=clock.time,
        sleep=clock.sleep,
    )

    permit = await limiter.acquire()
    before = limiter.current_rate
    async with permit:
        pass
    after = limiter.current_rate
    assert after >= before
    await permit.mark_success()
    assert limiter.current_rate == pytest.approx(after)


@pytest.mark.asyncio
async def test_min_rate_floor_enforced() -> None:
    clock = DummyClock()
    limiter = AIMDAsyncLimiter(
        max_rate=10.0,
        initial_rate=1.0,
        multiplicative_decrease=0.05,
        min_rate=0.8,
        clock=clock.time,
        sleep=clock.sleep,
    )

    permit = await limiter.acquire()
    await permit.mark_failure()
    assert limiter.current_rate == pytest.approx(0.8)


@pytest.mark.asyncio
async def test_mark_failure_idempotent() -> None:
    clock = DummyClock()
    limiter = AIMDAsyncLimiter(
        max_rate=12.0,
        initial_rate=6.0,
        multiplicative_decrease=0.5,
        clock=clock.time,
        sleep=clock.sleep,
    )

    permit = await limiter.acquire()
    await permit.mark_failure()
    after_first = limiter.current_rate
    await permit.mark_failure()
    assert limiter.current_rate == pytest.approx(after_first)


@pytest.mark.asyncio
async def test_wait_for_slot_uses_event_loop_clock() -> None:
    limiter = AIMDAsyncLimiter(max_rate=20.0, initial_rate=10.0)

    permit = await limiter.acquire()
    await permit.mark_success()
    assert limiter.current_rate >= 10.0
