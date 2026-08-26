"""MCP SDK 版本兼容：2.x 的 MCPServer 与 1.x 的 FastMCP 接口一致
（tool 装饰器 / run 默认 stdio），只有类名与模块路径变了。"""
try:  # mcp >= 2.0
    from mcp.server.mcpserver import MCPServer as FastMCP
except ModuleNotFoundError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP

__all__ = ["FastMCP"]
