"""
==========
LAISSEZ
==========
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal

class PaymentLog(BaseModel):
    transaction_hash: str
    network: str
    description: str
    paid_to: str
    paid_by: str
    amount: str
    unit: str


class PaidTool(BaseModel):
    """
    Configure a paid tool for an MCP server.

    Args:
        name: The name of the tool
        price: The price of the tool in USDC. Defaults to 0.001.
        network: The network to use for the tool. Defaults to 'base-sepolia'.
        description: The description of the tool
    """
    name: str = Field(..., description="The name of the tool")
    price: float = Field(0.001, description="The price of the tool in USDC")
    network: Optional[Literal['base-sepolia', 'base']] = Field('base-sepolia', description="The network to use for the tool")
    description: str = Field(..., description="The description of the tool")