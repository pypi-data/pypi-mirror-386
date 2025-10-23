"""Asynchronous rate limiter that follows AIMD control semantics."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

Clock = Callable[[], float]
Sleep = Callable[[float], Awaitable[None]]


@dataclass(slots=True)
class Permit:
    """Context manager returned by :class:`AIMDAsyncLimiter` acquisitions.

    A ``Permit`` tracks the success or failure of a rate-limited operation.
    When used as a context manager, it automatically records success on normal
    exit and failure on exception. Alternatively, you can manually call
    :meth:`mark_success` or :meth:`mark_failure` to control the feedback signal.

    Note:
        A permit can only be finalized once; subsequent calls to
        :meth:`mark_success` or :meth:`mark_failure` are silently ignored.

    Example:
        >>> limiter = AIMDAsyncLimiter(max_rate=10.0)
        >>> async with limiter.acquire():
        ...     # Work is automatically recorded as success or failure
        ...     await perform_api_call()
        ...
        >>> # Manual control:
        >>> permit = await limiter.acquire()
        >>> try:
        ...     await perform_api_call()
        ...     await permit.mark_success()
        ... except SpecificError:
        ...     await permit.mark_failure()
    """

    _limiter: AIMDAsyncLimiter
    _finalized: bool = False

    async def __aenter__(self) -> Permit:
        """Return the permit for use inside ``async with`` blocks."""

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object | None,
    ) -> bool:
        """Record success unless an exception escapes the context manager."""

        if exc is None:
            await self.mark_success()
        else:
            await self.mark_failure()
        return False

    async def mark_success(self) -> None:
        """Record a successful request if the permit has not been finalized."""

        if not self._finalized:
            self._finalized = True
            await self._limiter.record_success()

    async def mark_failure(self) -> None:
        """Record a failed request if the permit has not been finalized."""

        if not self._finalized:
            self._finalized = True
            await self._limiter.record_failure()


class _AcquireHandle:
    """Awaitable and async-context-aware wrapper used for acquisitions."""

    __slots__ = ("_limiter", "_permit")

    def __init__(self, limiter: AIMDAsyncLimiter) -> None:
        self._limiter = limiter
        self._permit: Permit | None = None

    async def _ensure(self) -> Permit:
        if self._permit is None:
            await self._limiter._wait_for_slot()
            self._permit = Permit(self._limiter)
        return self._permit

    def __await__(self):  # type: ignore[no-untyped-def]
        return self._ensure().__await__()

    async def __aenter__(self) -> Permit:
        return await self._ensure()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object | None,
    ) -> bool:
        permit = await self._ensure()
        return await permit.__aexit__(exc_type, exc, tb)


class AIMDAsyncLimiter:
    """Asynchronous rate limiter implementing AIMD with slow start and fast recovery.

    Parameters
    ----------
    max_rate:
        Hard cap in requests per second that the limiter never exceeds.
    initial_rate:
        Starting request rate used during slow start.
    slow_start_threshold:
        Rate at which the limiter transitions from exponential to additive growth.
        The default is half of ``max_rate``.
    additive_increase:
        Linear increment applied after each success in congestion avoidance.
    multiplicative_decrease:
        Backoff factor applied on failures (value in ``(0, 1)``).
    min_rate:
        Lower bound for the rate to prevent stalls.
    clock:
        Callable returning monotonically increasing seconds; defaults to the running
        event loop clock.
    sleep:
        Coroutine used to await until the next permit; defaults to ``asyncio.sleep``.
    """

    def __init__(
        self,
        max_rate: float,
        *,
        initial_rate: float = 1.0,
        slow_start_threshold: float | None = None,
        additive_increase: float = 1.0,
        multiplicative_decrease: float = 0.5,
        min_rate: float = 0.1,
        clock: Clock | None = None,
        sleep: Sleep | None = None,
    ) -> None:
        if max_rate <= 0:
            msg = "max_rate must be strictly positive"
            raise ValueError(msg)
        if not (0 < initial_rate <= max_rate):
            msg = "initial_rate must be in the interval (0, max_rate]"
            raise ValueError(msg)
        if slow_start_threshold is None:
            slow_start_threshold = max_rate / 2
        if not (initial_rate <= slow_start_threshold <= max_rate):
            msg = "slow_start_threshold must be between initial_rate and max_rate"
            raise ValueError(msg)
        if additive_increase <= 0:
            msg = "additive_increase must be strictly positive"
            raise ValueError(msg)
        if not (0 < multiplicative_decrease < 1):
            msg = "multiplicative_decrease must be in the interval (0, 1)"
            raise ValueError(msg)
        if min_rate <= 0:
            msg = "min_rate must be strictly positive"
            raise ValueError(msg)

        self._max_rate = max_rate
        self._current_rate = initial_rate
        self._initial_rate = initial_rate
        self._slow_start_threshold = slow_start_threshold
        self._additive_increase = additive_increase
        self._multiplicative_decrease = multiplicative_decrease
        self._min_rate = min_rate
        self._clock = clock
        self._sleep = sleep or asyncio.sleep

        self._acquire_lock = asyncio.Lock()
        self._state_lock = asyncio.Lock()
        self._next_ready = 0.0
        self._slow_start = True
        self._in_fast_recovery = False
        self._recovery_target: float | None = None

    def acquire(self) -> _AcquireHandle:
        """Return an awaitable handle that grants access to a permit."""

        return _AcquireHandle(self)

    async def record_success(self) -> None:
        """Update the control loop after a successful operation."""

        async with self._state_lock:
            if self._slow_start and self._current_rate < self._slow_start_threshold:
                new_rate = min(
                    self._current_rate * 2,
                    self._slow_start_threshold,
                    self._max_rate,
                )
                self._current_rate = max(new_rate, self._min_rate)
                if self._current_rate >= self._slow_start_threshold:
                    self._slow_start = False
                    self._in_fast_recovery = False
                    self._recovery_target = None
                return

            self._slow_start = False
            new_rate = min(self._current_rate + self._additive_increase, self._max_rate)
            self._current_rate = max(new_rate, self._min_rate)

            if (  # pragma: no branch
                self._in_fast_recovery
                and self._recovery_target is not None
                and self._current_rate >= self._recovery_target
            ):
                self._in_fast_recovery = False
                self._recovery_target = None

    async def record_failure(self) -> None:
        """Update the control loop after a failed operation."""

        async with self._state_lock:
            previous_rate = self._current_rate
            reduced = max(
                self._current_rate * self._multiplicative_decrease,
                self._min_rate,
            )
            self._current_rate = reduced
            self._slow_start = False
            self._in_fast_recovery = True
            self._recovery_target = max(previous_rate, reduced)
            self._slow_start_threshold = max(reduced, self._min_rate)

    @property
    def current_rate(self) -> float:
        """Return the instantaneous permit rate in requests per second."""

        return self._current_rate

    @property
    def max_rate(self) -> float:
        """Return the configured maximum request rate."""

        return self._max_rate

    @property
    def slow_start_threshold(self) -> float:
        """Return the boundary between slow start and congestion avoidance."""

        return self._slow_start_threshold

    @property
    def in_slow_start(self) -> bool:
        """Indicate whether the limiter is currently performing slow start."""

        return self._slow_start

    @property
    def in_fast_recovery(self) -> bool:
        """Indicate whether the limiter is recovering from a recent failure."""

        return self._in_fast_recovery

    def _now(self) -> float:
        """Return the current monotonic time."""

        if self._clock is not None:
            return self._clock()
        loop = asyncio.get_running_loop()
        return loop.time()

    async def _wait_for_slot(self) -> None:
        """Block until the control loop allows the next permit."""

        while True:
            async with self._acquire_lock:
                now = self._now()
                wait = self._next_ready - now
                if wait <= 0:
                    interval = 1.0 / max(self._current_rate, self._min_rate)
                    base = max(self._next_ready, now)
                    self._next_ready = base + interval
                    return

            await self._sleep(wait)
