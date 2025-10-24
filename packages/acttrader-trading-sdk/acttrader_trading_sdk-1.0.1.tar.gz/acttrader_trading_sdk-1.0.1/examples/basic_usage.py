"""
Basic Usage Example
Demonstrates basic ActTrader SDK usage
"""

import asyncio
from acttrader import ActTrader


async def main():
    """Basic usage example"""
    # Initialize client
    client = ActTrader(
        base_url='http://s20.sysfx.com:10001',
        ws_url='wss://eforex20.acttrader.com/charts/ws',
        username='T18425',
        password='Test@1234'
    )
    
    try:
        # Get authentication token
        token_result = await client.auth.get_token(60)
        print('Authenticated with token:', token_result.result)
        
        # Initialize symbol cache (required for lots-based trading)
        await client.initialize_symbol_cache()
        print('Symbol cache initialized')
        
        # Get accounts
        accounts_result = await client.account.get_accounts()
        accounts = accounts_result.result
        print(f'Found {len(accounts)} accounts')
        
        # Get market symbols
        symbols_result = await client.market.get_symbols()
        symbols = symbols_result.result
        print(f'Available symbols: {len(symbols)}')
        
        # Place a market order using LOTS (recommended)
        if accounts:
            order_result = await client.trading.place_market_order({
                'symbol': 'EURUSD',
                'lots': 0.1,       # 0.1 lots (auto-converted to quantity)
                'side': 1,         # Buy
                'account': accounts[0].AccountID,
                'stop': 1.0800,    # Stop loss
                'limit': 1.1200,   # Take profit
                'commentary': 'Test order'
            })
            print('Order placed:', order_result.result.OrderID)
        
        # Get open trades
        trades_result = await client.trading.get_open_trades()
        print('Open trades:', len(trades_result.result))
        
        # Start streaming
        stream = client.stream()
        
        def on_connected():
            print('Streaming connected')
            asyncio.create_task(stream.subscribe(['EURUSD', 'GBPUSD']))
        
        def on_ticker(data):
            print('Price update:', data)
        
        stream.on('connected', on_connected)
        stream.on('ticker', on_ticker)
        
        await stream.connect()
        
        # Keep running for a while
        await asyncio.sleep(10)
        
        await stream.disconnect()
        await client.auth.logout()
        
    except Exception as error:
        print('Error:', error)


if __name__ == '__main__':
    asyncio.run(main())
