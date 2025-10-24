"""
Trading module
Handles all trading operations: orders, positions, trade history
"""

from typing import Optional, List, Dict, Any
from ..client import ActTraderClient
from ..symbol_cache import SymbolCache
from ..types import (
    ApiResponse, Order, Trade, OrderResponse, RemovedOrder, OrderSide,
    PlaceMarketOrderParams, PlacePendingOrderParams, PlaceStopLimitParams,
    PlaceTrailParams, TradeHistoryParams, RemovedOrdersParams
)


class TradingModule:
    """Trading module for ActTrader API"""
    
    def __init__(self, client: ActTraderClient, symbol_cache: SymbolCache):
        """
        Initialize trading module
        
        Args:
            client: ActTrader HTTP client
            symbol_cache: Symbol cache for lots conversion
        """
        self.client = client
        self.symbol_cache = symbol_cache
    
    async def get_open_orders(self, token: Optional[str] = None) -> ApiResponse[List[Order]]:
        """
        Get all open orders
        
        Args:
            token: Optional authentication token
            
        Returns:
            Array of open orders
            
        Example:
            ```python
            result = await client.trading.get_open_orders()
            orders = result.result
            ```
        """
        params = {}
        if token is not None:
            params['token'] = token
        return await self.client.get('/api/v2/trading/openorders', params)
    
    async def get_open_trades(self, token: Optional[str] = None) -> ApiResponse[List[Trade]]:
        """
        Get all open trades/positions
        
        Args:
            token: Optional authentication token
            
        Returns:
            Array of open trades
            
        Example:
            ```python
            result = await client.trading.get_open_trades()
            trades = result.result
            ```
        """
        params = {}
        if token is not None:
            params['token'] = token
        return await self.client.get('/api/v2/trading/opentrades', params)
    
    async def place_market_order(self, params: Dict[str, Any]) -> ApiResponse[OrderResponse]:
        """
        Place a market order
        
        Args:
            params: Market order parameters (use either quantity or lots)
            
        Returns:
            Order response with OrderID
            
        Example:
            ```python
            # Using quantity
            result = await client.trading.place_market_order({
                'symbol': 'EURUSD',
                'quantity': 100000,  # Direct quantity
                'side': 1,
                'account': 100
            })
            
            # Using lots (automatically converted to quantity)
            result2 = await client.trading.place_market_order({
                'symbol': 'EURUSD',
                'lots': 1.0,  # 1 lot = quantity based on contract size
                'side': 1,
                'account': 100,
                'stop': 1.1234,  # Optional
                'limit': 1.234,   # Optional
                'trail': 10      # Optional
            })
            ```
        """
        # Convert lots to quantity if lots is provided
        processed_params = self._process_order_params(params)
        
        # Filter out None values
        clean_params = {k: v for k, v in processed_params.items() if v is not None}
        
        return await self.client.get('/api/v2/trading/placemarket', clean_params)
    
    async def place_pending_order(self, params: Dict[str, Any]) -> ApiResponse[OrderResponse]:
        """
        Place a pending order (Entry Limit or Entry Stop)
        
        Args:
            params: Pending order parameters (use either quantity or lots)
            
        Returns:
            Order response with OrderID
            
        Example:
            ```python
            # Using lots
            result = await client.trading.place_pending_order({
                'symbol': 'EURUSD',
                'lots': 0.5,  # 0.5 lots
                'side': 0,
                'account': 100,
                'price': 1.0099,
                'stop': 1.123,    # Optional
                'limit': 1.124    # Optional
            })
            ```
        """
        # Convert lots to quantity if lots is provided
        processed_params = self._process_order_params(params)
        
        # Filter out None values
        clean_params = {k: v for k, v in processed_params.items() if v is not None}
        
        return await self.client.get('/api/v2/trading/placepending', clean_params)
    
    def _process_order_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process order parameters - convert lots to quantity if needed
        
        Args:
            params: Order parameters
            
        Returns:
            Processed parameters
            
        Raises:
            ValueError: If validation fails
        """
        lots = params.get('lots')
        quantity = params.get('quantity')
        symbol = params.get('symbol')
        
        # Validate: must have either lots or quantity
        if not lots and not quantity:
            raise ValueError('Either "lots" or "quantity" must be provided')
        
        # Validate: cannot have both
        if lots and quantity:
            raise ValueError('Cannot provide both "lots" and "quantity". Use one or the other.')
        
        # If lots provided, convert to quantity
        if lots:
            calculated_quantity = self.symbol_cache.lots_to_quantity(symbol, lots)
            return {
                **params,
                'quantity': calculated_quantity,
                'lots': None  # Remove lots from params
            }
        
        # Otherwise use quantity as-is
        return params
    
    async def place_stop(self, params: Dict[str, Any]) -> ApiResponse[OrderResponse]:
        """
        Place a stop order on an existing trade or pending order
        
        Args:
            params: Stop order parameters
            
        Returns:
            Order response with OrderID
            
        Example:
            ```python
            # Place stop on a trade
            await client.trading.place_stop({
                'trade': 123123,
                'price': 1.0099
            })
            
            # Place stop on a pending order
            await client.trading.place_stop({
                'order': 122344,
                'pips': 50
            })
            ```
        """
        return await self.client.get('/api/v2/trading/placestop', params)
    
    async def place_limit(self, params: Dict[str, Any]) -> ApiResponse[OrderResponse]:
        """
        Place a limit order on an existing trade or pending order
        
        Args:
            params: Limit order parameters
            
        Returns:
            Order response with OrderID
            
        Example:
            ```python
            # Place limit on a trade
            await client.trading.place_limit({
                'trade': 123123,
                'price': 1.0099
            })
            
            # Place limit on a pending order using pips
            await client.trading.place_limit({
                'order': 122344,
                'pips': 50
            })
            ```
        """
        return await self.client.get('/api/v2/trading/placelimit', params)
    
    async def place_trail(self, params: Dict[str, Any]) -> ApiResponse[OrderResponse]:
        """
        Place a trailing stop on an existing trade or pending order
        
        Args:
            params: Trail parameters
            
        Returns:
            Order response with OrderID
            
        Example:
            ```python
            # Place trailing stop on a trade
            await client.trading.place_trail({
                'trade': 123123,
                'trail': 10 # 10 pips
            })
            
            # Place trailing stop on a pending order
            await client.trading.place_trail({
                'order': 122344,
                'trail': 15
            })
            ```
        """
        return await self.client.get('/api/v2/trading/placetrail', params)
    
    async def modify_order(self, order_id: int, price: Optional[float] = None, 
                          quantity: Optional[float] = None, token: Optional[str] = None) -> ApiResponse[None]:
        """
        Modify an existing order
        
        Args:
            order_id: Order ID to modify
            price: New order price
            quantity: New order quantity
            token: Optional authentication token
            
        Returns:
            Success response
            
        Example:
            ```python
            await client.trading.modify_order(247668792, 1.008, 10)
            ```
        """
        return await self.client.get('/api/v2/trading/modifyorder', {
            'order': order_id,
            'price': price,
            'quantity': quantity,
            'token': token
        })
    
    async def cancel_order(self, order_id: int, token: Optional[str] = None) -> ApiResponse[None]:
        """
        Cancel an order
        
        Args:
            order_id: Order ID to cancel
            token: Optional authentication token
            
        Returns:
            Success response
            
        Example:
            ```python
            await client.trading.cancel_order(247574778)
            ```
        """
        return await self.client.get('/api/v2/trading/cancelorder', {
            'order': order_id,
            'token': token
        })
    
    async def close_trade(self, trade_id: int, quantity: float, hedge: str = 'N', 
                        token: Optional[str] = None) -> ApiResponse[OrderResponse]:
        """
        Close an open trade
        
        Args:
            trade_id: Trade ID to close
            quantity: Quantity to close
            hedge: Close with hedge (Y/N), default N
            token: Optional authentication token
            
        Returns:
            Order response with closing OrderID
            
        Example:
            ```python
            result = await client.trading.close_trade(247568770, 100)
            print(result.result.OrderID)
            ```
        """
        return await self.client.get('/api/v2/trading/closetrade', {
            'trade': trade_id,
            'quantity': quantity,
            'hedge': hedge,
            'token': token
        })
    
    async def hedge_trade(self, trade_id: int, quantity: float, 
                         token: Optional[str] = None) -> ApiResponse[OrderResponse]:
        """
        Hedge an open position
        
        Args:
            trade_id: Trade ID to hedge
            quantity: Quantity to hedge
            token: Optional authentication token
            
        Returns:
            Order response with hedging OrderID
            
        Example:
            ```python
            result = await client.trading.hedge_trade(247568770, 100)
            print(result.result.OrderID)
            ```
        """
        return await self.client.get('/api/v2/trading/hedgetrade', {
            'trade': trade_id,
            'quantity': quantity,
            'token': token
        })
    
    async def get_trade_history(self, params: Optional[Dict[str, Any]] = None) -> ApiResponse[List[Trade]]:
        """
        Get trading history
        
        Args:
            params: Query parameters for trade history
            
        Returns:
            Array of historical trades
            
        Example:
            ```python
            result = await client.trading.get_trade_history({
                'from_date': '2021-04-01T00:00',
                'till': '2021-04-02T00:00',
                'account': 1231
            })
            history = result.result
            ```
        """
        return await self.client.get('/api/v2/trading/tradehistory', params)
    
    async def get_removed_orders(self, params: Optional[Dict[str, Any]] = None) -> ApiResponse[List[RemovedOrder]]:
        """
        Get removed orders history
        
        Args:
            params: Query parameters for removed orders
            
        Returns:
            Array of removed orders
            
        Example:
            ```python
            result = await client.trading.get_removed_orders({
                'from_date': '2021-04-01T00:00',
                'till': '2021-07-01T00:00',
                'account': 1001
            })
            removed_orders = result.result
            ```
        """
        return await self.client.get('/api/v2/trading/removedorders', params)
