import asyncio
import json
import sys

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


def parse_tool_result(result):
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

    return parsed_items


async def main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_servers.hotel_server"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("TOOLS:", [tool.name for tool in tools.tools])

            result = await session.call_tool(
                "search_hotels",
                {"city": "Bangkok"},
            )

            parsed = parse_tool_result(result)

            print("IS ERROR:", result.isError)
            print("COUNT:", len(parsed))
            print("FIRST:", parsed[0] if parsed else "no results")


if __name__ == "__main__":
    asyncio.run(main())