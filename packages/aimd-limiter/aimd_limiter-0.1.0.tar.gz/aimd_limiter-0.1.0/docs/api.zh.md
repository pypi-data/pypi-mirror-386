# API 参考

## `AIMDAsyncLimiter`

```python
from aimd_limiter import AIMDAsyncLimiter
```

### 构造参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `max_rate` | `float` | 必填 | 每秒可发放的许可上限，必须大于 0。 |
| `initial_rate` | `float` | `1.0` | 慢启动阶段的初始速率，限定在 `(0, max_rate]`。 |
| `slow_start_threshold` | `float \| None` | `max_rate / 2` | 从指数增长切换到加性增长的阈值。 |
| `additive_increase` | `float` | `1.0` | 拥塞避免阶段在成功后增加的线性步长。 |
| `multiplicative_decrease` | `float` | `0.5` | 失败时应用的退避系数，必须位于 `(0, 1)`。 |
| `min_rate` | `float` | `0.1` | 防止完全停顿的速率下限，必须大于 0。 |
| `clock` | `Callable[[], float] \| None` | `None` | 自定义单调时间函数，默认使用事件循环时间。 |
| `sleep` | `Callable[[float], Awaitable[None]] \| None` | `asyncio.sleep` | 自定义等待协程，用于实现跨事件循环或测试。 |

### 公共方法

- `acquire() -> Awaitable[Permit]`：异步等待下一份许可，同时支持 `await` 与 `async with`。
- `record_success() -> Awaitable[None]`：手动记录成功事件，通常由 `Permit` 调用。
- `record_failure() -> Awaitable[None]`：手动记录失败事件。

### 只读属性

- `current_rate: float`：当前有效速率（许可/秒）。
- `max_rate: float`：配置的硬性上限。
- `slow_start_threshold: float`：慢启动与拥塞避免之间的边界。
- `in_slow_start: bool`：指示是否处于慢启动阶段。
- `in_fast_recovery: bool`：指示是否处于快速恢复阶段。

## `Permit`

```python
permit = await limiter.acquire()
async with permit:
    ...
```

`acquire()` 返回的上下文管理器，会跟踪成功或失败。一旦许可被终结，再次调用 `mark_success()` 或 `mark_failure()` 将被忽略。

### 方法

- `mark_success() -> Awaitable[None]`：在未终结的情况下记录成功。
- `mark_failure() -> Awaitable[None]`：在未终结的情况下记录失败。

## `_AcquireHandle`

`limiter.acquire()` 返回的对象既可被 `await`，也可用于 `async with`，通常无需直接操作 `_AcquireHandle`：

```python
permit = await limiter.acquire()
async with limiter.acquire():
    ...
```

上述两种写法都会在执行任务前等待许可放行。

## 错误处理

构造函数会校验参数范围，若不符合要求则抛出 `ValueError`。限流器不会创建后台任务，协程的取消会自然向上冒泡。
