"""
Trading Example
Demonstrates trading operations with lots-based trading
"""

import asyncio
from acttrader import ActTrader
from acttrader.types import ActTraderConfig


async def main():
    """Trading operations example"""
    # Initialize client
    config = ActTraderConfig(
        base_url='http://s20.sysfx.com:10001',
        order_ws_url='ws://s20.sysfx.com:10006/ws',
        price_feed_ws_url='wss://eforex20.acttrader.com/charts/ws',
        username='T18425',
        password='Test@1234'
    )
    client = ActTrader(config)
    
    try:
        # Authenticate
        await client.auth.get_token(60)
        await client.initialize_symbol_cache()
        
        # Get accounts
        accounts_result = await client.account.get_accounts()
        accounts = accounts_result.result
        
        if not accounts:
            print("No accounts found")
            return
        
        # Handle both dict and object formats
        first_account = accounts[0]
        if isinstance(first_account, dict):
            account_id = first_account['AccountID']
            balance = first_account['Balance']
            currency = first_account['Currency']
        else:
            account_id = first_account.AccountID
            balance = first_account.Balance
            currency = first_account.Currency
            
        print(f"Using account: {account_id}")
        print(f"Balance: {balance} {currency}")
        
        
        # Place market order using LOTS
        print("\n=== Placing Market Order ===")
        order_result = await client.trading.place_market_order({
            'symbol': 'EURUSD',
            'lots': 0.1,        # 0.1 lots (auto-converted to quantity)
            'side': 1,          # Buy
            'account': account_id,
            'stop': '',     # Stop loss
            'limit': '',    # Take profit
            'commentary': 'Python SDK test order'
        })
        # Handle string, dict, and object responses
        if isinstance(order_result.result, str):
            print(f"Order placed: {order_result.result}")
        elif isinstance(order_result.result, dict):
            print(f"Order placed: {order_result.result.get('OrderID', 'Unknown')}")
        else:
            print(f"Order placed: {order_result.result.OrderID}")
        
        # Place pending order
        print("\n=== Placing Pending Order ===")
        pending_result = await client.trading.place_pending_order({
            'symbol': 'GBPUSD',
            'lots': 0.05,       # 0.05 lots
            'side': 0,          # Sell
            'account': account_id,
            'price': 1.2500,    # Entry price
            'stop': 1.2600,     # Stop loss
            'limit': 1.2400,    # Take profit
            'commentary': 'Pending sell order'
        })
        # Handle string, dict, and object responses
        if isinstance(pending_result.result, str):
            print(f"Pending order placed: {pending_result.result}")
        elif isinstance(pending_result.result, dict):
            print(f"Pending order placed: {pending_result.result.get('OrderID', 'Unknown')}")
        else:
            print(f"Pending order placed: {pending_result.result.OrderID}")
        
        # Get open orders
        print("\n=== Open Orders ===")
        orders_result = await client.trading.get_open_orders()
        orders = orders_result.result
        if orders:
            for order in orders:
                print(f"Order: {order}")
                # Handle both dict and object formats
                if isinstance(order, dict):
                    order_id = order.get('OrderID', 'Unknown')
                    symbol = order.get('Symbol', 'Unknown')
                    side = order.get('Side', 'Unknown')
                    quantity = order.get('Quantity', 'Unknown')
                    price = order.get('Price', 'Unknown')
                else:
                    order_id = getattr(order, 'OrderID', 'Unknown')
                    symbol = getattr(order, 'Symbol', 'Unknown')
                    side = getattr(order, 'Side', 'Unknown')
                    quantity = getattr(order, 'Quantity', 'Unknown')
                    price = getattr(order, 'Price', 'Unknown')
                print(f"Order {order_id}: {symbol} {side} {quantity} @ {price}")
        else:
            print("No open orders found")
        
        # Get open trades
        print("\n=== Open Trades ===")
        trades_result = await client.trading.get_open_trades()
        trades = trades_result.result
        if trades:
            for trade in trades:
                print(f"Trade: {trade}")
                # Handle both dict and object formats
                if isinstance(trade, dict):
                    trade_id = trade.get('TradeID', 'Unknown')
                    symbol = trade.get('Symbol', 'Unknown')
                    side = trade.get('Side', 'Unknown')
                    quantity = trade.get('Quantity', 'Unknown')
                    price = trade.get('Price', 'Unknown')
                else:
                    trade_id = getattr(trade, 'TradeID', 'Unknown')
                    symbol = getattr(trade, 'Symbol', 'Unknown')
                    side = getattr(trade, 'Side', 'Unknown')
                    quantity = getattr(trade, 'Quantity', 'Unknown')
                    price = getattr(trade, 'Price', 'Unknown')
                print(f"Trade {trade_id}: {symbol} {side} {quantity} @ {price}")
        else:
            print("No open trades found")
        
        # Set up streaming for order updates
        print("\n=== Setting up Order Stream ===")
        order_stream = client.stream_orders()
        
        def on_order_event(data):
            print(f"Order event: {data}")
        
        def on_trade_event(data):
            print(f"Trade event: {data}")
        
        order_stream.on('order', on_order_event)
        order_stream.on('trade', on_trade_event)
        
        await order_stream.connect()
        await order_stream.subscribe(['EURUSD', 'GBPUSD'])
        
        # Set up price feed stream
        print("\n=== Setting up Price Feed Stream ===")
        price_stream = client.stream_price_feed()
        
        def on_price_feed(data):
            print(f"Price feed: {data}")
        
        price_stream.on('pricefeed', on_price_feed)
        
        await price_stream.connect()
        await price_stream.subscribe(['EURUSD', 'GBPUSD'])
        
        # Keep running for a while to see events
        print("\n=== Listening for events (30 seconds) ===")
        await asyncio.sleep(30)
        
        # Clean up
        await order_stream.disconnect()
        await price_stream.disconnect()
        await client.auth.logout()
        
    except Exception as error:
        print('Error:', error)


if __name__ == '__main__':
    asyncio.run(main())
