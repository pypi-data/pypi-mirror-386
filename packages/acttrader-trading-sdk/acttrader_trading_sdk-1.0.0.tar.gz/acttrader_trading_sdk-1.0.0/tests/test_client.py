"""
Test HTTP client functionality
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from acttrader.client import ActTraderClient
from acttrader.types import ActTraderConfig


class TestActTraderClient:
    """Test ActTraderClient"""
    
    def test_client_initialization(self):
        """Test client initialization"""
        config = ActTraderConfig(
            base_url='http://rest-api.sysfx.com:18001',
            username='test_user',
            password='test_pass'
        )
        
        client = ActTraderClient(config)
        
        assert client.base_url == 'http://rest-api.sysfx.com:18001'
        assert client.username == 'test_user'
        assert client.password == 'test_pass'
        assert client.token is None
        assert client.digest_auth is not None
    
    def test_client_initialization_with_token(self):
        """Test client initialization with token"""
        config = ActTraderConfig(
            base_url='http://rest-api.sysfx.com:18001',
            token='test_token'
        )
        
        client = ActTraderClient(config)
        
        assert client.base_url == 'http://rest-api.sysfx.com:18001'
        assert client.token == 'test_token'
        assert client.username is None
        assert client.password is None
        assert client.digest_auth is None
    
    def test_set_token(self):
        """Test setting token"""
        config = ActTraderConfig(base_url='http://rest-api.sysfx.com:18001')
        client = ActTraderClient(config)
        
        client.set_token('new_token')
        assert client.get_token() == 'new_token'
    
    def test_get_ws_urls(self):
        """Test getting WebSocket URLs"""
        config = ActTraderConfig(
            base_url='http://rest-api.sysfx.com:18001',
            ws_url='ws://stream.sysfx.com:18002',
            order_ws_url='ws://order-stream.sysfx.com:18002',
            price_feed_ws_url='ws://pricefeed-stream.sysfx.com:18003'
        )
        
        client = ActTraderClient(config)
        
        assert client.get_ws_url() == 'ws://stream.sysfx.com:18002'
        assert client.get_order_ws_url() == 'ws://order-stream.sysfx.com:18002'
        assert client.get_price_feed_ws_url() == 'ws://pricefeed-stream.sysfx.com:18003'
    
    @pytest.mark.asyncio
    async def test_get_with_digest_success(self):
        """Test successful GET request with digest auth"""
        config = ActTraderConfig(
            base_url='http://rest-api.sysfx.com:18001',
            username='test_user',
            password='test_pass'
        )
        
        client = ActTraderClient(config)
        
        # Mock the digest auth response
        mock_response = Mock()
        mock_response.json.return_value = {'success': True, 'result': 'test_token'}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.digest_auth, 'get', return_value=mock_response):
            result = await client.get_with_digest('/api/v2/auth/token', {'lifetime': 60})
            
            assert result == {'success': True, 'result': 'test_token'}
    
    @pytest.mark.asyncio
    async def test_get_with_digest_no_auth(self):
        """Test GET request with digest auth when not configured"""
        config = ActTraderConfig(base_url='http://rest-api.sysfx.com:18001')
        client = ActTraderClient(config)
        
        with pytest.raises(ValueError, match='Digest authentication not configured'):
            await client.get_with_digest('/api/v2/auth/token')
    
    @pytest.mark.asyncio
    async def test_get_success(self):
        """Test successful GET request"""
        config = ActTraderConfig(
            base_url='http://rest-api.sysfx.com:18001',
            token='test_token'
        )
        
        client = ActTraderClient(config)
        
        # Mock the session response
        mock_response = Mock()
        mock_response.json.return_value = {'success': True, 'result': [{'AccountID': 100}]}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'get', return_value=mock_response):
            result = await client.get('/api/v2/account/accounts')
            
            assert result == {'success': True, 'result': [{'AccountID': 100}]}
    
    @pytest.mark.asyncio
    async def test_post_success(self):
        """Test successful POST request"""
        config = ActTraderConfig(
            base_url='http://rest-api.sysfx.com:18001',
            token='test_token'
        )
        
        client = ActTraderClient(config)
        
        # Mock the session response
        mock_response = Mock()
        mock_response.json.return_value = {'success': True, 'result': {'OrderID': 12345}}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(client.session, 'post', return_value=mock_response):
            result = await client.post('/api/v2/trading/placemarket', {'symbol': 'EURUSD'})
            
            assert result == {'success': True, 'result': {'OrderID': 12345}}
    
    def test_handle_error_with_response(self):
        """Test error handling with response"""
        config = ActTraderConfig(base_url='http://rest-api.sysfx.com:18001')
        client = ActTraderClient(config)
        
        # Mock error with response
        mock_error = Mock()
        mock_error.response = Mock()
        mock_error.response.status_code = 400
        mock_error.response.reason = 'Bad Request'
        mock_error.response.json.return_value = {'message': 'Invalid request'}
        
        error = client._handle_error(mock_error)
        
        assert 'API Error: Invalid request (Status: 400)' in str(error)
    
    def test_handle_error_no_response(self):
        """Test error handling without response"""
        config = ActTraderConfig(base_url='http://rest-api.sysfx.com:18001')
        client = ActTraderClient(config)
        
        # Mock error without response
        mock_error = Mock()
        mock_error.response = None
        mock_error.request = Mock()
        
        error = client._handle_error(mock_error)
        
        assert 'No response received from server' in str(error)
