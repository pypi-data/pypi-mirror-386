# Usage Guide

This guide walks through the most common integration patterns for `AIMDAsyncLimiter`.

## Installing

Add the package to your project using `uv` (recommended) or `pip`:

```pwsh
uv add aimd-limiter
# or
pip install aimd-limiter
```

## Creating A Limiter

```python
from aimd_limiter import AIMDAsyncLimiter

limiter = AIMDAsyncLimiter(max_rate=50.0)
```

Key constructor arguments:

- `max_rate`: hard upper bound in permits per second.
- `initial_rate`: starting rate during slow start. Defaults to `1.0`.
- `slow_start_threshold`: boundary before switching to additive increase. Defaults to `max_rate / 2`.
- `additive_increase` / `multiplicative_decrease`: govern how quickly the limiter grows and backs off.
- `min_rate`: floor that prevents stalls.

## Guarding Work With Context Managers

The easiest way to apply the limiter is an async context manager:

```python
async with limiter.acquire():
    await send_request()
```

A permit is acquired before the block executes and automatically records success or failure depending on whether an exception escapes the block.

## Manual Feedback

Manual feedback is useful when additional information determines success:

```python
permit = await limiter.acquire()
try:
    response = await client.fetch()
    if response.status == 429:
        await permit.mark_failure()
    else:
        await permit.mark_success()
except Exception:
    await permit.mark_failure()
    raise
```

You can reuse the permit inside multiple helper functions as long as it is finalized exactly once.

## Coordinating Multiple Producers

All calls into the same limiter instance share a single control loop. To protect a downstream dependency across tasks:

```python
async def worker(name: str) -> None:
    while True:
        async with limiter.acquire():
            await call_backend(name)

await asyncio.gather(*(worker(f"worker-{i}") for i in range(4)))
```

Each worker will naturally adapt to the global rate budget.

## Customizing Clocks And Sleep

The limiter accepts custom `clock` and `sleep` callables for advanced use cases (e.g., deterministic testing or time-travel simulations):

```python
import time

def monotonic_seconds() -> float:
    return time.monotonic()

async def busy_sleep(delay: float) -> None:
    await trio.sleep(delay)  # example: bridging to an alternative event loop

limiter = AIMDAsyncLimiter(
    max_rate=25.0,
    clock=monotonic_seconds,
    sleep=busy_sleep,
)
```

When providing your own sleep coroutine, respect cancellation and cooperatively yield control to the event loop.

## Instrumentation Hooks

Expose limiter state to metrics by reading properties without locks:

```python
current = limiter.current_rate
in_recovery = limiter.in_fast_recovery
```

Pair these readings with success/failure counts to build dashboards or alerts.
