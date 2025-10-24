"""
WebSocket streaming module
Handles real-time market data and trading events via WebSocket
"""

import asyncio
import json
import websockets
from typing import Dict, List, Optional, Callable, Any
from ..types import (
    WSEventType, WSMessage, TickerPayload, PriceFeedMessage, PriceFeedData,
    OrderBookPayload, OrderWSPayload, AccountWSPayload, TradeWSPayload,
    AlertWSPayload, EquityWarningPayload
)


class StreamingClient:
    """WebSocket streaming client for real-time data"""
    
    def __init__(self, ws_url: str, token: str):
        """
        Initialize streaming client
        
        Args:
            ws_url: WebSocket URL
            token: Authentication token
        """
        self.ws_url = ws_url
        self.token = token
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.subscribed_symbols: List[str] = []
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.connected = False
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._reconnect_delay = 5  # seconds
    
    def on(self, event: WSEventType, handler: Callable) -> None:
        """
        Register event handler
        
        Args:
            event: Event type to listen for
            handler: Handler function
        """
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)
    
    def off(self, event: WSEventType, handler: Optional[Callable] = None) -> None:
        """
        Unregister event handler
        
        Args:
            event: Event type
            handler: Specific handler to remove (if None, removes all)
        """
        if event in self.event_handlers:
            if handler:
                if handler in self.event_handlers[event]:
                    self.event_handlers[event].remove(handler)
            else:
                self.event_handlers[event].clear()
    
    async def connect(self) -> None:
        """
        Connect to WebSocket
        
        Example:
            ```python
            stream = client.stream_orders()
            await stream.connect()
            ```
        """
        try:
            # Build connection URL with token
            if 'eforex20.acttrader.com' in self.ws_url:
                # Price feed WebSocket - no authentication needed
                print('Using price feed connection method (no auth)')
                connection_url = self.ws_url
            elif self.token:
                # Order WebSocket - uses token authentication
                print('Using order stream connection method (with auth)')
                connection_url = f"{self.ws_url}?token={self.token}"
            else:
                connection_url = self.ws_url
                
            print(f'Connecting to WebSocket: {connection_url}')
            self.websocket = await websockets.connect(connection_url)
            
            self.connected = True
            self._reconnect_attempts = 0
            
            # Emit connected event
            await self._emit_event('connected', None)
            
            # Start listening for messages in background
            asyncio.create_task(self._listen())
            
        except Exception as e:
            await self._emit_event('error', e)
            await self._handle_reconnect()
    
    async def disconnect(self) -> None:
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.connected = False
            await self._emit_event('disconnected', None)
    
    async def subscribe(self, symbols: List[str]) -> None:
        """
        Subscribe to symbols
        
        Args:
            symbols: List of symbols to subscribe to
            
        Example:
            ```python
            await stream.subscribe(['EURUSD', 'GBPUSD'])
            ```
        """
        self.subscribed_symbols.extend(symbols)
        
        if self.connected and self.websocket:
            message = {
                'm': 'subscribe',
                'p': symbols
            }
            print(f'Subscribing to symbols: {message}')
            await self.websocket.send(json.dumps(message))
    
    async def unsubscribe(self, symbols: List[str]) -> None:
        """
        Unsubscribe from symbols
        
        Args:
            symbols: List of symbols to unsubscribe from
            
        Example:
            ```python
            await stream.unsubscribe(['USDJPY'])
            ```
        """
        for symbol in symbols:
            if symbol in self.subscribed_symbols:
                self.subscribed_symbols.remove(symbol)
        
        if self.connected and self.websocket:
            message = {
                'm': 'unsubscribe',
                'p': symbols
            }
            await self.websocket.send(json.dumps(message))
    
    async def _listen(self) -> None:
        """Listen for WebSocket messages"""
        try:
            async for message in self.websocket:
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            await self._emit_event('disconnected', None)
            await self._handle_reconnect()
        except Exception as e:
            await self._emit_event('error', e)
    
    async def _handle_message(self, message: str) -> None:
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            
            # Handle different message types
            if 'event' in data:
                # Legacy format
                event_type = data['event']
                payload = data.get('payload', [])
                await self._emit_event(event_type, payload)
            elif 'm' in data and 'd' in data:
                # Price feed format
                await self._emit_event('pricefeed', data)
            else:
                # Handle other message formats
                await self._emit_event('message', data)
                
        except json.JSONDecodeError:
            await self._emit_event('error', f"Invalid JSON message: {message}")
        except Exception as e:
            await self._emit_event('error', e)
    
    async def _emit_event(self, event: str, data: Any) -> None:
        """Emit event to registered handlers"""
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    print(f"Error in event handler for {event}: {e}")
    
    async def _handle_reconnect(self) -> None:
        """Handle automatic reconnection"""
        if self._reconnect_attempts < self._max_reconnect_attempts:
            self._reconnect_attempts += 1
            await asyncio.sleep(self._reconnect_delay)
            await self.connect()
        else:
            await self._emit_event('error', "Max reconnection attempts reached")
