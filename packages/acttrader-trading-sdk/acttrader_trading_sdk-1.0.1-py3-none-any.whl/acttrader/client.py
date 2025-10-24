"""
Base HTTP client for ActTrader API
Handles authentication and request/response processing
"""

import requests
from typing import Dict, Any, Optional, TypeVar, Generic
from urllib.parse import urljoin
import json

from .digest_auth import DigestAuth
from .types import ActTraderConfig, ApiResponse

T = TypeVar('T')


class ActTraderClient:
    """Base HTTP client for ActTrader API"""
    
    def __init__(self, config: ActTraderConfig):
        """
        Initialize the HTTP client
        
        Args:
            config: ActTrader configuration
        """
        self.base_url = config.base_url.rstrip('/')
        self.ws_url = config.ws_url  # Legacy single WebSocket URL
        self.order_ws_url = config.order_ws_url  # WebSocket URL for order updates
        self.price_feed_ws_url = config.price_feed_ws_url  # WebSocket URL for price feed
        self.token = config.token
        self.username = config.username
        self.password = config.password
        
        # Create session for connection pooling
        self.session = requests.Session()
        self.session.timeout = 30
        
        # Setup digest auth if credentials provided
        self.digest_auth = None
        if self.username and self.password:
            self.digest_auth = DigestAuth(self.username, self.password)
    
    def set_token(self, token: str) -> None:
        """Set authentication token"""
        self.token = token
    
    def get_token(self) -> Optional[str]:
        """Get current token"""
        return self.token
    
    def get_ws_url(self) -> Optional[str]:
        """Get WebSocket URL (legacy)"""
        return self.ws_url
    
    def get_order_ws_url(self) -> Optional[str]:
        """Get Order Updates WebSocket URL"""
        return self.order_ws_url
    
    def get_price_feed_ws_url(self) -> Optional[str]:
        """Get Price Feed WebSocket URL"""
        return self.price_feed_ws_url
    
    async def get_with_digest(self, path: str, params: Optional[Dict[str, Any]] = None) -> ApiResponse[T]:
        """
        Make a GET request with digest authentication
        
        Args:
            path: API path
            params: Query parameters
            
        Returns:
            API response
            
        Raises:
            ValueError: If digest authentication not configured
            requests.RequestException: If request fails
        """
        if not self.digest_auth:
            raise ValueError('Digest authentication not configured. Provide username and password.')
        
        try:
            url = urljoin(self.base_url, path)
            config = {'params': params} if params else {}
            
            response = self.digest_auth.get(url, config)
            response.raise_for_status()
            
            return self._parse_response(response.json())
        except requests.exceptions.RequestException as e:
            raise self._handle_error(e)
    
    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> ApiResponse[T]:
        """
        Make a GET request with token authentication
        
        Args:
            path: API path
            params: Query parameters
            
        Returns:
            API response
            
        Raises:
            requests.RequestException: If request fails
        """
        try:
            url = urljoin(self.base_url, path)
            # Add token to params
            query_params = params.copy() if params else {}
            if 'token' not in query_params:
                query_params['token'] = self.token
            
            response = self.session.get(url, params=query_params)
            response.raise_for_status()
            return self._parse_response(response.json())
        except requests.exceptions.RequestException as e:
            raise self._handle_error(e)
    
    async def post(self, path: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> ApiResponse[T]:
        """
        Make a POST request
        
        Args:
            path: API path
            data: Request body data
            params: Query parameters
            
        Returns:
            API response
            
        Raises:
            requests.RequestException: If request fails
        """
        try:
            url = urljoin(self.base_url, path)
            
            # Add token to params
            query_params = params.copy() if params else {}
            if 'token' not in query_params:
                query_params['token'] = self.token
            
            response = self.session.post(url, json=data, params=query_params)
            response.raise_for_status()
            
            return self._parse_response(response.json())
        except requests.exceptions.RequestException as e:
            raise self._handle_error(e)
    
    def _parse_response(self, json_data: Dict[str, Any]) -> ApiResponse:
        """
        Parse JSON response and convert to ApiResponse object
        
        Args:
            json_data: Raw JSON response from API
            
        Returns:
            ApiResponse object
        """
        # Handle different response formats
        if isinstance(json_data, dict):
            # If it's already in ApiResponse format
            if 'success' in json_data:
                return ApiResponse(
                    success=json_data.get('success', False),
                    message=json_data.get('message'),
                    result=json_data.get('result')
                )
            else:
                # If it's a direct result, wrap it in ApiResponse
                return ApiResponse(
                    success=True,
                    message=None,
                    result=json_data
                )
        else:
            # If it's not a dict, wrap it as result
            return ApiResponse(
                success=True,
                message=None,
                result=json_data
            )
    
    def _handle_error(self, error: requests.exceptions.RequestException) -> Exception:
        """
        Handle API errors and convert to appropriate exceptions
        
        Args:
            error: Request exception
            
        Returns:
            Appropriate exception
        """
        if hasattr(error, 'response') and error.response is not None:
            # The request was made and the server responded with a status code
            # that falls out of the range of 2xx
            try:
                error_data = error.response.json()
                message = error_data.get('message', error.response.reason)
            except (ValueError, KeyError):
                message = error.response.reason
            
            return Exception(f'API Error: {message} (Status: {error.response.status_code})')
        elif hasattr(error, 'request'):
            # The request was made but no response was received
            return Exception('No response received from server')
        else:
            # Something happened in setting up the request that triggered an Error
            return error
