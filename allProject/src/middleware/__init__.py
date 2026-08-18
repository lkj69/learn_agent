"""
中间件模块
包含各种用于 Agent 的中间件配置

可用的中间件:
- SummarizationMiddleware: 消息历史总结和压缩
- ToolRetryMiddleware: 工具调用失败时的自动重试
"""
from typing import List, Optional

# 总结中间件相关
from .summaryWare import (
    SummaryWareConfig,
    create_summary_middleware
)

# 工具重试中间件相关
from .toolRetryWare import (
    ToolRetryConfig,
    create_tool_retry_middleware,
)


__all__ = [
    # 总结中间件
    "SummaryWareConfig",
    "create_summary_middleware",
    
    # 工具重试中间件
    "ToolRetryConfig",
    "create_tool_retry_middleware",
]
