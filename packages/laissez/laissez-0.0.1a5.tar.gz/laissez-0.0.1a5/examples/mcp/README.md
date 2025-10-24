# Laissez MCP Examples

## Motivation
These scripts demonstrate how users can use Laissez to create paid MCP server tools and MCP clients that pay for those tools. The paid server exposes MCP tools behind Laissez payment enforcement, while the client shows how an agent pays and invokes those tools over HTTP. Payments are settled using x402, and logged to the Laissez App at https://app.laissez.xyz.

## Prerequisites
- Install dependencies for the examples group:
  - `uv sync --group examples`
- Ensure you have a Laissez API key. You can get one by following the Laissez CLI set-up wizard when running the examples, or by visiting https://app.laissez.xyz.
- Ensure you have an OpenAI API key to run the MCP client example.

## Run the Paid MCP Server
- Command: `uv run examples/mcp/paid-mcp-server.py`
- What happens:
  - Starts a FastMCP app serving two paid tools: `roll_die` and `multiply`.
  - Generates a throwaway wallet for settling micro-payments.
  - Listens on `http://127.0.0.1:8000`.

## Run the MCP Client Example
- Ensure the server is running locally (or update `BASE_URL` in `examples/mcp/mcp-client.py`).
- Command: `uv run examples/mcp/mcp-client.py`
- What happens:
  - Creates a `pydantic_ai` agent using `LaissezMCPConnector` to connect to the paid MCP server.
  - Calls the paid MCP tools to roll two dice, multiply the results, and prints the outcome.

## Takeaways
- **Paid access flow**: `LaissezMCPProvider` wraps MCP tools with Laissez paywalls.
- **Client integration**: `LaissezMCPConnector` enables agents to authenticate and pay for MCP tool calls seamlessly.
