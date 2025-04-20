import requests
import json
from typing import Dict, List, Any, Optional, Union

class VybeClient:
    """
    Client for interacting with the Vybe API for Solana blockchain analytics.
    
    Provides methods for querying account information, token data, 
    program analytics, and market/price data.
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.vybe.xyz/v1"):
        """
        Initialize the Vybe API client.
        
        Args:
            api_key (str): API key for authentication
            base_url (str, optional): Base URL for the API.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _make_request(self, endpoint: str, method: str = "GET", params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> Dict:
        """
        Make a request to the Vybe API.
        
        Args:
            endpoint (str): API endpoint to call
            method (str, optional): HTTP method. Defaults to "GET".
            params (Dict, optional): Query parameters. Defaults to None.
            data (Dict, optional): Request body. Defaults to None.
            
        Returns:
            Dict: Response from the API
            
        Raises:
            Exception: If the API request fails
        """
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, params=params, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg += f". Details: {json.dumps(error_data)}"
                except:
                    error_msg += f". Status code: {e.response.status_code}"
            raise Exception(error_msg)
    
    # Account Endpoints
    
    def get_known_accounts(self, query_params: Optional[Dict] = None) -> Dict:
        """
        Get a categorized list of labeled Solana accounts.
        
        Args:
            query_params (Dict, optional): Query parameters for filtering. Defaults to None.
                Possible parameters: ownerAddress, name, labels, entityName, entityId, 
                sortByAsc, sortByDesc
                
        Returns:
            Dict: List of known accounts
        """
        return self._make_request("account/known-accounts", params=query_params)
    
    def get_token_balance(self, owner_address: str, query_params: Optional[Dict] = None) -> Dict:
        """
        Get SPL token balances for a provided account address.
        
        Args:
            owner_address (str): The owner's address
            query_params (Dict, optional): Query parameters. Defaults to None.
                Possible parameters: includeNoPriceBalance, sortByAsc, sortByDesc, limit, page
                
        Returns:
            Dict: Token balance information
        """
        return self._make_request(f"account/token-balance/{owner_address}", params=query_params)
    
    def get_token_balance_timeseries(self, owner_address: str, days: int = 30) -> Dict:
        """
        Get daily SPL token balances for an account in time-series format.
        
        Args:
            owner_address (str): The owner's address
            days (int, optional): Number of days of data. Defaults to 30.
                
        Returns:
            Dict: Time-series token balance data
        """
        params = {"days": days}
        return self._make_request(f"account/token-balance-ts/{owner_address}", params=params)
    
    # Program Endpoints
    
    def get_program_details(self, program_id: str) -> Dict:
        """
        Get program details including metrics.
        
        Args:
            program_id (str): The program ID
                
        Returns:
            Dict: Program details and metrics
        """
        return self._make_request(f"program/{program_id}")
    
    def get_program_active_users(self, program_id: str, query_params: Optional[Dict] = None) -> Dict:
        """
        Get active users with instruction/transaction counts.
        
        Args:
            program_id (str): The program ID
            query_params (Dict, optional): Query parameters. Defaults to None.
                Possible parameters: days, limit, sortByAsc, sortByDesc
                
        Returns:
            Dict: List of active users
        """
        return self._make_request(f"program/{program_id}/active-users", params=query_params)
    
    def get_program_active_users_timeseries(self, program_id: str, range_param: str) -> Dict:
        """
        Get time series data for active users.
        
        Args:
            program_id (str): The program ID
            range_param (str): Time range (e.g., '7d', '30d')
                
        Returns:
            Dict: Time-series active user data
        """
        params = {"range": range_param}
        return self._make_request(f"program/{program_id}/active-users-ts", params=params)
    
    # Token Endpoints
    
    def get_token_details(self, mint_address: str) -> Dict:
        """
        Get token details and 24h activity overview.
        
        Args:
            mint_address (str): The token mint address
                
        Returns:
            Dict: Token details and activity
        """
        return self._make_request(f"token/{mint_address}")
    
    def get_token_top_holders(self, mint_address: str, query_params: Optional[Dict] = None) -> Dict:
        """
        Get top token holders.
        
        Args:
            mint_address (str): The token mint address
            query_params (Dict, optional): Query parameters. Defaults to None.
                Possible parameters: page, limit
                
        Returns:
            Dict: List of top token holders
        """
        return self._make_request(f"token/{mint_address}/top-holders", params=query_params)
    
    def get_token_transfers(self, query_params: Optional[Dict] = None) -> Dict:
        """
        Get token transfer transactions with filtering options.
        
        Args:
            query_params (Dict, optional): Query parameters for filtering. Defaults to None.
                
        Returns:
            Dict: Token transfer data
        """
        return self._make_request("token/transfers", params=query_params)
    
    def get_token_trades(self, query_params: Optional[Dict] = None) -> Dict:
        """
        Get trade data executed within programs.
        
        Args:
            query_params (Dict, optional): Query parameters for filtering. Defaults to None.
                
        Returns:
            Dict: Token trade data
        """
        return self._make_request("token/trades", params=query_params)
    
    # Market/Price Endpoints
    
    def get_token_ohlcv(self, mint_address: str, query_params: Optional[Dict] = None) -> Dict:
        """
        Get OHLC price data for tokens.
        
        Args:
            mint_address (str): The token mint address
            query_params (Dict, optional): Query parameters. Defaults to None.
                Possible parameters: resolution, timeStart, timeEnd, limit, page
                
        Returns:
            Dict: OHLC price data
        """
        return self._make_request(f"price/{mint_address}/token-ohlcv", params=query_params)
    
    def get_markets(self) -> Dict:
        """
        Get all available market IDs.
        
        Returns:
            Dict: List of market IDs
        """
        return self._make_request("price/markets")