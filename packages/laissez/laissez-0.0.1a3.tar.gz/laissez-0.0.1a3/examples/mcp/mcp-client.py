"""
==========
LAISSEZ
==========

EXAMPLE: MCP Client with Laissez

This example shows how to use Laissez with the MCP client from the Pydantic AI SDK.

Pre-requisites:
* Ensure that you are running the paid MCP server from `examples/mcp/paid-mcp-server.py`.
    * You can do so from the root of the project by running `uv run examples/mcp/paid-mcp-server.py`.
* Update `BASE_URL` in this file to point to the URL of this example paid MCP server

To run:
* Run this file from the root of the project by running `uv run examples/mcp/mcp-client.py`.
"""

import asyncio
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP
from laissez.client import LaissezClient
from dotenv import load_dotenv

load_dotenv()

LOCAL = True
BASE_URL = 'http://127.0.0.1:8000' if LOCAL else 'https://dice-roll.laissez.xyz'
laissez_client = LaissezClient()


async def main():

    server = MCPServerStreamableHTTP(
        url=f'{BASE_URL}/mcp',
        http_client=laissez_client   
    )

    agent = Agent(
        model='openai:gpt-5-mini',
        instructions='Show your working out',
        toolsets=[server]
    )

    result = await agent.run("Roll a dice twice then multiply the two results and return the final result")
    print(result.output)


if __name__ == '__main__':
    asyncio.run(main())