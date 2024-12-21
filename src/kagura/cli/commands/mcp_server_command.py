# cli/commands/mcp_server.py

from typing import Any, List

# import anyio
import click
from mcp.server import Server

from mcp.types import Tool

# from mcp.types import TextContent, Tool

from kagura.core.agent import Agent


@click.command()
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)
def mcp_server(port: int, transport: str) -> int:
    server = Server("kagura-mcp-server")

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        print("Listing list_tools...")
        tools = []
        for agent_info in Agent.list_agents():
            print(f"Agent info: {agent_info}")
            tools.append(
                Tool(
                    name=agent_info["name"],
                    description=agent_info["description"],
                    inputSchema=agent_info["input_schema"],
                )
            )
        return tools

    @server.call_tool()
    async def kagura_agent_tool(name: str, arguments: dict) -> List[Any]:
        # WIP
        # print(f"Calling tool {name} with arguments {arguments}")
        # agent = Agent.assigner(name, arguments)
        # if agent.is_workflow:
        #     text = ""
        #     async for update in await agent.execute():
        #         if update.COMPLETED:
        #             text = update
        #     return [TextContent(type="text", text=text)]

        # else:
        #     result = await agent.execute()
        # return [TextContent(type="text", text=result)]
        return []

    # if transport == "sse":
    #    from mcp.server.sse import SseServerTransport
    #    from starlette.serverlications import Starlette
    #    from starlette.routing import Route

    #    sse = SseServerTransport("/messages")

    #    async def handle_sse(request):
    #        async with sse.connect_sse(
    #            request.scope, request.receive, request._send
    #        ) as streams:
    #            await server.run(
    #                streams[0], streams[1], server.create_initialization_options()
    #            )

    #    async def handle_messages(request):
    #        await sse.handle_post_message(request.scope, request.receive, request._send)

    #    starlette_server = Starlette(
    #        debug=True,
    #        routes=[
    #            Route("/sse", endpoint=handle_sse),
    #            Route("/messages", endpoint=handle_messages, methods=["POST"]),
    #        ],
    #    )

    #    import uvicorn

    #    uvicorn.run(starlette_server, host="0.0.0.0", port=port)
    # else:
    #    from mcp.server.stdio import stdio_server

    #    async def arun():
    #        async with stdio_server() as streams:
    #            await server.run(
    #                streams[0], streams[1], server.create_initialization_options()
    #            )

    #    anyio.run(arun)

    return 0


if __name__ == "__main__":
    import asyncio

    asyncio.run(mcp_server())
