import asyncio
import json
import os
import sys
from typing import Any

from concurrent.futures import ThreadPoolExecutor
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, get_default_environment, stdio_client


class MCPToolError(RuntimeError):
    """Raised when an MCP server or tool call fails."""


SERVER_MODULES = {
    "hotel": "mcp_servers.hotel_server",
    "flight": "mcp_servers.flight_server",
}

SERVER_ENV_VARS = {
    "hotel": "HOTEL_PROVIDER_BASE_URL",
    "flight": "FLIGHT_PROVIDER_BASE_URL",
}


def _server_environment(server: str) -> dict[str, str]:
    variable_name = SERVER_ENV_VARS[server]
    variable_value = os.getenv(variable_name, "").strip()

    if not variable_value:
        raise MCPToolError(
            f"{variable_name} is required to launch the {server} MCP server."
        )

    environment = get_default_environment()
    environment[variable_name] = variable_value

    return environment


def call_mcp_tool(server: str, tool_name: str, arguments: dict | None = None) -> Any:
    """
    Synchronous wrapper used by LangChain tools.

    Runs the async MCP call in a worker thread so it works both from normal
    scripts and from FastAPI/LangGraph contexts that already have an event loop.
    """
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            asyncio.run, _call_mcp_tool_async(server, tool_name, arguments or {})
        )
        return future.result()


async def _call_mcp_tool_async(server: str, tool_name: str, arguments: dict) -> Any:
    if server not in SERVER_MODULES:
        raise MCPToolError(f"Unknown MCP server: {server}")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", SERVER_MODULES[server]],
        env=_server_environment(server),
    )

    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                result = await session.call_tool(tool_name, arguments)

                if result.isError:
                    raise MCPToolError(f"MCP tool failed: {tool_name}")

                return _parse_tool_result(result)

    except Exception as exc:
        if isinstance(exc, MCPToolError):
            raise
        raise MCPToolError(f"MCP call failed for {server}.{tool_name}: {exc}") from exc


def _parse_tool_result(result: Any) -> Any:
    parsed_items = []

    for content_item in result.content:
        text = getattr(content_item, "text", None)

        if not text:
            continue

        value = json.loads(text)

        if isinstance(value, list):
            parsed_items.extend(value)
        else:
            parsed_items.append(value)

    if len(parsed_items) == 1:
        return parsed_items[0]

    return parsed_items