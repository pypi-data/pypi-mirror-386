"""
Symbol Cache for ActTrader SDK
Auto-refreshing symbol cache with 24-hour intervals
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from .types import Symbol2, Symbol


class SymbolCache:
    """Auto-refreshing symbol cache"""
    
    def __init__(self, fetch_function: Callable[[], Any]):
        """
        Initialize symbol cache
        
        Args:
            fetch_function: Async function to fetch symbols
        """
        self.fetch_function = fetch_function
        self.symbols: Dict[str, Any] = {}
        self.last_update: Optional[datetime] = None
        self.refresh_interval = timedelta(hours=24)
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the cache by fetching symbols"""
        async with self._lock:
            await self._fetch_and_update()
    
    async def refresh(self) -> None:
        """Manually refresh the cache"""
        async with self._lock:
            await self._fetch_and_update()
    
    async def _fetch_and_update(self) -> None:
        """Fetch symbols and update cache"""
        try:
            result = await self.fetch_function()
            if result.success and result.result:
                # Convert list to dict for faster lookup
                # Handle both Symbol and Symbol2 types
                symbol_dict = {}
                for symbol in result.result:
                    # Get symbol name (different field names in Symbol vs Symbol2)
                    # Handle both dict and object formats
                    if isinstance(symbol, dict):
                        symbol_name = symbol.get('Pair label') or symbol.get('Symbol')
                    else:
                        symbol_name = getattr(symbol, 'Pair_label', None) or getattr(symbol, 'Symbol', None)
                    
                    if symbol_name:
                        symbol_dict[symbol_name] = symbol
                
                self.symbols = symbol_dict
                self.last_update = datetime.now()
        except Exception as e:
            print(f"Warning: Failed to refresh symbol cache: {e}")
    
    def get_symbol(self, symbol_name: str) -> Optional[Any]:
        """
        Get symbol information from cache
        
        Args:
            symbol_name: Symbol name (e.g., 'EURUSD')
            
        Returns:
            Symbol data or None
        """
        return self.symbols.get(symbol_name)
    
    def lots_to_quantity(self, symbol_name: str, lots: float) -> float:
        """
        Convert lots to quantity for a symbol
        
        Args:
            symbol_name: Symbol name
            lots: Number of lots
            
        Returns:
            Quantity (lots × contract size)
            
        Raises:
            ValueError: If symbol not found in cache
        """
        symbol = self.get_symbol(symbol_name)
        if not symbol:
            raise ValueError(f"Symbol '{symbol_name}' not found in cache. Call initialize_symbol_cache() first.")
        
        # Get contract size (different field names in Symbol vs Symbol2)
        # Handle both dict and object formats
        if isinstance(symbol, dict):
            contract_size = symbol.get('Contract size') or symbol.get('ContractSize')
        else:
            contract_size = getattr(symbol, 'Contract_size', None) or getattr(symbol, 'ContractSize', None)
        
        if contract_size is None:
            raise ValueError(f"Contract size not available for symbol '{symbol_name}'")
        
        return lots * contract_size
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Cache statistics
        """
        hours_since_update = None
        if self.last_update:
            hours_since_update = (datetime.now() - self.last_update).total_seconds() / 3600
        
        return {
            'symbol_count': len(self.symbols),
            'last_update': self.last_update,
            'hours_since_update': hours_since_update
        }
    
    async def auto_refresh_if_needed(self) -> None:
        """Auto-refresh cache if it's older than the refresh interval"""
        if not self.last_update or datetime.now() - self.last_update > self.refresh_interval:
            await self.refresh()
