"""
Alert module (deprecated)
Handles price alerts - deprecated functionality
"""

from typing import Optional, List
from ..client import ActTraderClient
from ..types import ApiResponse, Alert, AlertResponse


class AlertModule:
    """
    Alert module for ActTrader API
    
    ⚠️ Note: The alert module is deprecated. Please check with ActTrader for alternative solutions.
    """
    
    def __init__(self, client: ActTraderClient):
        """
        Initialize alert module
        
        Args:
            client: ActTrader HTTP client
        """
        self.client = client
    
    async def get_alerts(self, token: Optional[str] = None) -> ApiResponse[List[Alert]]:
        """
        Get active alerts
        
        Args:
            token: Optional authentication token
            
        Returns:
            Array of active alerts
            
        Example:
            ```python
            result = await client.alert.get_alerts()
            alerts = result.result
            ```
        """
        return await self.client.get('/api/v2/alert/alerts', {'token': token})
    
    async def create_alert(self, symbol: str, price: float, alert_type: str, 
                         commentary: str, token: Optional[str] = None) -> ApiResponse[AlertResponse]:
        """
        Create alert
        
        Args:
            symbol: Symbol (e.g., 'EUR/USD')
            price: Alert price
            alert_type: Type: 'BID' or 'ASK'
            commentary: Alert commentary
            token: Optional authentication token
            
        Returns:
            Alert response with AlertID
            
        Example:
            ```python
            result = await client.alert.create_alert(
                'EUR/USD',  # Symbol
                1.1800,     # Price
                'BID',      # Type: 'BID' or 'ASK'
                'Target price'  # Commentary
            )
            ```
        """
        return await self.client.get('/api/v2/alert/create', {
            'symbol': symbol,
            'price': price,
            'type': alert_type,
            'commentary': commentary,
            'token': token
        })
    
    async def modify_alert(self, alert_id: int, price: float, alert_type: str, 
                          commentary: str, token: Optional[str] = None) -> ApiResponse[None]:
        """
        Modify alert
        
        Args:
            alert_id: Alert ID to modify
            price: New alert price
            alert_type: Type: 'BID' or 'ASK'
            commentary: New commentary
            token: Optional authentication token
            
        Returns:
            Success response
            
        Example:
            ```python
            await client.alert.modify_alert(123, 1.1850, 'BID', 'Updated target')
            ```
        """
        return await self.client.get('/api/v2/alert/modify', {
            'alert': alert_id,
            'price': price,
            'type': alert_type,
            'commentary': commentary,
            'token': token
        })
    
    async def remove_alert(self, alert_id: int, token: Optional[str] = None) -> ApiResponse[None]:
        """
        Remove alert
        
        Args:
            alert_id: Alert ID to remove
            token: Optional authentication token
            
        Returns:
            Success response
            
        Example:
            ```python
            await client.alert.remove_alert(123)
            ```
        """
        return await self.client.get('/api/v2/alert/remove', {
            'alert': alert_id,
            'token': token
        })
    
    async def get_triggered_alerts(self, from_date: str, till_date: str, 
                                 token: Optional[str] = None) -> ApiResponse[List[Alert]]:
        """
        Get triggered alerts
        
        Args:
            from_date: From date (YYYYMMDDHH24MI)
            till_date: Till date (YYYYMMDDHH24MI)
            token: Optional authentication token
            
        Returns:
            Array of triggered alerts
            
        Example:
            ```python
            triggered = await client.alert.get_triggered_alerts(
                '202109010000',  # From date (YYYYMMDDHH24MI)
                '202109302359'   # Till date (YYYYMMDDHH24MI)
            )
            ```
        """
        return await self.client.get('/api/v2/alert/triggered', {
            'from': from_date,
            'till': till_date,
            'token': token
        })
