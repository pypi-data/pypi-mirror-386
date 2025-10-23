# API Reference

## `AIMDAsyncLimiter`

```python
from aimd_limiter import AIMDAsyncLimiter
```

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_rate` | `float` | required | Hard upper bound on permits per second. Must be `> 0`. |
| `initial_rate` | `float` | `1.0` | Starting rate used during slow start. Clamped to `(0, max_rate]`. |
| `slow_start_threshold` | `float \| None` | `max_rate / 2` | Switch-over point from exponential to additive growth. |
| `additive_increase` | `float` | `1.0` | Linear increment applied after each success in congestion avoidance. |
| `multiplicative_decrease` | `float` | `0.5` | Backoff multiplier applied on failures. Must be in `(0, 1)`. |
| `min_rate` | `float` | `0.1` | Lower bound that avoids full stalls. Must be `> 0`. |
| `clock` | `Callable[[], float] \| None` | `None` | Optional monotonic time provider (defaults to `asyncio.get_running_loop().time`). |
| `sleep` | `Callable[[float], Awaitable[None]] \| None` | `asyncio.sleep` | Custom coroutine used to wait for the next permit. |

### Public Methods

- `acquire() -> Awaitable[Permit]`: Asynchronously wait for the next permit. Supports `await` and `async with`.
- `record_success() -> Awaitable[None]`: Manually record a successful operation. Usually called by `Permit`.
- `record_failure() -> Awaitable[None]`: Manually record a failed operation.

### Properties

- `current_rate: float`: Current effective rate in permits per second.
- `max_rate: float`: Configured hard cap.
- `slow_start_threshold: float`: Current threshold between slow start and congestion avoidance.
- `in_slow_start: bool`: `True` while the limiter is still in exponential growth.
- `in_fast_recovery: bool`: `True` after a failure until the recovery target is met.

## `Permit`

```python
permit = await limiter.acquire()
async with permit:
    ...
```

A context manager returned by `acquire()` that tracks success or failure. Once a permit is finalized, subsequent calls to `mark_success()` or `mark_failure()` are ignored.

### Methods

- `mark_success() -> Awaitable[None]`: Record success if the permit is not already finalized.
- `mark_failure() -> Awaitable[None]`: Record failure if the permit is not already finalized.

## `_AcquireHandle`

The object returned by `limiter.acquire()` behaves like both an awaitable and an async context manager. You generally do not interact with `_AcquireHandle` directly; instead, use one of:

```python
permit = await limiter.acquire()
async with limiter.acquire():
    ...
```

Both forms ensure that the limiter waits for the next slot before executing your work.

## Error Handling

The limiter validates all constructor arguments and raises `ValueError` when inputs fall outside the permitted ranges. No background tasks are spawned; cancellation propagates naturally through awaited coroutines.
