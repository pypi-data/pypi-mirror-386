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

import random
import secrets
from fastmcp import FastMCP
from eth_account import Account
from laissez.types import PaidTool
from laissez.mcp import LaissezMCPProvider
from dotenv import load_dotenv

load_dotenv()


# STEP 1: CREATE YOUR MCP
mcp = FastMCP("Dice Roller")

@mcp.tool
def roll_die() -> int:
    return random.randint(1, 6)

@mcp.tool
def multiply(a: int, b: int) -> int:
    return a * b



# STEP 2: DEFINE YOUR PAID TOOLS
paid_tools = [
    PaidTool(name="roll_die", price=0.001, description="Roll a die and return the result"),
    PaidTool(name="multiply", price=0.005, description="Multiply two numbers and return the result"),
]



# STEP 3: CREATE OR BRING YOUR WALLET
random_string = secrets.token_urlsafe(32)
wallet = Account.create(random_string)



# STEP 4: RECEIVE PAYMENTS WITH LAISSEZ
app = LaissezMCPProvider(
    mcp=mcp,
    tools=paid_tools,
    wallet=wallet
)


if __name__ == "__main__":
    app.run()