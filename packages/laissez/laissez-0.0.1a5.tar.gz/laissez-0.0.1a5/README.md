# Laissez

Agent spending you can trust.

## What you get
- **Paid MCP server**: Create a paid MCP server using `LaissezMCPProvider`.
- **Paying MCP client**: Use `LaissezMCPConnector` to connect to paid MCP servers and pay for their tools automatically.
- **Transparent settlement**: Payments are finalized with x402 and appear in the Laissez App dashboard at <https://app.laissez.xyz>.

## Set up once
- `uv sync --group examples` to pull the example dependencies.
- Grab a Laissez API key via the CLI wizard when you first run the examples, or from <https://app.laissez.xyz>.
- Export your OpenAI API key (the client agent calls an OpenAI model).
- Optional: add the keys to a `.env`; the examples load it with `python-dotenv`.

## Run the paid MCP server
- Command: `uv run examples/mcp/paid-mcp-server.py`
- What happens: spins up a FastMCP streamable http server on `http://127.0.0.1:8000`, generates a temporary wallet (if not provided), and exposes paid tools (e.g. `roll_die`, `multiply`) behind Laissez enforcement. All with the simplicity of `LaissezMCPProvider`.

## Run the paying MCP client
- Ensure the server is live or update `BASE_URL` in `examples/mcp/mcp-client.py` to point at your deployment.
- Command: `uv run examples/mcp/mcp-client.py`
- What happens: creates a `pydantic_ai` agent backed by `LaissezMCPConnector`, pays for two dice rolls plus a multiply call, and prints the result.

## Keep exploring
- See `examples/mcp/README.md` for a deeper walkthrough of the server and client.
- Tweak prices, add more tools, or swap in different MCP agents to prototype your own billing flows.