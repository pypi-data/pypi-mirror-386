# aimd-limiter

[English](README.md) · [简体中文](README.zh-CN.md)

![CI](https://github.com/mxcoras/aimd-limiter/actions/workflows/ci-cd.yml/badge.svg)

Asynchronous Python rate limiter built around the Additive Increase Multiplicative Decrease (AIMD) control loop with slow start, congestion avoidance, and fast recovery behaviors.

## Features

- Fully asynchronous API compatible with Python 3.10+.
- Deterministic AIMD core with slow start, congestion avoidance, and fast recovery.
- Designed for integration inside asyncio-based services and SDKs.
- 100% test coverage.

## Usage Example

```python
import asyncio

from aimd_limiter import AIMDAsyncLimiter


async def main() -> None:
    limiter = AIMDAsyncLimiter(max_rate=20.0)
    async with limiter.acquire():
        # Perform work guarded by AIMD flow control.
        ...


asyncio.run(main())
```

## Documentation

- [Documentation](https://mxcoras.github.io/aimd-limiter/)

## Development

```pwsh
uv sync --all-groups
uv run pre-commit install
uv run pytest
uv run pre-commit run --all-files --show-diff-on-failure
```
