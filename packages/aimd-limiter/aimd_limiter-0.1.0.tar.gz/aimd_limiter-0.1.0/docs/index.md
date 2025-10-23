# AIMD Limiter

AIMD Limiter is an asynchronous Python rate limiter built on the Additive Increase Multiplicative Decrease (AIMD) control loop. It is designed for services and SDKs that need adaptive back-pressure with predictable dynamics.

## Key Features

- Fully asynchronous API compatible with `asyncio` and upcoming free-threaded CPython builds.
- Deterministic control loop that mirrors TCP slow start, congestion avoidance, and fast recovery.
- Back-pressure expressed as permits, with automatic success/failure feedback.
- Observable state via lightweight properties to inform metrics and dashboards.

## When To Use

Choose AIMD Limiter when you need to:

- Protect upstream services from overload while keeping utilization high.
- Smooth bursty workloads without hard-coding fixed delays.
- Provide fairness across many producers with minimal coordination.

If you simply need deterministic throttling with a fixed window, a classic token bucket may suffice. AIMD becomes preferable when feedback-driven adaptation is required.

## Documentation Map

- [Usage Guide](usage.md): learn how to integrate the limiter in real applications.
- [API Reference](api.md): explore constructors, methods, and key data structures.
- [Thread Safety](thread-safety.md): understand the concurrency model and deployment constraints.

## Contributing & Support

- Source code and issue tracker live at [GitHub](https://github.com/mxcoras/aimd-limiter).
- Pull requests and feature requests are welcome.
