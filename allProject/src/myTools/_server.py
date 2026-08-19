"""共享的 FastMCP 服务器实例。

各工具模块通过 `from ._server import mcp` 引用此实例，
并使用 `@mcp.tool()` 装饰器将函数注册为 MCP 工具。
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("smart-assistant-tools")
