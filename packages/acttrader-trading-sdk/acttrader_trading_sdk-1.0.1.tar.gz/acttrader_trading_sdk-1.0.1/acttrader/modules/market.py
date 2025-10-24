"""
Market data module
Handles market data, symbols, instruments, and price information
"""

from typing import Optional, List
from ..client import ActTraderClient
from ..types import ApiResponse, Instrument, Symbol, Symbol2, PriceShift


class MarketModule:
    """Market data module for ActTrader API"""
    
    def __init__(self, client: ActTraderClient):
        """
        Initialize market module
        
        Args:
            client: ActTrader HTTP client
        """
        self.client = client
    
    async def get_instruments(self, active: str = 'Y', token: Optional[str] = None) -> ApiResponse[List[Instrument]]:
        """
        Get all active instruments
        
        Args:
            active: Filter for active instruments ('Y' or 'N')
            token: Optional authentication token
            
        Returns:
            Array of instruments
            
        Example:
            ```python
            result = await client.market.get_instruments('Y')
            instruments = result.result
            
            for instrument in instruments:
                print(f"{instrument.Name} ({instrument.Type})")
            ```
        """
        params = {'active': active}
        if token is not None:
            params['token'] = token
        return await self.client.get('/api/v2/market/instruments', params)
    
    async def get_symbols(self, token: Optional[str] = None) -> ApiResponse[List[Symbol]]:
        """
        Get trading symbols with current prices
        
        Args:
            token: Optional authentication token
            
        Returns:
            Array of symbols with current prices
            
        Example:
            ```python
            result = await client.market.get_symbols()
            symbols = result.result
            
            for symbol in symbols:
                print(f"{symbol.Symbol}: Bid {symbol.Sell}, Ask {symbol.Buy}")
            ```
        """
        params = {}
        if token is not None:
            params['token'] = token
        return await self.client.get('/api/v2/market/symbols', params)
    
    async def get_symbols_detailed(self, token: Optional[str] = None) -> ApiResponse[List[Symbol2]]:
        """
        Get symbols with detailed information (margin, commission, etc.)
        
        Args:
            token: Optional authentication token
            
        Returns:
            Array of detailed symbol information
            
        Example:
            ```python
            result = await client.market.get_symbols_detailed()
            details = result.result
            
            for detail in details:
                print(f"{detail.Pair_label}:")
                print(f"  Contract Size: {detail.Contract_size}")
                print(f"  Min Volume: {detail.Min_volume}")
                print(f"  Margin Rate: {detail.Margin_settings.Rate}%")
            ```
        """
        params = {}
        if token is not None:
            params['token'] = token
        return await self.client.get('/api/v2/market/symbols2', params)
    
    async def get_shifts(self, token: Optional[str] = None) -> ApiResponse[List[PriceShift]]:
        """
        Get price shifts for instruments
        
        Args:
            token: Optional authentication token
            
        Returns:
            Array of price shifts
            
        Example:
            ```python
            result = await client.market.get_shifts()
            shifts = result.result
            ```
        """
        params = {}
        if token is not None:
            params['token'] = token
        return await self.client.get('/api/v2/market/shifts', params)
