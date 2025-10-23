# 使用指南

本文介绍 `AIMDAsyncLimiter` 的常见集成方式。

## 安装

使用推荐的 `uv` 或常规的 `pip` 进行安装：

```pwsh
uv add aimd-limiter
# 或者
pip install aimd-limiter
```

## 创建限流器

```python
from aimd_limiter import AIMDAsyncLimiter

limiter = AIMDAsyncLimiter(max_rate=50.0)
```

关键构造参数：

- `max_rate`：每秒允许的最大许可数量。
- `initial_rate`：慢启动阶段的初始速率，默认为 `1.0`。
- `slow_start_threshold`：从指数增长切换到加性增长的阈值，默认取 `max_rate / 2`。
- `additive_increase` / `multiplicative_decrease`：控制增长与退避速度。
- `min_rate`：防止完全停顿的速率下限。

## 使用异步上下文管理器

最简单的使用方式是配合 `async with`：

```python
async with limiter.acquire():
    await send_request()
```

进入代码块前获得许可，退出时根据是否抛出异常自动记录成功或失败。

## 手动反馈

当成功条件取决于额外信息时，可进行手动反馈：

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

同一个许可只需最终确认一次，可在多个辅助函数之间传递。

## 协调多个生产者

同一限流器实例共享一个控制循环。以下示例展示如何保护公共下游服务：

```python
async def worker(name: str) -> None:
    while True:
        async with limiter.acquire():
            await call_backend(name)

await asyncio.gather(*(worker(f"worker-{i}") for i in range(4)))
```

所有任务会自动随整体速率预算进行调整。

## 自定义时钟与睡眠函数

可通过 `clock` 与 `sleep` 参数替换默认的事件循环计时与 `asyncio.sleep`，便于测试或跨事件循环的适配：

```python
import time

def monotonic_seconds() -> float:
    return time.monotonic()

async def busy_sleep(delay: float) -> None:
    await trio.sleep(delay)  # 示例：桥接至其他事件循环

limiter = AIMDAsyncLimiter(
    max_rate=25.0,
    clock=monotonic_seconds,
    sleep=busy_sleep,
)
```

自定义睡眠协程需要支持取消，并在等待期间让出控制权。

## 监控与观测

限流器公开若干只读属性，可直接用于记录指标：

```python
current = limiter.current_rate
in_recovery = limiter.in_fast_recovery
```

结合成功/失败次数，可构建观测面板或告警。
