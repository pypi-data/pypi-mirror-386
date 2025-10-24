"""
ActTrader Python SDK
Main entry point for the ActTrader SDK
"""

from typing import Optional
from .client import ActTraderClient
from .modules import AuthModule, AccountModule, MarketModule, TradingModule, AlertModule, StreamingClient
from .symbol_cache import SymbolCache
from .types import ActTraderConfig


class ActTrader:
    """
    ActTrader SDK
    Official Python SDK for ActTrader Trading API
    
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
    
    def __init__(self, config: ActTraderConfig):
        """
        Initialize ActTrader SDK
        
        Args:
            config: ActTrader configuration
        """
        self.client = ActTraderClient(config)
        self.symbol_cache = SymbolCache(self._fetch_symbols)
        
        # Initialize modules
        self.auth = AuthModule(self.client)
        self.account = AccountModule(self.client)
        self.market = MarketModule(self.client)
        self.trading = TradingModule(self.client, self.symbol_cache)
        self.alert = AlertModule(self.client)
    
    async def _fetch_symbols(self):
        """Fetch symbols for symbol cache"""
        try:
            # Try detailed symbols first (preferred for symbol cache)
            return await self.market.get_symbols_detailed()
        except Exception:
            # Fallback to basic symbols if detailed endpoint is not available
            return await self.market.get_symbols()
    
    async def initialize_symbol_cache(self) -> None:
        """
        Initialize symbol cache
        Should be called after authentication
        
        Example:
            ```python
            await client.auth.get_token(60)
            await client.initialize_symbol_cache()
            ```
        """
        await self.symbol_cache.initialize()
    
    async def refresh_symbol_cache(self) -> None:
        """
        Manually refresh symbol cache
        
        Example:
            ```python
            await client.refresh_symbol_cache()
            ```
        """
        await self.symbol_cache.refresh()
    
    def get_symbol_cache_stats(self) -> dict:
        """
        Get symbol cache statistics
        
        Returns:
            Cache statistics
        """
        return self.symbol_cache.get_stats()
    
    def get_symbol(self, symbol_name: str):
        """
        Get symbol information from cache
        
        Args:
            symbol_name: Symbol name (e.g., 'EURUSD')
            
        Returns:
            Symbol data or None
        """
        return self.symbol_cache.get_symbol(symbol_name)
    
    def lots_to_quantity(self, symbol_name: str, lots: float) -> float:
        """
        Convert lots to quantity for a symbol
        
        Args:
            symbol_name: Symbol name
            lots: Number of lots
            
        Returns:
            Quantity (lots × contract size)
        """
        return self.symbol_cache.lots_to_quantity(symbol_name, lots)
    
    def set_token(self, token: str) -> None:
        """
        Set authentication token
        
        Args:
            token: Authentication token
            
        Example:
            ```python
            client.set_token('your_token_here')
            ```
        """
        self.client.set_token(token)
    
    def get_token(self) -> Optional[str]:
        """
        Get current authentication token
        
        Returns:
            Current token or None
            
        Example:
            ```python
            token = client.get_token()
            ```
        """
        return self.client.get_token()
    
    def stream(self, token: Optional[str] = None) -> StreamingClient:
        """
        Create a new streaming client for real-time data (legacy method)
        Requires WebSocket URL to be configured
        
        Args:
            token: Optional token override (uses current token if not provided)
            
        Returns:
            StreamingClient instance
            
        Deprecated:
            Use stream_orders() or stream_price_feed() for separate connections
        """
        ws_url = self.client.get_ws_url()
        if not ws_url:
            raise ValueError('WebSocket URL not configured. Provide ws_url in config.')
        
        auth_token = token or self.client.get_token()
        if not auth_token:
            raise ValueError('Authentication token required for streaming. Call auth.get_token() first.')
        
        return StreamingClient(ws_url, auth_token)
    
    def stream_orders(self, token: Optional[str] = None) -> StreamingClient:
        """
        Create a streaming client for order updates
        Handles order events, trade events, account updates, and legacy ticker data
        
        Args:
            token: Optional token override (uses current token if not provided)
            
        Returns:
            StreamingClient instance
            
        Example:
            ```python
            order_stream = client.stream_orders()
            
            await order_stream.connect()
            
            order_stream.on('connected', lambda: print('Connected to order updates stream'))
            order_stream.on('order', lambda data: print('Order event:', data))
            order_stream.on('trade', lambda data: print('Trade event:', data))
            
            await order_stream.subscribe(['EURUSD', 'GBPUSD'])
            ```
        """
        ws_url = self.client.get_order_ws_url() or self.client.get_ws_url()
        if not ws_url:
            raise ValueError('Order WebSocket URL not configured. Provide order_ws_url or ws_url in config.')
        
        auth_token = token or self.client.get_token()
        if not auth_token:
            raise ValueError('Authentication token required for streaming. Call auth.get_token() first.')
        
        return StreamingClient(ws_url, auth_token)
    
    def stream_price_feed(self, token: Optional[str] = None) -> StreamingClient:
        """
        Create a streaming client for price feed data
        Handles price feed messages with OHLC data
        
        Args:
            token: Optional token override (uses current token if not provided)
            
        Returns:
            StreamingClient instance
            
        Example:
            ```python
            price_stream = client.stream_price_feed()
            
            await price_stream.connect()
            
            price_stream.on('connected', lambda: print('Connected to price feed stream'))
            price_stream.on('pricefeed', lambda data: print('Price feed with OHLC:', data))
            
            await price_stream.subscribe(['EURUSD', 'GBPUSD'])
            ```
        """
        ws_url = self.client.get_price_feed_ws_url() or self.client.get_ws_url()
        if not ws_url:
            raise ValueError('Price feed WebSocket URL not configured. Provide price_feed_ws_url or ws_url in config.')
        
        auth_token = ''
        
        print(f'Price feed WebSocket URL: {ws_url}')
        return StreamingClient(ws_url, auth_token)
