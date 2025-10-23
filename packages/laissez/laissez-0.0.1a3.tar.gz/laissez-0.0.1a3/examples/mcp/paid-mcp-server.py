"""
==========
LAISSEZ
==========

EXAMPLE: Paid MCP Server with Laissez

This example shows how to create a paid MCP server with Laissez.

Pre-requisites:
* Ensure that the names of the paid tools in the `paid_tools` list match the names of the tools in the MCP server

To run:
* Run this file from the root of the project by running `uv run examples/mcp/paid-mcp-server.py`.
"""

from fastmcp import FastMCP
import random
from laissez.server import create_paid_mcp_app, PaidTool
from dotenv import load_dotenv
import secrets
from eth_account import Account

load_dotenv()

mcp = FastMCP("Dice Roller")

@mcp.tool
def roll_die() -> int:
    return random.randint(1, 6)

@mcp.tool
def multiply(a: int, b: int) -> int:
    return a * b


paid_tools = [
    PaidTool(name="roll_die", price=0.001, description="Roll a die and return the result"),
    PaidTool(name="multiply", price=0.005, description="Multiply two numbers and return the result"),
]


if __name__ == "__main__":
    import uvicorn
    import asyncio 

    random_string = secrets.token_urlsafe(32)
    wallet = Account.create(random_string)

    app = asyncio.run(create_paid_mcp_app(mcp, paid_tools, wallet))
    uvicorn.run(app, host="127.0.0.1", port=8000)