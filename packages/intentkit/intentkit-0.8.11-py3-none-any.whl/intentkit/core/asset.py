"""Shared asset retrieval utilities for agents."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

import httpx
from pydantic import BaseModel, Field
from web3 import Web3

from intentkit.clients.web3 import get_web3_client
from intentkit.config.config import config
from intentkit.models.agent import Agent
from intentkit.models.agent_data import AgentData
from intentkit.utils.error import IntentKitAPIError

logger = logging.getLogger(__name__)

# USDC contract addresses for different networks
USDC_ADDRESSES = {
    "base-mainnet": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "ethereum-mainnet": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "arbitrum-mainnet": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
    "optimism-mainnet": "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85",
    "polygon-mainnet": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
}

# NATION token address for base-mainnet
NATION_ADDRESS = "0x2f74f818e81685c8086dd783837a4605a90474b8"


class Asset(BaseModel):
    """Model for individual asset with symbol and balance."""

    symbol: str = Field(description="Asset symbol (e.g., ETH, USDC, NATION)")
    balance: Decimal = Field(description="Asset balance as decimal")


class AgentAssets(BaseModel):
    """Simplified agent asset response with wallet net worth and tokens."""

    net_worth: str = Field(description="Total wallet net worth in USD")
    tokens: list[Asset] = Field(description="List of assets with symbol and balance")


async def _get_token_balance(
    web3_client: Web3, wallet_address: str, token_address: str
) -> Decimal:
    """Get ERC-20 token balance for a wallet address."""
    try:
        # ERC-20 standard ABI for balanceOf and decimals
        erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function",
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function",
            },
        ]

        contract = web3_client.eth.contract(
            address=web3_client.to_checksum_address(token_address), abi=erc20_abi
        )

        balance_wei = contract.functions.balanceOf(
            web3_client.to_checksum_address(wallet_address)
        ).call()
        decimals = contract.functions.decimals().call()

        # Convert from wei to token units using actual decimals
        balance = Decimal(balance_wei) / Decimal(10**decimals)
        return balance
    except Exception as exc:  # pragma: no cover - log path only
        logger.error("Error getting token balance: %s", exc)
        return Decimal("0")


async def _get_eth_balance(web3_client: Web3, wallet_address: str) -> Decimal:
    """Get ETH balance for a wallet address."""
    try:
        balance_wei = web3_client.eth.get_balance(
            web3_client.to_checksum_address(wallet_address)
        )
        balance = Decimal(balance_wei) / Decimal(10**18)
        return balance
    except Exception as exc:  # pragma: no cover - log path only
        logger.error("Error getting ETH balance: %s", exc)
        return Decimal("0")


async def _get_wallet_net_worth(wallet_address: str) -> str:
    """Get wallet net worth using Moralis API."""
    try:
        async with httpx.AsyncClient() as client:
            url = (
                "https://deep-index.moralis.io/api/v2.2/wallets/"
                f"{wallet_address}/net-worth"
            )
            headers = {
                "accept": "application/json",
                "X-API-Key": config.moralis_api_key,
            }
            params = {
                "exclude_spam": "true",
                "exclude_unverified_contracts": "true",
                "chains": ["eth", "base", "polygon", "arbitrum", "optimism"],
            }

            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("total_networth_usd", "0")
    except Exception as exc:  # pragma: no cover - log path only
        logger.error("Error getting wallet net worth for %s: %s", wallet_address, exc)
        return "0"


async def _build_assets_list(
    agent: Agent, agent_data: AgentData, web3_client: Web3
) -> list[Asset]:
    """Build the assets list based on network conditions and agent configuration."""
    assets: list[Asset] = []

    if not agent_data or not agent_data.evm_wallet_address:
        return assets

    wallet_address = agent_data.evm_wallet_address
    network_id: Optional[str] = agent.network_id

    # ETH is always included
    eth_balance = await _get_eth_balance(web3_client, wallet_address)
    assets.append(Asset(symbol="ETH", balance=eth_balance))

    if network_id and network_id.endswith("-mainnet"):
        usdc_address = USDC_ADDRESSES.get(str(network_id))
        if usdc_address:
            usdc_balance = await _get_token_balance(
                web3_client, wallet_address, usdc_address
            )
            assets.append(Asset(symbol="USDC", balance=usdc_balance))

    if network_id == "base-mainnet":
        nation_balance = await _get_token_balance(
            web3_client, wallet_address, NATION_ADDRESS
        )
        assets.append(Asset(symbol="NATION", balance=nation_balance))

    if agent.ticker and agent.token_address:
        lower_addresses = [addr.lower() for addr in USDC_ADDRESSES.values()]
        is_usdc = agent.token_address.lower() in lower_addresses
        is_nation = agent.token_address.lower() == NATION_ADDRESS.lower()

        if not is_usdc and not is_nation:
            custom_balance = await _get_token_balance(
                web3_client, wallet_address, agent.token_address
            )
            assets.append(Asset(symbol=agent.ticker, balance=custom_balance))

    return assets


async def agent_asset(agent_id: str) -> AgentAssets:
    """Fetch wallet net worth and token balances for an agent."""
    agent = await Agent.get(agent_id)
    if not agent:
        raise IntentKitAPIError(404, "AgentNotFound", "Agent not found")

    agent_data = await AgentData.get(agent_id)
    if not agent_data or not agent_data.evm_wallet_address:
        return AgentAssets(net_worth="0", tokens=[])

    if not agent.network_id:
        return AgentAssets(net_worth="0", tokens=[])

    try:
        web3_client = get_web3_client(str(agent.network_id))
        tokens = await _build_assets_list(agent, agent_data, web3_client)
        net_worth = await _get_wallet_net_worth(agent_data.evm_wallet_address)
        return AgentAssets(net_worth=net_worth, tokens=tokens)
    except IntentKitAPIError:
        raise
    except Exception as exc:
        logger.error("Error getting agent assets for %s: %s", agent_id, exc)
        raise IntentKitAPIError(
            500, "AgentAssetError", "Failed to retrieve agent assets"
        ) from exc


__all__ = [
    "Asset",
    "AgentAssets",
    "USDC_ADDRESSES",
    "NATION_ADDRESS",
    "agent_asset",
    "_build_assets_list",
    "_get_wallet_net_worth",
]
