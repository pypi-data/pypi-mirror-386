"""
ActTrader Python SDK
Official Python SDK for ActTrader Trading API

This SDK provides a comprehensive interface to interact with ActTrader's REST API 
and WebSocket streaming services.

Features:
- 🔐 Authentication - Digest authentication and token-based session management
- 💰 Account Management - Access account information and manage settings
- 📊 Market Data - Get real-time and historical market data, symbols, and instruments
- 📈 Trading Operations - Place, modify, and cancel orders; manage positions
- 🎯 Lots-Based Trading - Trade with lots (auto-converts to quantity using contract size)
- 💾 Symbol Cache - Auto-refreshing symbol cache (24-hour intervals)
- 🔔 Alerts - Create and manage price alerts (deprecated)
- 🌊 WebSocket Streaming - Real-time market data and trading events
- 📘 Type Hints - Full Python type hints included
- ⚡ Async Support - Modern async/await API

Example:
    ```python
    from acttrader import ActTrader
    
    # Initialize with username and password for digest auth
    client = ActTrader(
        base_url='http://rest-api.sysfx.com:18001',
        ws_url='ws://stream.sysfx.com:18002',
        username='your_username',
        password='your_password'
    )
    
    # Or initialize with existing token
    client = ActTrader(
        base_url='http://rest-api.sysfx.com:18001',
        token='your_token'
    )
    ```
"""

from .client import ActTraderClient
from .main import ActTrader
from .types import (
    ActTraderConfig,
    ApiResponse,
    Account,
    Symbol,
    Order,
    Trade,
    OrderSide,
    OrderType,
    TokenResponse,
    Instrument,
    Symbol2,
    PriceShift,
    OrderResponse,
    RemovedOrder,
    Alert,
    AlertResponse,
    PlaceMarketOrderParams,
    PlacePendingOrderParams,
    PlaceStopLimitParams,
    PlaceTrailParams,
    TradeHistoryParams,
    RemovedOrdersParams,
    WSEventType,
    WSMessage,
    TickerPayload,
    PriceFeedMessage,
    PriceFeedData,
    OrderBookEntry,
    OrderBookPayload,
    OrderWSPayload,
    AccountWSPayload,
    TradeWSPayload,
    AlertWSPayload,
    EquityWarningPayload,
)

# Version
__version__ = "1.0.1"
__author__ = "Act"
__email__ = "support@acttrader.com"

# Main exports
__all__ = [
    "ActTrader",
    "ActTraderClient",
    "ActTraderConfig",
    "ApiResponse",
    "Account",
    "Symbol",
    "Order",
    "Trade",
    "OrderSide",
    "OrderType",
    "TokenResponse",
    "Instrument",
    "Symbol2",
    "PriceShift",
    "OrderResponse",
    "RemovedOrder",
    "Alert",
    "AlertResponse",
    "PlaceMarketOrderParams",
    "PlacePendingOrderParams",
    "PlaceStopLimitParams",
    "PlaceTrailParams",
    "TradeHistoryParams",
    "RemovedOrdersParams",
    "WSEventType",
    "WSMessage",
    "TickerPayload",
    "PriceFeedMessage",
    "PriceFeedData",
    "OrderBookEntry",
    "OrderBookPayload",
    "OrderWSPayload",
    "AccountWSPayload",
    "TradeWSPayload",
    "AlertWSPayload",
    "EquityWarningPayload",
]
