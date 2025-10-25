"""
==========
LAISSEZ
==========
"""

import asyncio
import logging
from typing import Optional, Tuple, List
from httpx import AsyncClient, Headers
from fastmcp import FastMCP
from pydantic_ai.mcp import MCPServerStreamableHTTP
from eth_account import Account

from x402.clients.base import x402Client
from x402.clients.httpx import x402HttpxClient as BaseX402HttpxClient
from x402.types import x402PaymentRequiredResponse

from laissez.types import PaymentLog, PaidTool
from laissez.common import check_and_create_wallet, get_laissez_api_key, print_ascii_art
from laissez.hooks import LaissezHttpxHooks
from laissez.middleware import LaissezMcpServerMiddleware

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


class LaissezMCPConnector(MCPServerStreamableHTTP):
    def __init__(
        self,
        url: str,
        api_key: Optional[str] = None,
        wallet: Optional[Account] = None,
    ):
        api_key = get_laissez_api_key(api_key)
        wallet = check_and_create_wallet(wallet)
        print_ascii_art()

        laissez_httpx_client = BaseX402HttpxClient(account=wallet, follow_redirects=True, timeout=30.0)
        x402_client = x402Client(account=wallet)
        
        self._backend = AsyncClient(
            base_url="https://app.laissez.xyz",
            timeout=30.0,
            headers=Headers({
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "laissez-client-python/0.0.1a3",
            }),
        )

        async def _on_payment(payment_log: PaymentLog) -> None:
            try:
                payload = payment_log.model_dump()
                resp = await self._backend.post("/api/v0/log", json=payload)
                if resp.status_code >= 400:
                    logger.warning("Failed to post payment log: status=%s", resp.status_code)
                else:
                    logger.debug("Payment logged successfully")
            except Exception as e:
                logger.warning("Error posting payment log: %s", e)




        async def _before_payment(payment_response: x402PaymentRequiredResponse) -> Tuple[bool, str]:
            """
            Calls the laissez backend to check if payment should proceed.
            Raises an exception if payment is not approved.
            """
            try:
                payload = payment_response.model_dump()
                resp = await self._backend.post("/api/v0/guard", json=payload)
                if resp.status_code != 200:
                    return False, f"Payment guard check failed with status {resp.status_code}"

                data = resp.json()
                approved = data.get("approved", False)
                reason = data.get("reason", "No reason provided.")
                return approved, reason

            except Exception as e:
                logger.warning("Payment guard check error: %s", e)
                return False, str(e)


        hooks = LaissezHttpxHooks(
            client=x402_client, on_payment=_on_payment, before_payment=_before_payment
        )
        laissez_httpx_client.event_hooks = {
            "request": [hooks.on_request],
            "response": [hooks.on_response]
        }

        super().__init__(url=str(url), http_client=laissez_httpx_client)





class LaissezMCPProvider:
    def __init__(self, mcp: FastMCP, tools: List[PaidTool], wallet: Account):

        self.mcp = mcp
        self.wallet = check_and_create_wallet(wallet)

        mcp_tools = asyncio.run(mcp.get_tools())
        processed_tools = []
        for tool in tools:
            if tool.name not in mcp_tools:
                logger.info("Paid tool %s not available on MCP server; skipping", tool.name)
                continue
            else:
                processed_tools.append(tool)
        self.tools = processed_tools
        


    def run(self) -> None:
        app = self.mcp.http_app(
            transport='streamable-http',
            stateless_http=True
        )
        app.add_middleware(LaissezMcpServerMiddleware, tools=self.tools, wallet=self.wallet)
        print_ascii_art()
        import uvicorn
        uvicorn.run(app, host="127.0.0.1", port=8000, ws="none")