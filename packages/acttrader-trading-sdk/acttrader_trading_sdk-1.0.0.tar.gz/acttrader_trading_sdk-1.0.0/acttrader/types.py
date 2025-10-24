"""
ActTrader SDK Type Definitions
All dates are in Eastern Time (EST/EDT)
"""

from typing import Dict, List, Optional, Union, Literal, Any, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar('T')


class ActTraderConfig(BaseModel):
    """Configuration for ActTrader client"""
    base_url: str
    ws_url: Optional[str] = None  # Legacy: single WebSocket URL
    order_ws_url: Optional[str] = None  # WebSocket URL for order updates
    price_feed_ws_url: Optional[str] = None  # WebSocket URL for price feed
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response format"""
    success: bool
    message: Optional[str] = None
    result: Optional[T] = None


# Account Types
class Account(BaseModel):
    """Account information"""
    AccountID: int
    Balance: float
    TraderID: int
    Currency: str
    UsedMargin: float
    Reserved: float


# Auth Types
class TokenResponse(BaseModel):
    """Authentication token response"""
    token: str


# Market Types
class Instrument(BaseModel):
    """Trading instrument"""
    id: int
    Name: str
    Type: str
    Active: Literal['Y', 'N']


class Symbol(BaseModel):
    """Trading symbol with current prices"""
    Symbol: str
    BaseCurrency: str
    QuoteCurrency: str
    Description: str
    Active: Literal['Y', 'N']
    MinTradeSize: float
    Precision: int
    ContractSize: float
    Buy: float
    Sell: float
    PriceDate: str
    Group: str
    Type: str


class MarginSettings(BaseModel):
    """Margin settings for a symbol"""
    Type: str
    Rate: float
    Discount_coeff: float
    Lots_limit_1: float
    Coeff_1: float
    Lots_limit_2: float
    Coeff_2: float


class TradingPause(BaseModel):
    """Trading pause configuration"""
    Week_day: str
    Pause_begin: str
    Pause_end: str
    Timezone: str


class Commission(BaseModel):
    """Commission settings"""
    Type: str
    Value: float


class Symbol2(BaseModel):
    """Detailed symbol information"""
    Pair_label: str
    Description: str
    Base_currency: str
    Quote_currency: str
    Instrument_type: str
    Group_name: str
    Contract_size: float
    Min_volume: float
    Max_volume: float
    Point_size: float
    Price_format: int
    Spread: str
    Condition_distance: float
    Buy_Shift: float
    Sell_Shift: float
    Margin_settings: MarginSettings
    Overnight_rollover_type: str
    Overnight_rollover_sell: float
    Overnight_rollover_buy: float
    Execution: str
    GTC_mode: str
    Filling: str
    Trading_pause: List[TradingPause]
    Commission: Commission


class PriceShift(BaseModel):
    """Price shift information"""
    Pair_label: str
    Base_currency: str
    Quote_currency: str
    Condition_distance: float
    Buy_Shift: float
    Sell_Shift: float


# Trading Types
OrderSide = Literal[0, 1]  # 0 = sell, 1 = buy
OrderType = Literal['I', 'C', 'EL', 'ES', 'S', 'L', 'M']
# I=initial, C=closing, EL/ES=entry limit/stop, S=stop, L=limit, M=margin call


class Order(BaseModel):
    """Trading order"""
    OrderID: int
    Symbol: str
    AccountID: int
    Quantity: float
    Price: float
    Type: OrderType
    Pending: Literal['Y', 'N']
    Side: OrderSide
    ToClose: Optional[float] = None
    Trail: Optional[float] = None
    Commentary: Optional[str] = None
    OpenTime: str


class Trade(BaseModel):
    """Trading position/trade"""
    TradeID: int
    Symbol: str
    AccountID: int
    Quantity: float
    Price: float
    Side: OrderSide
    Commission: Optional[float] = None
    Interest: Optional[float] = None
    Commentary: Optional[str] = None
    OpenTime: str
    CloseTime: Optional[str] = None
    OpenPrice: Optional[float] = None
    ClosePrice: Optional[float] = None
    ProfitLoss: Optional[float] = None
    OpenBalance: Optional[float] = None
    OpenUsedMargn: Optional[float] = None
    OpenEquity: Optional[float] = None
    CloseBalance: Optional[float] = None
    CloseUsedMargn: Optional[float] = None
    CloseEquity: Optional[float] = None
    CloseOrderType: Optional[str] = None


class OrderResponse(BaseModel):
    """Order creation response"""
    OrderID: int


class RemovedOrder(BaseModel):
    """Removed order information"""
    OrderID: int
    Symbol: str
    AccountID: int
    Quantity: float
    Side: OrderSide
    Type: OrderType
    RemoveTime: str
    Commentary: Optional[str] = None
    RemovedBy: str


# Alert Types (deprecated)
class Alert(BaseModel):
    """Price alert"""
    AlertID: int
    Symbol: str
    Price: float
    Type: Literal['BID', 'ASK']
    Commentary: Optional[str] = None
    Triggered: Optional[str] = None


class AlertResponse(BaseModel):
    """Alert creation response"""
    AlertID: int


# WebSocket Types
WSEventType = Literal[
    'ticker', 'orderbook', 'order', 'account', 'trade', 
    'alert', 'equity_warning', 'pricefeed'
]


class WSMessage(BaseModel):
    """WebSocket message wrapper"""
    event: WSEventType
    payload: Any


class TickerPayload(BaseModel):
    """Ticker price data"""
    m: str  # market symbol
    time: str
    bid: float
    ask: float


# Price Feed Types (new format)
class PriceFeedData(BaseModel):
    """Price feed data with OHLC"""
    m: str  # market symbol (e.g., "EURUSD")
    time: str  # ISO timestamp
    bid: float
    ask: float
    day_open: float
    day_high: float
    day_low: float


class PriceFeedMessage(BaseModel):
    """Price feed message"""
    m: str  # message type (e.g., "ticker")
    d: List[PriceFeedData]


class OrderBookEntry(BaseModel):
    """Order book entry"""
    Quantity: str
    Rate: str


class OrderBookPayload(BaseModel):
    """Order book data"""
    m: str
    buy: List[OrderBookEntry]
    sell: List[OrderBookEntry]


class OrderWSPayload(BaseModel):
    """Order WebSocket payload"""
    AccountID: Optional[int] = None
    Action: Literal['I', 'U', 'D']  # Insert, Update, Delete
    OpenTime: Optional[str] = None
    OrderID: int
    Pending: Optional[Literal['Y', 'N']] = None
    Price: Optional[float] = None
    Quantity: Optional[float] = None
    Side: Optional[OrderSide] = None
    Symbol: Optional[str] = None
    TradeID: Optional[int] = None
    Type: Optional[OrderType] = None
    ToClose: Optional[float] = None
    Trail: Optional[float] = None
    Commentary: Optional[str] = None


class AccountWSPayload(BaseModel):
    """Account WebSocket payload"""
    AccountID: int
    Action: Literal['I', 'U', 'D']
    Balance: Optional[float] = None
    Income: Optional[float] = None
    TraderID: int
    Type: Optional[str] = None
    UsedMargin: Optional[float] = None


class TradeWSPayload(BaseModel):
    """Trade WebSocket payload"""
    AccountID: Optional[int] = None
    Action: Literal['I', 'U', 'D']
    CloseOrderID: Optional[int] = None
    CloseTime: Optional[str] = None
    OpenOrderID: Optional[int] = None
    OpenTime: Optional[str] = None
    Price: float
    ProfitLoss: Optional[float] = None
    Quantity: float
    Side: Optional[OrderSide] = None
    Symbol: Optional[str] = None
    TradeID: int
    Commentary: Optional[str] = None
    OpenOrderType: Optional[str] = None
    CloseOrderType: Optional[str] = None


class AlertWSPayload(BaseModel):
    """Alert WebSocket payload"""
    AccountID: int
    AlertID: int
    Commentary: Optional[str] = None
    Price: float
    Symbol: str
    Triggered: str
    Type: Literal['BID', 'ASK']


class EquityWarningPayload(BaseModel):
    """Equity warning WebSocket payload"""
    AccountID: int
    Equity: float
    EquityNotificationPercentLevel: float
    UsedMargin: float


# Query Parameter Types
class PlaceMarketOrderParams(BaseModel):
    """Market order parameters"""
    token: str
    symbol: str
    quantity: Optional[float] = None  # Either quantity or lots must be provided
    lots: Optional[float] = None  # Will be converted to quantity using contract size
    side: OrderSide
    account: int
    stop: Optional[float] = None
    limit: Optional[float] = None
    trail: Optional[float] = None
    commentary: Optional[str] = None


class PlacePendingOrderParams(BaseModel):
    """Pending order parameters"""
    token: str
    symbol: str
    quantity: Optional[float] = None  # Either quantity or lots must be provided
    lots: Optional[float] = None  # Will be converted to quantity using contract size
    side: OrderSide
    account: int
    price: float
    stop: Optional[float] = None
    limit: Optional[float] = None
    trail: Optional[float] = None
    commentary: Optional[str] = None


class PlaceStopLimitParams(BaseModel):
    """Stop/limit order parameters"""
    token: str
    trade: Optional[int] = None
    order: Optional[int] = None
    price: Optional[float] = None
    pips: Optional[float] = None


class PlaceTrailParams(BaseModel):
    """Trailing stop parameters"""
    token: str
    trade: Optional[int] = None
    order: Optional[int] = None
    trail: float


class TradeHistoryParams(BaseModel):
    """Trade history query parameters"""
    token: str
    from_date: Optional[str] = None
    till: Optional[str] = None
    account: Optional[int] = None
    tradeId: Optional[int] = None


class RemovedOrdersParams(BaseModel):
    """Removed orders query parameters"""
    token: str
    from_date: Optional[str] = None
    till: Optional[str] = None
    order: Optional[int] = None
    account: Optional[int] = None
