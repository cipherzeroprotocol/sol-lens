import requests
import json
from typing import Dict, List, Any, Optional, Union

class HeliusClient:
    """
    Client for interacting with the Helius API for Solana blockchain data.
    
    Provides methods for querying account information, transactions, 
    and other Solana blockchain data.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the Helius API client.
        
        Args:
            api_key (str): API key for authentication
        """
        self.api_key = api_key
        self.base_url = f"https://mainnet.helius-rpc.com/?api-key={self.api_key}"
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, params: List[Any]) -> Dict:
        """
        Make a JSON-RPC request to the Helius API.
        
        Args:
            method (str): The RPC method to call
            params (List[Any]): Parameters for the RPC method
            
        Returns:
            Dict: Response from the API
            
        Raises:
            Exception: If the API request fails
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                raise Exception(f"API error: {json.dumps(result['error'])}")
                
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg += f". Details: {json.dumps(error_data)}"
                except:
                    error_msg += f". Status code: {e.response.status_code}"
            raise Exception(error_msg)
    
    # Account & Balance Endpoints
    
    def get_account_info(self, address: str, encoding: str = "jsonParsed") -> Dict:
        """
        Get information for a specific account.
        
        Args:
            address (str): The account address
            encoding (str, optional): Response encoding. Defaults to "jsonParsed".
            
        Returns:
            Dict: Account information
        """
        params = [address, {"encoding": encoding}]
        return self._make_request("getAccountInfo", params)
    
    def get_balance(self, address: str) -> Dict:
        """
        Get the SOL balance of an account.
        
        Args:
            address (str): The account address
            
        Returns:
            Dict: Account balance information
        """
        params = [address]
        return self._make_request("getBalance", params)
    
    def get_token_account_balance(self, token_account: str) -> Dict:
        """
        Get the token balance for a specific token account.
        
        Args:
            token_account (str): The token account address
            
        Returns:
            Dict: Token balance information
        """
        params = [token_account]
        return self._make_request("getTokenAccountBalance", params)
    
    def get_token_accounts_by_owner(self, owner: str, program_id: str = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA") -> Dict:
        """
        Get all token accounts for an owner.
        
        Args:
            owner (str): The owner's address
            program_id (str, optional): Token program ID. Defaults to SPL Token program.
            
        Returns:
            Dict: List of token accounts
        """
        params = [
            owner, 
            {"programId": program_id}, 
            {"encoding": "jsonParsed"}
        ]
        return self._make_request("getTokenAccountsByOwner", params)
    
    # Transaction Endpoints
    
    def get_transaction(self, signature: str, encoding: str = "jsonParsed") -> Dict:
        """
        Get transaction details.
        
        Args:
            signature (str): Transaction signature
            encoding (str, optional): Response encoding. Defaults to "jsonParsed".
            
        Returns:
            Dict: Transaction details
        """
        params = [
            signature, 
            {"encoding": encoding, "maxSupportedTransactionVersion": 0}
        ]
        return self._make_request("getTransaction", params)
    
    def get_signatures_for_address(self, address: str, limit: int = 100) -> Dict:
        """
        Get signatures for transactions involving an address.
        
        Args:
            address (str): The account address
            limit (int, optional): Maximum number of signatures. Defaults to 100.
            
        Returns:
            Dict: List of transaction signatures
        """
        params = [address, {"limit": limit}]
        return self._make_request("getSignaturesForAddress", params)
    
    def simulate_transaction(self, serialized_tx: str) -> Dict:
        """
        Simulate executing a transaction.
        
        Args:
            serialized_tx (str): Serialized transaction
            
        Returns:
            Dict: Simulation results
        """
        params = [
            serialized_tx, 
            {"encoding": "base64", "commitment": "processed"}
        ]
        return self._make_request("simulateTransaction", params)
    
    # Program Endpoints
    
    def get_program_accounts(self, program_id: str, filters: List[Dict] = None) -> Dict:
        """
        Get all accounts owned by a program.
        
        Args:
            program_id (str): Program ID
            filters (List[Dict], optional): Filters to apply. Defaults to None.
            
        Returns:
            Dict: List of program accounts
        """
        params = [
            program_id, 
            {"encoding": "jsonParsed", "filters": filters or []}
        ]
        return self._make_request("getProgramAccounts", params)