"""
Dual WebSocket Example
Demonstrates using separate WebSocket connections for orders and price feed
"""

import asyncio
from acttrader import ActTrader
from acttrader.types import ActTraderConfig


async def main():
    """Dual WebSocket example"""
    # Initialize client with separate WebSocket URLs
    config = ActTraderConfig(
        base_url='http://s20.sysfx.com:10001',
        order_ws_url='ws://s20.sysfx.com:10006/ws',      # Order updates stream
        price_feed_ws_url='wss://eforex20.acttrader.com/charts/ws',  # Price feed stream
        username='T18425',
        password='Test@1234'
    )
    client = ActTrader(config)
    
    try:
        # Authenticate
        await client.auth.get_token(60)
        await client.initialize_symbol_cache()
        
        # Create separate streaming clients
        price_stream = client.stream_price_feed()  # Price feed data
        order_stream = client.stream_orders()      # Order updates
        
        # Order stream handlers
        def on_order_connected(*args):
            print('Order stream connected')
            # asyncio.create_task(order_stream.subscribe(['EURUSD', 'GBPUSD']))
        
        def on_order_event(data):
            print(f'Order event: {data}')
        
        def on_trade_event(data):
            print(f'Trade event: {data}')
        
        def on_account_update(data):
            print(f'Account update: {data}')
        
        # Price feed stream handlers
        def on_price_connected(*args):
            print('Price feed stream connected')
            asyncio.create_task(price_stream.subscribe(['EURUSD', 'GBPUSD', 'USDJPY']))
        
        def on_price_feed(data):
            print(f'Price feed with OHLC: {data}')
        
        def on_ticker(data):
            print(f'Ticker update: {data}')
        
        def on_price_error(error):
            print(f'Price feed error: {error}')
        
        def on_price_disconnected():
            print('Price feed disconnected')
        
        # Register order stream handlers
        order_stream.on('connected', on_order_connected)
        order_stream.on('order', on_order_event)
        order_stream.on('trade', on_trade_event)
        order_stream.on('account', on_account_update)
        
        # Register price feed handlers
        price_stream.on('connected', on_price_connected)
        price_stream.on('pricefeed', on_price_feed)
        price_stream.on('ticker', on_ticker)
        price_stream.on('error', on_price_error)
        price_stream.on('disconnected', on_price_disconnected)
        
        # Connect both streams
        print('Connecting to order stream...')
        print(f'Order stream URL: {order_stream.ws_url}')
        await order_stream.connect()
        
        # Small delay between connections
        await asyncio.sleep(1)
        
        print('Connecting to price feed stream...')
        print(f'Price feed URL: {price_stream.ws_url}')
        print(f'Price feed token: {price_stream.token}')
        try:
            await price_stream.connect()
        except Exception as e:
            print(f'Failed to connect to price feed: {e}')
            print('Continuing with order stream only...')
        
        # Keep running to receive events
        print('Listening for events (60 seconds)...')
        await asyncio.sleep(60)
        
        # Clean up
        print('Disconnecting...')
        await order_stream.disconnect()
        await price_stream.disconnect()
        await client.auth.logout()
        
    except Exception as error:
        print('Error:', error)


if __name__ == '__main__':
    asyncio.run(main())
