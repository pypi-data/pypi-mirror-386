"""
Digest Authentication for ActTrader API
Handles HTTP Digest authentication as required by the ActTrader API
"""

import hashlib
import random
import string
from typing import Dict, Any, Optional
import requests
from requests.auth import HTTPDigestAuth


class DigestAuth:
    """HTTP Digest Authentication handler"""
    
    def __init__(self, username: str, password: str):
        """
        Initialize digest authentication
        
        Args:
            username: Username for authentication
            password: Password for authentication
        """
        self.username = username
        self.password = password
        self._auth = HTTPDigestAuth(username, password)
    
    def get(self, url: str, config: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Make a GET request with digest authentication
        
        Args:
            url: URL to request
            config: Optional configuration dict
            
        Returns:
            Response object
        """
        if config is None:
            config = {}
        
        # Extract params from config
        params = config.get('params', {})
        
        # Make the request with digest auth
        response = requests.get(url, params=params, auth=self._auth, timeout=30)
        return response
    
    def post(self, url: str, data: Optional[Dict[str, Any]] = None, config: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Make a POST request with digest authentication
        
        Args:
            url: URL to request
            data: Optional data to send
            config: Optional configuration dict
            
        Returns:
            Response object
        """
        if config is None:
            config = {}
        if data is None:
            data = {}
        
        # Extract params from config
        params = config.get('params', {})
        
        # Make the request with digest auth
        response = requests.post(url, json=data, params=params, auth=self._auth, timeout=30)
        return response
