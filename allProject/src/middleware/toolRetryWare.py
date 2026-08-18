"""
ToolRetryMiddleware 工具重试中间件
集中式配置，一行 config 全搞定
"""
from typing import Any, Dict, Optional, Tuple, Union
import random
import time

from langchain.agents.middleware import ToolRetryMiddleware


class ToolRetryConfig:
    """
    工具重试统一配置（唯一配置入口）

    示例:
        config = {
            "max_retries": 6,
            "backoff_factor": 2.0,
            "initial_delay": 1.0,
            "max_delay": 10.0,
            "jitter": True,
            "retry_on": (TimeoutError,),
            "on_failure": "continue",
        }
    """

    DEFAULT: Dict[str, Any] = {
        "max_retries": 6,          # 不含首次调用 → 共 7 次
        "backoff_factor": 2.0,     # 指数退避
        "initial_delay": 1.0,      # 第一次重试等待
        "max_delay": 10.0,         # 上限
        "jitter": True,             # 防惊群
        "retry_on": (TimeoutError,),# 只重试的异常
        "on_failure": "continue",   # continue | raise
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: 用户自定义配置，未指定的项自动用 DEFAULT 补齐
        """
        cfg = {**self.DEFAULT, **(config or {})}
        self.max_retries = cfg["max_retries"]
        self.backoff_factor = cfg["backoff_factor"]
        self.initial_delay = cfg["initial_delay"]
        self.max_delay = cfg["max_delay"]
        self.jitter = cfg["jitter"]
        self.retry_on = cfg["retry_on"]
        self.on_failure = cfg["on_failure"]

    def _delay(self, attempt: int) -> float:
        delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
        delay = min(delay, self.max_delay)
        if self.jitter:
            delay = delay * random.uniform(0.8, 1.2)
        return delay

    def to_middleware(self) -> ToolRetryMiddleware:
        middleware = ToolRetryMiddleware(
            max_retries=self.max_retries,
            retry_on=self.retry_on,
            on_failure=self.on_failure,
        )

        if hasattr(middleware, "before_retry"):
            def _wait(retry_state):
                attempt = getattr(retry_state, "attempt_number", 1)
                time.sleep(self._delay(attempt))
            middleware.before_retry = _wait

        return middleware


def create_tool_retry_middleware(
    config: Optional[Dict[str, Any]] = None,
) -> ToolRetryMiddleware:
    """
    唯一对外工厂函数：一个 config 搞定所有重试策略

    用法:
        # 默认（6 次 + TimeoutError + continue）
        middleware = create_tool_retry_middleware()

        # 只改你想改的
        middleware = create_tool_retry_middleware({
            "max_retries": 10,
            "retry_on": (TimeoutError, ConnectionError),
            "on_failure": "raise",
        })
    """
    return ToolRetryConfig(config).to_middleware()