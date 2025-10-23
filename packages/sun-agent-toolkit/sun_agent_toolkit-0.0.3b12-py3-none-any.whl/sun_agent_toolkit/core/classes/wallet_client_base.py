from abc import ABC, abstractmethod
from typing import Any, TypedDict

from pydantic import BaseModel, Field
from sun_agent_toolkit.core.classes.tool_base import ToolBase, create_tool
from sun_agent_toolkit.core.types.chain import Chain
from sun_agent_toolkit.core.types.token import Token


class EmptyParams(BaseModel):
    pass


class BalanceParams(BaseModel):
    address: str = Field(description="The wallet address to check the balance of")
    tokenAddress: str | None = Field(description="The token address to check the balance of", default=None)


class Signature(TypedDict):
    signature: str


class Balance(TypedDict):
    decimals: int
    symbol: str
    name: str
    value: str
    in_base_units: str


class WalletClientBase(ABC):
    @abstractmethod
    def get_address(self) -> str:
        pass

    @abstractmethod
    def get_chain(self) -> Chain:
        pass

    @abstractmethod
    async def sign_message(self, message: str) -> Signature:
        pass

    @abstractmethod
    def balance_of(self, address: str, token_address: str | None = None) -> Balance:
        pass

    def get_token_info_by_ticker(self, ticker: str) -> Token:
        raise NotImplementedError("get_token_info_by_ticker is not implemented for this wallet client")

    def get_core_tools(self) -> list[ToolBase[Any]]:
        return [
            create_tool(
                {"name": "get_address", "description": "Get the address of the wallet", "parameters": EmptyParams},
                lambda _: self.get_address(),
            ),
            create_tool(
                {"name": "get_chain", "description": "Get the chain of the wallet", "parameters": EmptyParams},
                lambda _: self.get_chain(),
            ),
            create_tool(
                {"name": "get_balance", "description": "Get the balance of the wallet", "parameters": BalanceParams},
                lambda parameters: self.balance_of(parameters["address"], parameters.get("tokenAddress")),
            ),
        ]
