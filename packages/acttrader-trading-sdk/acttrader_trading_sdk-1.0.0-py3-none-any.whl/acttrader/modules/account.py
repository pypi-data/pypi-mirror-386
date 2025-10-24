"""
Account management module
Handles account information and user settings
"""

from typing import Optional, List
from ..client import ActTraderClient
from ..types import ApiResponse, Account


class AccountModule:
    """Account management module for ActTrader API"""
    
    def __init__(self, client: ActTraderClient):
        """
        Initialize account module
        
        Args:
            client: ActTrader HTTP client
        """
        self.client = client
    
    async def get_accounts(self, token: Optional[str] = None) -> ApiResponse[List[Account]]:
        """
        Get all accounts for current user
        
        Args:
            token: Optional authentication token
            
        Returns:
            Array of accounts
            
        Example:
            ```python
            result = await client.account.get_accounts()
            accounts = result.result
            
            for account in accounts:
                print(f"Account {account.AccountID}:")
                print(f"  Balance: {account.Balance} {account.Currency}")
                print(f"  Used Margin: {account.UsedMargin}")
            ```
        """
        # Only pass token if it's explicitly provided, otherwise let client use its stored token
        params = {}
        if token is not None:
            params['token'] = token
        return await self.client.get('/api/v2/account/accounts', params)
    
    async def change_password(self, old_password: str, new_password: str, token: Optional[str] = None) -> ApiResponse[None]:
        """
        Change user password
        
        Args:
            old_password: Current password
            new_password: New password
            token: Optional authentication token
            
        Returns:
            Success response
            
        Example:
            ```python
            await client.account.change_password('old_password', 'new_password')
            ```
        """
        params = {
            'oldpassword': old_password,
            'newpassword': new_password
        }
        if token is not None:
            params['token'] = token
        return await self.client.get('/api/v2/account/changepassword', params)
