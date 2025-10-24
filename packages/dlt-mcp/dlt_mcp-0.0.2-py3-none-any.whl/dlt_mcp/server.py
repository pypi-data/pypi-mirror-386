from __future__ import annotations

from fastmcp import FastMCP

from dlt_mcp._tools import TOOLS_REGISTRY


def create_server() -> FastMCP:
    """Create an instance of the FastMCP server and register
    tools, prompts, and resources on it.
    """
    tools = tuple(TOOLS_REGISTRY.values())

    server = FastMCP(
        name="dlt MCP",
        instructions="Helps you build with the dlt Python library.",
        tools=tools,  # type: ignore[invalid-argument-type]
    )

    return server


def start() -> None:
    server = create_server()
    server.run()
