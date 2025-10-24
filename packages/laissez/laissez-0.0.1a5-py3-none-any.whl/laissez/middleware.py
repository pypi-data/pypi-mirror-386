"""
==========
LAISSEZ
==========
"""

import asyncio
import base64
import json
import logging
from fastmcp.server.http import StarletteWithLifespan
from eth_account import Account
from typing import List, cast
from starlette.responses import JSONResponse
from starlette.types import Message, Receive, Scope, Send
from x402.facilitator import FacilitatorClient
from x402.common import find_matching_payment_requirements, process_price_to_atomic_amount, x402_VERSION
from x402.types import PaymentPayload, PaymentRequirements, x402PaymentRequiredResponse, SupportedNetworks
from laissez.types import PaidTool


logger = logging.getLogger(__name__)


class RequestReplay:
    def __init__(self, receive: Receive, body: bytes):
        self._receive = receive
        self._body = body
        self._called = False
        self._lock = asyncio.Lock()

    async def __call__(self) -> Message:
        async with self._lock:
            if not self._called:
                self._called = True
                return {"type": "http.request", "body": self._body, "more_body": False}
        return await self._receive()


class LaissezMcpServerMiddleware:
    def __init__(self, app: StarletteWithLifespan, tools: List[PaidTool], wallet: Account):
        self.app = app
        self.tools = tools
        self.wallet = wallet
        self.facilitator = FacilitatorClient()

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        method = scope.get("method", "")
        path = scope.get("path", "")
        scheme = scope.get("scheme", "https")

        # Check if it's an MCP POST request
        if method != "POST" or not path.startswith("/mcp"):
            logger.debug("Non-MCP HTTP %s request to %s, passing through", method, path)
            await self.app(scope, receive, send)
            return
        
        # Parse the MCP request body
        body = b''
        more_body = True
        while more_body:
            message = await receive()
            if message['type'] == 'http.request':
                body += message.get('body', b'')
                more_body = message.get('more_body', False)
        
        receive_replay = RequestReplay(receive, body)

        # Parse the tool action
        tool_action = None
        if body:
            try:
                mcp_request = json.loads(body)
                tool_action = mcp_request.get("method")
            except json.JSONDecodeError:
                logger.warning("Failed to parse MCP request body: %s", body)
                
        if tool_action != "tools/call":
            logger.debug("MCP method %s does not require payment, passing through", tool_action)
            await self.app(scope, receive_replay, send)
            return

        # Parse the tool name
        tool_parameters = mcp_request.get("params", {})
        tool_name = tool_parameters.get("name")

        if not tool_name:
            logger.warning("MCP request missing tool name, passing through")
            await self.app(scope, receive_replay, send)
            return

        logger.debug("MCP request for tool %s", tool_name)

        # Check if the tool is in the payment config
        tool_names = [tool.name for tool in self.tools]
        if tool_name not in tool_names:
            logger.info("Tool %s not configured for payments, passing through", tool_name)
            await self.app(scope, receive_replay, send)
            return

        # Build the payment requirements
        headers = { k.decode().lower(): v.decode() for k, v in scope.get("headers", []) }
        tool = self.tools[tool_names.index(tool_name)]
        price = str(tool.price)
        network = tool.network

        try:
            max_amount, asset_address, eip712 = process_price_to_atomic_amount(price, network)
        except ValueError as e:
            error_response = JSONResponse(content={"error": f"Invalid price configuration: {str(e)}"}, status_code=500)
            await error_response(scope, receive_replay, send)
            return

        host = headers.get("host", "")
        resource_url = f"{scheme}://{host}{path}"
        
        payment_requirements = [
            PaymentRequirements(
                scheme="exact",
                network=cast(SupportedNetworks, network),
                asset=asset_address,
                max_amount_required=max_amount,
                resource=resource_url,
                description=tool.description,
                mime_type="application/json",
                pay_to=self.wallet.address,
                max_timeout_seconds=60,
                extra=eip712,
            )
        ]

        # Check if payment is required
        if 'x-payment' not in headers:
            logger.info("Payment required for tool %s", tool_name)

            response_data = x402PaymentRequiredResponse(
                x402_version=x402_VERSION,
                accepts=payment_requirements,
                error=f"Payment required for {tool_name}",
            ).model_dump(by_alias=True)

            error_response = JSONResponse(content=response_data, status_code=402)
            await error_response(scope, receive_replay, send)
            return

        # Decode the X-Payment header
        try:
            payment_dictionary = json.loads(base64.b64decode(headers['x-payment']))
            payment = PaymentPayload(**payment_dictionary)
        except Exception as e:
            logger.warning("Failed to decode X-Payment header: %s", e)
            error_response = JSONResponse(content={"error": f"Invalid payment header format: {str(e)}"}, status_code=400)
            await error_response(scope, receive_replay, send)
            return
            
        selected_payment_requirements = find_matching_payment_requirements(
            payment_requirements=payment_requirements,
            payment=payment
        )


        if not selected_payment_requirements:
            logger.warning("No matching payment requirements found for tool %s", tool_name)
            error_response = JSONResponse(content={"error": f"No matching payment requirements found"}, status_code=400)
            await error_response(scope, receive_replay, send)
            return

        # TODO
        # THIS IS FINE FOR BASE-SEPOLIA
        # BUT WILL NEED TO BE CALL TO LAISSEZ BACKEND FOR MAINNET
        verify_response = await self.facilitator.verify(payment, selected_payment_requirements)

        if not verify_response.is_valid:
            logger.warning("Payment verification failed for tool %s: %s", tool_name, verify_response.invalid_reason)
            error_response = JSONResponse(content={"error": f"Payment verification failed: {verify_response.invalid_reason}"}, status_code=402)
            await error_response(scope, receive_replay, send)
            return


        logger.info("Payment verified for tool %s", tool_name)

        async def send_wrapper(message: Message):
            if message['type'] == 'http.response.start':
                status_code = message['status']
                if 200 <= status_code < 300:
                    try:
                        settle_response = None
                        reason = 'unknown_settle_error'
                        for attempt in range(3):
                            try:
                                settle_response = await self.facilitator.settle(
                                    payment, selected_payment_requirements
                                )
                            except Exception as settle_error:
                                reason = f"settlement_exception:{settle_error}"
                                logger.exception(
                                    "Payment settlement attempt %s raised an exception for tool %s",
                                    attempt + 1,
                                    tool_name,
                                )
                                settle_response = None
                            else:
                                if settle_response and settle_response.success:
                                    break
                                reason = (
                                    settle_response.error_reason
                                    if settle_response
                                    else 'unknown_settle_error'
                                )
                                if attempt < 2:
                                    logger.warning(
                                        "Payment settlement attempt %s failed for tool %s: %s",
                                        attempt + 1,
                                        tool_name,
                                        reason,
                                    )
                            if settle_response and settle_response.success:
                                break
                            if attempt < 2:
                                await asyncio.sleep(0.5 * (attempt + 1))

                        if settle_response and settle_response.success:
                            settlement_payload = settle_response.model_dump_json(by_alias=True)
                            settlement_header = base64.b64encode(
                                settlement_payload.encode('utf-8')
                            ).decode('utf-8')
                            message['headers'].append(
                                (b'X-Payment-Response', settlement_header.encode('utf-8'))
                            )
                            message['headers'].append(
                                (b'Access-Control-Expose-Headers', b'X-Payment-Response')
                            )
                            logger.info("Payment settled for tool %s", tool_name)
                        else:
                            message['headers'].append(
                                (b'X-Payment-Error', reason.encode('utf-8'))
                            )
                            logger.warning("Payment settlement failed for tool %s: %s", tool_name, reason)
                    except Exception as e:
                        error_message = f"settlement_exception:{e}"
                        message['headers'].append(
                            (b'X-Payment-Error', error_message.encode('utf-8'))
                        )
                        logger.exception("Payment settlement raised an exception for tool %s", tool_name)
            await send(message)

        await self.app(scope, receive_replay, send_wrapper)