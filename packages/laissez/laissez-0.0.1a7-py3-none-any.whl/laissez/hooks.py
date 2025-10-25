"""
==========
LAISSEZ
==========
"""

import asyncio
import json
import logging
from typing import Callable, Optional, Awaitable
from httpx import AsyncClient, Response
from x402.clients.base import MissingRequestConfigError, PaymentError, decode_x_payment_response, x402Client
from x402.clients.httpx import HttpxHooks
from x402.types import x402PaymentRequiredResponse
from laissez.types import PaymentLog


logger = logging.getLogger(__name__)


class LaissezHttpxHooks(HttpxHooks):
    def __init__(
        self,
        client: x402Client,
        on_payment: Optional[Callable[[PaymentLog], Awaitable[None]]] = None,
        before_payment: Optional[
            Callable[[x402PaymentRequiredResponse], Awaitable[None]]
        ] = None,
    ):
        super().__init__(client=client)
        self.on_payment = on_payment
        self.before_payment = before_payment
        self.payment_creation_lock = asyncio.Lock()

    async def on_response(self, response: Response) -> Response:
        if response.status_code != 402:
            return response

        if response.request and response.request.extensions.get("x402_retry"):
            return response

        try:
            if not response.request:
                raise MissingRequestConfigError("Missing request configuration")

            await response.aread()
            data = response.json()
            payment_response = x402PaymentRequiredResponse(**data)

            if self.before_payment:
                try:
                    approved, reason = await self.before_payment(payment_response)
                except Exception as e:
                    logger.warning("Payment guard hook raised an exception: %s", e)
                    return response

                if not approved:

                    request_id = None
                    tool_name = None
                    if response.request and response.request.content:
                        try:
                            request_data = json.loads(response.request.content)
                            request_id = request_data.get("id")
                            tool_name = (
                                request_data.get("params", {}).get("name")
                                if isinstance(request_data, dict)
                                else None
                            )
                        except json.JSONDecodeError:
                            pass

                    tool_label = tool_name or "unknown tool"
                    logger.info("Payment guard rejected payment for %s: %s", tool_label, reason)
                    rejection_message = (
                        f"Laissez guard blocked payment for '{tool_label}': {reason}. "
                        "Please finish the task without using that paid tool."
                    )

                    structured_detail = {
                        "type": "payment_rejected",
                        "tool": tool_name,
                        "reason": reason,
                    }

                    result_content = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": rejection_message,
                                }
                            ],
                            "structuredContent": structured_detail,
                            "isError": False,
                        },
                    }

                    response.status_code = 200
                    response.headers['Content-Type'] = 'application/json'
                    response._content = str.encode(json.dumps(result_content))
                    return response

            async with self.payment_creation_lock:
                selected_requirements = self.client.select_payment_requirements(
                    payment_response.accepts
                )

                payment_header = self.client.create_payment_header(
                    selected_requirements, payment_response.x402_version
                )

                request = response.request
                request.headers["X-Payment"] = payment_header
                request.extensions["x402_retry"] = True

                async with AsyncClient(follow_redirects=True, timeout=30.0) as client:
                    retry_response = await client.send(request)

                if 200 <= retry_response.status_code < 300:

                    if 'x-payment-error' in retry_response.headers:
                        logger.warning(
                            "Server reported payment settlement failure: %s",
                            retry_response.headers['x-payment-error'],
                        )
                        return retry_response


                    payment_info = "with unknown details"
                    decoded_header = {}
                    
                    if 'x-payment-response' in retry_response.headers:
                        try:
                            decoded_header = decode_x_payment_response(retry_response.headers['x-payment-response'])
                            payment_info = f"\nTransaction: {decoded_header.get('transaction')}\n\tPayer: {decoded_header.get('payer')}\n\tNetwork: {decoded_header.get('network')}"
                        except Exception as e:
                            payment_info = f"with settlement details that could not be decoded: {e}"
                            logger.debug("Failed to decode payment settlement details: %s", e)

                    logger.info("Payment authorized: %s", payment_info)

                    # post to laissez db
                    payment_log = PaymentLog(
                        transaction_hash=decoded_header.get("transaction", "unknown"),
                        network=selected_requirements.network,
                        description=selected_requirements.description,
                        paid_to=selected_requirements.pay_to,
                        paid_by=decoded_header.get("payer", self.client.account.address),
                        amount=selected_requirements.max_amount_required,
                        unit=selected_requirements.extra.get("name", "unknown"),
                    )

                    if self.on_payment:
                        try:
                            await self.on_payment(payment_log)
                        except Exception as e:
                            logger.warning("Failed to forward payment log: %s", e)
                            pass

                    response.status_code = retry_response.status_code
                    response.headers.clear()
                    response.headers.update(retry_response.headers)
                    response._content = await retry_response.aread()
                    response.request = retry_response.request

                    logger.debug("Payment header applied and request retried successfully")
                    return response
                else:
                    await retry_response.aread()
                    return retry_response

        except PaymentError as e:
            logger.error("Payment error while handling response: %s", e)
            return response
        except Exception as e:
            logger.exception("Unexpected error during payment handling")
            return response