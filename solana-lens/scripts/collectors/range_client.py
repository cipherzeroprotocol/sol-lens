import requests
import json
from typing import Dict, List, Any, Optional, Union

class RangeClient:
    """
    Client for interacting with the Range API for blockchain research.
    
    The Range API provides endpoints for address information, risk assessment,
    transaction analysis, and cross-chain exploration.
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.range.org/v1"):
        """
        Initialize the Range API client.
        
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
        Make a request to the Range API.
        
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
    
    # Address Information Endpoints
    
    def get_address_info(self, address: str, network: str = "solana") -> Dict:
        """
        Get information about an address including network and labels.
        
        Args:
            address (str): The blockchain address to query
            network (str): The blockchain network
            
        Returns:
            Dict: Address information including labels
        """
        params = {
            "address": address,
            "network": network
        }
        return self._make_request("address", params=params)
    
    def get_address_risk_score(self, address: str, network: str = "solana") -> Dict:
        """
        Get risk score for a specific address.
        
        Args:
            address (str): The blockchain address to assess
            network (str): The blockchain network
            
        Returns:
            Dict: Risk assessment data
        """
        params = {
            "address": address,
            "network": network
        }
        return self._make_request("risk/address", params=params)
    
    def get_address_counterparties(self, address: str, network: str = "solana") -> Dict:
        """
        Get addresses that have interacted with a specific address.
        
        Args:
            address (str): The blockchain address to query
            network (str): The blockchain network
            
        Returns:
            Dict: Counterparty information
        """
        params = {
            "address": address,
            "network": network
        }
        return self._make_request("address/counterparties", params=params)
    
    def get_address_transactions(self, address: str, network: str = "solana") -> Dict:
        """
        Get transactions for a specific address.
        
        Args:
            address (str): The blockchain address to query
            network (str): The blockchain network
            
        Returns:
            Dict: Transaction data
        """
        params = {
            "address": address,
            "network": network
        }
        return self._make_request("address/transactions", params=params)
    
    def get_transaction_details(self, tx_hash: str, network: str = "solana") -> Dict:
        """
        Get detailed information about a transaction.
        
        Args:
            tx_hash (str): Transaction hash
            network (str): The blockchain network
            
        Returns:
            Dict: Transaction details
        """
        params = {
            "hash": tx_hash,
            "network": network
        }
        return self._make_request("transaction", params=params)
    
    def get_transaction_risk_score(self, tx_hash: str, network: str = "solana") -> Dict:
        """
        Get risk score for a transaction.
        
        Args:
            tx_hash (str): Transaction hash
            network (str): The blockchain network
            
        Returns:
            Dict: Risk assessment data
        """
        params = {
            "hash": tx_hash,
            "network": network
        }
        return self._make_request("risk/transaction", params=params)
    
    # Cross-Chain Explorer
    
    def get_transaction_by_hash(self, tx_hash: str) -> Dict:
        """
        Get transaction by hash across chains.
        
        Args:
            tx_hash (str): Transaction hash
            
        Returns:
            Dict: Cross-chain transaction data
        """
        return self._make_request(f"transaction/hash?hash={tx_hash}")
    
    def get_transactions_by_address(self, address: str) -> Dict:
        """
        Get transactions by address across chains.
        
        Args:
            address (str): Blockchain address
            
        Returns:
            Dict: Cross-chain transaction data
        """
        return self._make_request(f"transactions/address?address={address}")