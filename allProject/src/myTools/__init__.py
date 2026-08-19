"""MCP 工具模块。

所有工具通过 `@mcp.tool()` 注册到共享的 FastMCP 服务器实例上，
通过 `python -m myTools` 以 stdio 方式对外暴露。
"""
from ._server import mcp

# 导入各工具模块以触发 @mcp.tool() 注册
from . import (  # noqa: F401
    calculator,
    convert_currency,
    get_time_info,
    get_weather,
    search_info,
)

__all__ = ["mcp"]
