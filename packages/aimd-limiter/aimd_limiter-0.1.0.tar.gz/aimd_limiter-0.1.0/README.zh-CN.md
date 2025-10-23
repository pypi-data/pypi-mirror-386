# aimd-limiter

[English](README.md) · 简体中文

异步 Python AIMD (Additive Increase Multiplicative Decrease) 限流器，支持慢启动、拥塞避免以及快速恢复控制策略。

## 主要特性

- 完整的异步 API，兼容 Python 3.10+。
- 明确的 AIMD 控制核心，涵盖慢启动、拥塞避免、快速恢复等阶段。
- 适用于 asyncio 驱动的服务端或 SDK。
- 100% 单元测试覆盖率。

## 使用示例

```python
import asyncio

from aimd_limiter import AIMDAsyncLimiter


async def main() -> None:
    limiter = AIMDAsyncLimiter(max_rate=20.0)
    async with limiter.acquire():
        # 在 AIMD 流控保护下执行任务
        ...


asyncio.run(main())
```

## 文档

- [项目文档](https://mxcoras.github.io/aimd-limiter/)

## 开发流程

```pwsh
uv sync --all-groups
uv run pre-commit install
uv run pytest
uv run pre-commit run --all-files --show-diff-on-failure
```
