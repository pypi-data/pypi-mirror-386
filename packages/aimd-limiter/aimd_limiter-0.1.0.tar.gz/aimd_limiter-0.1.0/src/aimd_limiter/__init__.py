"""AIMD-based asynchronous rate limiter."""

from importlib.metadata import version

from .limiter import AIMDAsyncLimiter, Permit

__all__ = ["AIMDAsyncLimiter", "Permit"]
__version__ = version("aimd-limiter")
