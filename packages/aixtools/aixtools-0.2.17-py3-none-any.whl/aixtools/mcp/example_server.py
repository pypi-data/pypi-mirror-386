"""
Example server implementation for Model Context Protocol (MCP).
"""

from aixtools.mcp.fast_mcp_log import FastMcpLog

mcp = FastMcpLog("Demo")
# mcp = FastMCP("Demo")


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"
