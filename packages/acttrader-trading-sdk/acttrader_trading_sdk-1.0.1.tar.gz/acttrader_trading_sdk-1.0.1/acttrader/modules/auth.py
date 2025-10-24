"""
Authentication module
Handles user authentication, token management, and password operations
"""

from typing import Optional
from ..client import ActTraderClient
from ..types import ApiResponse


class AuthModule:
    """Authentication module for ActTrader API"""
    
    def __init__(self, client: ActTraderClient):
        """
        Initialize authentication module
        
        Args:
            client: ActTrader HTTP client
        """
        self.client = client
    
    async def get_token(self, lifetime: int = 20) -> ApiResponse[str]:
        """
        Get authentication token
        Requires digest authentication with username and password
        
        Args:
            lifetime: Token lifetime in minutes (default: 20)
            
        Returns:
            Authentication token
            
        Example:
            ```python
            result = await client.auth.get_token(60)
            token = result.result  # "cW6gzixF"
            client.set_token(token)
            ```
        """
        response = await self.client.get_with_digest(
            '/api/v2/auth/token',
            {'lifetime': lifetime}
        )
        
        # Store token in client for future requests
        if response.success and response.result:
            print(f'Token: {response.result}')
            self.client.set_token(response.result)
        
        return response
    
    async def logout(self, token: Optional[str] = None) -> ApiResponse[None]:
        """
        Logout and revoke current token
        
        Args:
            token: Optional token to revoke (uses stored token if not provided)
            
        Returns:
            Success response
            
        Example:
            ```python
            await client.auth.logout()
            ```
        """
        return await self.client.get('/api/v2/auth/logout', {'token': token})
    
    async def reset_password(self, login: str) -> ApiResponse[None]:
        """
        Reset user password
        Password will be sent to user's email
        
        Args:
            login: User login ID
            
        Returns:
            Success response
            
        Example:
            ```python
            await client.auth.reset_password('user_login_id')
            ```
        """
        return await self.client.get('/api/v2/auth/reset', {'login': login})
