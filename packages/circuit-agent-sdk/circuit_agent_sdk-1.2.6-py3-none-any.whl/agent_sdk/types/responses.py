"""
Response type definitions for the Agent SDK.

This module provides all response models returned by SDK operations.
All models use strict Pydantic validation for type safety.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .swidge import SwidgeData, SwidgeExecuteResponseData


class SignAndSendData(BaseModel):
    """
    Success data from sign_and_send operations.

    This data is returned in the `data` field when a transaction is successfully
    signed and broadcast.

    Attributes:
        internal_transaction_id: Internal transaction ID for tracking
        tx_hash: Transaction hash once broadcast to the network
        transaction_url: Optional transaction URL (explorer link)
    """

    internal_transaction_id: int = Field(
        ..., description="Internal transaction ID for tracking"
    )
    tx_hash: str = Field(..., description="Transaction hash once broadcast")
    transaction_url: str | None = Field(
        None, description="Optional transaction URL (explorer link)"
    )

    model_config = ConfigDict(extra="ignore")


class SignAndSendResponse(BaseModel):
    """
    Standard response from sign_and_send operations.

    This response follows the unified SDK response structure with success, data,
    error, and error_details fields.

    Attributes:
        success: Whether the operation was successful
        data: Transaction data (only present on success)
        error: Error message (only present on failure)
        error_details: Detailed error information (only present on failure)

    Example:
        ```python
        response = sdk.sign_and_send({
            "network": "ethereum:1",
            "request": {"toAddress": "0x...", "data": "0x", "value": "0"}
        })
        if response.success and response.data:
            print(f"Transaction hash: {response.data.tx_hash}")
            if response.data.transaction_url:
                print(f"View on explorer: {response.data.transaction_url}")
        else:
            print(f"Transaction failed: {response.error}")
        ```
    """

    success: bool = Field(..., description="Whether the operation was successful")
    data: SignAndSendData | None = Field(
        None, description="Transaction data (only present on success)"
    )
    error: str | None = Field(
        None, description="Error message (only present on failure)"
    )
    error_details: dict | None = Field(
        None, description="Detailed error information (only present on failure)"
    )

    @property
    def error_message(self) -> str | None:
        """Alias for error field to provide consistent API."""
        return self.error

    model_config = ConfigDict(extra="ignore")


class EvmMessageSignData(BaseModel):
    """EVM message signature data."""

    status: int
    v: int
    r: str
    s: str
    formattedSignature: str
    type: Literal["evm"]


class EvmMessageSignResponse(BaseModel):
    """
    Response from EVM message signing operations.

    Attributes:
        success: Whether the operation was successful
        data: Signature data (only present on success)
        error: Error message (only present on failure)
        error_details: Detailed error information (only present on failure)
    """

    success: bool = Field(..., description="Whether the operation was successful")
    data: EvmMessageSignData | None = Field(
        None, description="Signature data (only present on success)"
    )
    error: str | None = Field(
        None, description="Error message (only present on failure)"
    )
    error_details: dict | None = Field(
        None, description="Detailed error information (only present on failure)"
    )

    @property
    def error_message(self) -> str | None:
        """Alias for error field to provide consistent API."""
        return self.error

    model_config = ConfigDict(extra="ignore")


class SwidgeQuoteResponse(BaseModel):
    """
    Swidge quote response wrapper.

    Attributes:
        success: Whether the operation was successful
        data: Swidge data (only present on success)
        error: Error message (only present on failure)
        error_details: Detailed error information (only present on failure)
    """

    success: bool = Field(..., description="Whether the operation was successful")
    data: SwidgeData | None = Field(
        None, description="Swidge data (only present on success)"
    )
    error: str | None = Field(
        None, description="Error message (only present on failure)"
    )
    error_details: dict | None = Field(
        None, description="Detailed error information (only present on failure)"
    )

    @property
    def error_message(self) -> str | None:
        """Alias for error field to provide consistent API."""
        return self.error

    def has_data(self) -> bool:
        """
        Check if the response has data (type-safe data check).

        Returns:
            True if success and data is not None.

        Note:
            Use this helper in combination with explicit None checks for proper type narrowing:
            ```python
            quote = agent.swidge.quote({...})
            if quote.has_data() and quote.data is not None:
                # Type checker now knows quote.data is SwidgeData
                execute = agent.swidge.execute(quote.data)
            ```
        """
        return self.success and self.data is not None

    model_config = ConfigDict(extra="ignore")


class SwidgeExecuteResponse(BaseModel):
    """
    Swidge execute response wrapper.

    Attributes:
        success: Whether the operation was successful
        data: Execute response data (only present on success)
        error: Error message (only present on failure)
        error_details: Detailed error information (only present on failure)
    """

    success: bool = Field(..., description="Whether the operation was successful")
    data: SwidgeExecuteResponseData | None = Field(
        None, description="Execute response data (only present on success)"
    )
    error: str | None = Field(
        None, description="Error message (only present on failure)"
    )
    error_details: dict | None = Field(
        None, description="Detailed error information (only present on failure)"
    )

    @property
    def error_message(self) -> str | None:
        """Alias for error field to provide consistent API."""
        return self.error

    def has_data(self) -> bool:
        """
        Check if the response has data (type-safe data check).

        Returns:
            True if success and data is not None.

        Note:
            Use this helper in combination with explicit None checks for proper type narrowing:
            ```python
            execute = agent.swidge.execute(quote.data)
            if execute.has_data() and execute.data is not None:
                # Type checker now knows execute.data is SwidgeExecuteResponseData
                print(f"Status: {execute.data.status}")
            ```
        """
        return self.success and self.data is not None

    model_config = ConfigDict(extra="ignore")


class UpdateJobStatusResponse(BaseModel):
    """Response from job status update."""

    status: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Response message")

    model_config = ConfigDict(extra="ignore")


class LogResponse(BaseModel):
    """
    Response from agent.log() operations.

    This response is returned after attempting to log a message to the console
    and optionally to the backend.

    Attributes:
        success: Whether the operation was successful
        error: Error message (only present on failure)
        error_details: Detailed error information (only present on failure)

    Example:
        ```python
        response = agent.log("Processing transaction")
        if not response.success:
            print(f"Failed to log: {response.error_message}")
        ```
    """

    success: bool = Field(..., description="Whether the operation was successful")
    error: str | None = Field(
        None, description="Error message (only present on failure)"
    )
    error_details: dict | None = Field(
        None, description="Detailed error information (only present on failure)"
    )

    @property
    def error_message(self) -> str | None:
        """Alias for error field to provide consistent API."""
        return self.error

    model_config = ConfigDict(extra="ignore")


class AssetChange(BaseModel):
    """
    Asset change representing a token transfer in a confirmed transaction.

    Attributes:
        network: Network identifier (e.g., "ethereum:1", "solana")
        transactionHash: Transaction hash
        from_: Sender address (using from_ to avoid Python keyword)
        to: Recipient address
        amount: Amount transferred (as string to preserve precision)
        token: Token contract address (None for native tokens)
        tokenId: Token ID for NFTs (None for fungible tokens)
        tokenType: Token type (e.g., "native", "ERC20", "ERC721")
        tokenUsdPrice: Token price in USD at time of transaction (None if unavailable)
        timestamp: Timestamp of the transaction
    """

    network: str = Field(..., description="Network identifier")
    transactionHash: str = Field(
        ..., description="Transaction hash", alias="transactionHash"
    )
    from_: str = Field(..., description="Sender address", alias="from")
    to: str = Field(..., description="Recipient address")
    amount: str = Field(..., description="Amount transferred (as string)")
    token: str | None = Field(None, description="Token contract address")
    tokenId: str | None = Field(None, description="Token ID for NFTs")
    tokenType: str = Field(..., description="Token type")
    tokenUsdPrice: str | None = Field(None, description="Token price in USD")
    timestamp: str = Field(..., description="Transaction timestamp")

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class TransactionsResponse(BaseModel):
    """
    Response from agent.transactions() operations.

    This response contains all confirmed transaction asset changes for the session.

    Attributes:
        success: Whether the operation was successful
        data: Array of asset changes (only present on success)
        error: Error message (only present on failure)
        error_details: Detailed error information (only present on failure)

    Example:
        ```python
        response = agent.transactions()
        if response.success and response.data:
            print(f"Found {len(response.data)} asset changes")
            for change in response.data:
                print(f"{change.from_} → {change.to}: {change.amount}")
        else:
            print(f"Failed: {response.error}")
        ```
    """

    success: bool = Field(..., description="Whether the operation was successful")
    data: list[AssetChange] | None = Field(
        None, description="Array of asset changes (only present on success)"
    )
    error: str | None = Field(
        None, description="Error message (only present on failure)"
    )
    error_details: dict | None = Field(
        None, description="Detailed error information (only present on failure)"
    )

    @property
    def error_message(self) -> str | None:
        """Alias for error field to provide consistent API."""
        return self.error

    model_config = ConfigDict(extra="ignore")


class PolymarketMetadata(BaseModel):
    """
    Polymarket-specific position metadata.

    Contains detailed market information for ERC1155 Polymarket positions including
    current prices, PNL tracking, and redeemability status.

    Attributes:
        contractAddress: ERC1155 contract address for the market
        tokenId: Token ID for the specific outcome
        decimals: Token decimals (typically 6)
        conditionId: Unique condition identifier
        formattedShares: Human-readable share count
        shares: Raw share count in smallest unit
        valueUsd: Current position value in USD
        question: Market question text
        outcome: Outcome name (e.g., "Yes", "No")
        priceUsd: Current price per share in USD
        averagePriceUsd: Average purchase price per share in USD
        isRedeemable: Whether position can be redeemed
        isNegativeRisk: Whether position uses negative risk collateral
        imageUrl: Market image URL
        initialValue: Initial position value in USD
        pnlUsd: Unrealized profit/loss in USD
        pnlPercent: Unrealized profit/loss percentage
        pnlRealizedUsd: Realized profit/loss in USD
        pnlRealizedPercent: Realized profit/loss percentage
        endDate: Market end date (ISO 8601 string)
    """

    contractAddress: str = Field(..., description="ERC1155 contract address")
    tokenId: str | None = Field(None, description="Token ID for the outcome")
    decimals: int = Field(..., description="Token decimals")
    conditionId: str = Field(..., description="Unique condition identifier")
    formattedShares: str = Field(..., description="Human-readable share count")
    shares: str = Field(..., description="Raw share count in smallest unit")
    valueUsd: str = Field(..., description="Current position value in USD")
    question: str = Field(..., description="Market question text")
    outcome: str = Field(..., description="Outcome name (e.g., 'Yes', 'No')")
    priceUsd: str = Field(..., description="Current price per share in USD")
    averagePriceUsd: str = Field(
        ..., description="Average purchase price per share in USD"
    )
    isRedeemable: bool = Field(..., description="Whether position can be redeemed")
    isNegativeRisk: bool = Field(
        ..., description="Whether position uses negative risk collateral"
    )
    imageUrl: str = Field(..., description="Market image URL")
    initialValue: str = Field(..., description="Initial position value in USD")
    pnlUsd: str = Field(..., description="Unrealized profit/loss in USD")
    pnlPercent: str = Field(..., description="Unrealized profit/loss percentage")
    pnlRealizedUsd: str = Field(..., description="Realized profit/loss in USD")
    pnlRealizedPercent: str = Field(..., description="Realized profit/loss percentage")
    endDate: str = Field(..., description="Market end date (ISO 8601 string)")

    model_config = ConfigDict(extra="ignore")


class EnrichedPosition(BaseModel):
    """
    Current position with optional Polymarket metadata enrichment.

    Represents a position held by the session wallet, with optional detailed
    Polymarket market information for ERC1155 positions.

    Attributes:
        network: Network identifier (e.g., "ethereum:137", "solana")
        assetAddress: Asset contract address
        tokenId: Token ID for NFTs/ERC1155 (None for fungible tokens)
        avgUnitCost: Average unit cost in USD
        currentQty: Current quantity held (raw amount)
        polymarketMetadata: Optional Polymarket metadata (only for ERC1155 positions)
    """

    network: str = Field(..., description="Network identifier")
    assetAddress: str = Field(..., description="Asset contract address")
    tokenId: str | None = Field(
        None, description="Token ID for NFTs/ERC1155 (None for fungible tokens)"
    )
    avgUnitCost: str = Field(..., description="Average unit cost in USD")
    currentQty: str = Field(..., description="Current quantity held (raw amount)")
    polymarketMetadata: PolymarketMetadata | None = Field(
        None, description="Optional Polymarket metadata (only for ERC1155 positions)"
    )

    model_config = ConfigDict(extra="ignore")


class CurrentPositionsData(BaseModel):
    """
    Data returned from get_current_positions() operations.

    Contains the list of current positions and a flag indicating if there are
    pending transactions that may affect balances.

    Attributes:
        positions: Array of current positions with optional Polymarket metadata
        hasPendingTxs: Whether there are pending transactions
    """

    positions: list[EnrichedPosition] = Field(
        ..., description="Array of current positions with optional Polymarket metadata"
    )
    hasPendingTxs: bool = Field(
        ..., description="Whether there are pending transactions"
    )

    model_config = ConfigDict(extra="ignore")


class CurrentPositionsResponse(BaseModel):
    """
    Response from get_current_positions() operations.

    Returns current live positions for the session with optional Polymarket
    metadata enrichment for ERC1155 positions.

    Attributes:
        success: Whether the operation was successful
        data: Current positions data (only present on success)
        error: Error message (only present on failure)
        error_details: Detailed error information (only present on failure)

    Example:
        ```python
        response = sdk.get_current_positions()
        if response.success and response.data:
            print(f"Found {len(response.data.positions)} positions")

            if response.data.hasPendingTxs:
                print("⚠️  Warning: Pending transactions may affect balances")

            for position in response.data.positions:
                print(f"{position.assetAddress}: {position.currentQty} units")
                print(f"  Average cost: ${position.avgUnitCost}")

                # Check for Polymarket enrichment
                if position.polymarketMetadata:
                    pm = position.polymarketMetadata
                    print(f"  📈 {pm.question}")
                    print(f"  Outcome: {pm.outcome}")
                    print(f"  Shares: {pm.formattedShares}")
                    print(f"  Value: ${pm.valueUsd}")
                    print(f"  PNL: ${pm.pnlUsd} ({pm.pnlPercent}%)")
                    print(f"  Redeemable: {'Yes' if pm.isRedeemable else 'No'}")
        else:
            print(f"Failed: {response.error}")
        ```
    """

    success: bool = Field(..., description="Whether the operation was successful")
    data: CurrentPositionsData | None = Field(
        None, description="Current positions data (only present on success)"
    )
    error: str | None = Field(
        None, description="Error message (only present on failure)"
    )
    error_details: dict | None = Field(
        None, description="Detailed error information (only present on failure)"
    )

    @property
    def error_message(self) -> str | None:
        """Alias for error field to provide consistent API."""
        return self.error

    model_config = ConfigDict(extra="ignore")
