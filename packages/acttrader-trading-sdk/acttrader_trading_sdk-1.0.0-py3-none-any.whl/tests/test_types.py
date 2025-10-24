"""
Test type definitions and data models
"""

import pytest
from acttrader.types import (
    ActTraderConfig, ApiResponse, Account, Symbol, Order, Trade,
    OrderSide, OrderType, TokenResponse, Instrument, Symbol2,
    PlaceMarketOrderParams, PlacePendingOrderParams
)


class TestActTraderConfig:
    """Test ActTraderConfig model"""
    
    def test_basic_config(self):
        """Test basic configuration"""
        config = ActTraderConfig(
            base_url='http://rest-api.sysfx.com:18001',
            username='test_user',
            password='test_pass'
        )
        
        assert config.base_url == 'http://rest-api.sysfx.com:18001'
        assert config.username == 'test_user'
        assert config.password == 'test_pass'
        assert config.ws_url is None
        assert config.order_ws_url is None
        assert config.price_feed_ws_url is None
        assert config.token is None
    
    def test_full_config(self):
        """Test full configuration"""
        config = ActTraderConfig(
            base_url='http://rest-api.sysfx.com:18001',
            ws_url='ws://stream.sysfx.com:18002',
            order_ws_url='ws://order-stream.sysfx.com:18002',
            price_feed_ws_url='ws://pricefeed-stream.sysfx.com:18003',
            username='test_user',
            password='test_pass',
            token='test_token'
        )
        
        assert config.base_url == 'http://rest-api.sysfx.com:18001'
        assert config.ws_url == 'ws://stream.sysfx.com:18002'
        assert config.order_ws_url == 'ws://order-stream.sysfx.com:18002'
        assert config.price_feed_ws_url == 'ws://pricefeed-stream.sysfx.com:18003'
        assert config.username == 'test_user'
        assert config.password == 'test_pass'
        assert config.token == 'test_token'


class TestApiResponse:
    """Test ApiResponse model"""
    
    def test_success_response(self):
        """Test successful response"""
        response = ApiResponse(
            success=True,
            result={'OrderID': 12345}
        )
        
        assert response.success is True
        assert response.result == {'OrderID': 12345}
        assert response.message is None
    
    def test_error_response(self):
        """Test error response"""
        response = ApiResponse(
            success=False,
            message='Invalid credentials'
        )
        
        assert response.success is False
        assert response.message == 'Invalid credentials'
        assert response.result is None


class TestAccount:
    """Test Account model"""
    
    def test_account_creation(self):
        """Test account creation"""
        account = Account(
            AccountID=100,
            Balance=10000.50,
            TraderID=123,
            Currency='USD',
            UsedMargin=500.25,
            Reserved=0.0
        )
        
        assert account.AccountID == 100
        assert account.Balance == 10000.50
        assert account.TraderID == 123
        assert account.Currency == 'USD'
        assert account.UsedMargin == 500.25
        assert account.Reserved == 0.0


class TestSymbol:
    """Test Symbol model"""
    
    def test_symbol_creation(self):
        """Test symbol creation"""
        symbol = Symbol(
            Symbol='EURUSD',
            BaseCurrency='EUR',
            QuoteCurrency='USD',
            Description='Euro/US Dollar',
            Active='Y',
            MinTradeSize=1000.0,
            Precision=5,
            ContractSize=100000.0,
            Buy=1.16295,
            Sell=1.16302,
            PriceDate='2025-01-15T10:30:00Z',
            Group='Major',
            Type='Forex'
        )
        
        assert symbol.Symbol == 'EURUSD'
        assert symbol.BaseCurrency == 'EUR'
        assert symbol.QuoteCurrency == 'USD'
        assert symbol.Active == 'Y'
        assert symbol.ContractSize == 100000.0
        assert symbol.Buy == 1.16295
        assert symbol.Sell == 1.16302


class TestOrder:
    """Test Order model"""
    
    def test_order_creation(self):
        """Test order creation"""
        order = Order(
            OrderID=12345,
            Symbol='EURUSD',
            AccountID=100,
            Quantity=100000.0,
            Price=1.16300,
            Type='I',
            Pending='Y',
            Side=1,
            ToClose=None,
            Trail=None,
            Commentary='Test order',
            OpenTime='2025-01-15T10:30:00Z'
        )
        
        assert order.OrderID == 12345
        assert order.Symbol == 'EURUSD'
        assert order.AccountID == 100
        assert order.Quantity == 100000.0
        assert order.Price == 1.16300
        assert order.Type == 'I'
        assert order.Pending == 'Y'
        assert order.Side == 1
        assert order.Commentary == 'Test order'


class TestTrade:
    """Test Trade model"""
    
    def test_trade_creation(self):
        """Test trade creation"""
        trade = Trade(
            TradeID=67890,
            Symbol='EURUSD',
            AccountID=100,
            Quantity=100000.0,
            Price=1.16300,
            Side=1,
            Commission=2.50,
            Interest=0.0,
            Commentary='Test trade',
            OpenTime='2025-01-15T10:30:00Z',
            CloseTime=None,
            OpenPrice=1.16300,
            ClosePrice=None,
            ProfitLoss=None
        )
        
        assert trade.TradeID == 67890
        assert trade.Symbol == 'EURUSD'
        assert trade.AccountID == 100
        assert trade.Quantity == 100000.0
        assert trade.Price == 1.16300
        assert trade.Side == 1
        assert trade.Commission == 2.50
        assert trade.OpenPrice == 1.16300


class TestOrderParams:
    """Test order parameter models"""
    
    def test_market_order_params(self):
        """Test market order parameters"""
        params = PlaceMarketOrderParams(
            token='test_token',
            symbol='EURUSD',
            lots=1.0,
            side=1,
            account=100,
            stop=1.1600,
            limit=1.1700,
            trail=10,
            commentary='Test order'
        )
        
        assert params.token == 'test_token'
        assert params.symbol == 'EURUSD'
        assert params.lots == 1.0
        assert params.quantity is None
        assert params.side == 1
        assert params.account == 100
        assert params.stop == 1.1600
        assert params.limit == 1.1700
        assert params.trail == 10
        assert params.commentary == 'Test order'
    
    def test_pending_order_params(self):
        """Test pending order parameters"""
        params = PlacePendingOrderParams(
            token='test_token',
            symbol='EURUSD',
            quantity=100000.0,
            side=0,
            account=100,
            price=1.1650,
            stop=1.1600,
            limit=1.1700
        )
        
        assert params.token == 'test_token'
        assert params.symbol == 'EURUSD'
        assert params.quantity == 100000.0
        assert params.lots is None
        assert params.side == 0
        assert params.account == 100
        assert params.price == 1.1650
        assert params.stop == 1.1600
        assert params.limit == 1.1700
