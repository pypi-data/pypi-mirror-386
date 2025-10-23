# Thread Safety

`AIMDAsyncLimiter` is built for cooperative concurrency inside a single `asyncio` event loop. Understanding its synchronization guarantees helps you deploy it confidently.

## Event Loop Semantics

- The limiter uses `asyncio.Lock` to guard both acquisition scheduling and state updates.
- Multiple concurrent tasks within the same event loop can call `acquire()` safely.
- State transitions (`record_success` / `record_failure`) always happen under the state lock, ensuring deterministic rate adjustments.

## Cross-Thread Usage

- `asyncio` event loops are not thread-safe by design. Use a separate limiter per thread or use thread-safe queues to marshal work back to the owning loop.
- When running on CPython 3.13+ with the experimental free-threaded runtime, you must still avoid calling limiter methods from threads that do not own the event loop.

## Multi-Process Setups

- Each process should run its own limiter instance. Sharing via inter-process communication would require additional coordination and is not provided by the library.

## Custom Clock & Sleep

If you provide custom `clock` or `sleep` callables, ensure they are themselves thread-safe and compatible with your scheduler. Avoid blocking the event loop inside `sleep`, otherwise global throughput will degrade.

## Cancellation & Back Pressure

- Cancellation propagates immediately; pending acquisitions are freed without mutating state.
- In-flight permits finalize independently; forgetting to mark success/failure leaves the limiter in a conservative state, so prefer the context manager pattern when possible.

## Testing Concurrency

Combine the limiter with `pytest-asyncio` or similar tools to drive concurrent test scenarios. Inject deterministic `clock` and `sleep` functions to simulate time in unit tests.
