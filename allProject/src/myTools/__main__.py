"""以 MCP 服务器方式运行本工具包。

使用方式：
    python -m myTools

默认通过 stdio 传输协议对外暴露所有已注册的 MCP 工具。
"""
from . import mcp  # noqa: F401  导入即触发各工具模块的 @mcp.tool() 注册

if __name__ == "__main__":
    mcp.run()
