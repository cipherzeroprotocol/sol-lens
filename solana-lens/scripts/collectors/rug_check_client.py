import datetime
import requests
import json
from typing import Dict, List, Any, Optional, Union

class RugCheckClient:
    """
    Client for interacting with the RugCheck API for Solana token analysis.
    
    Provides methods for token risk assessment, insider network analysis,
    and token verification.
    """
    
    def __init__(self, jwt_token: str, base_url: str = "https://api.rugcheck.xyz/v1"):
        """
        Initialize the RugCheck API client.
        
        Args:
            jwt_token (str): JWT token for authentication
            base_url (str, optional): Base URL for the API.
        """
        self.jwt_token = jwt_token
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _make_request(self, endpoint: str, method: str = "GET", params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> Dict:
        """
        Make a request to the RugCheck API.
        
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
    
    # Authentication
    
    @classmethod
    def login_with_solana(cls, wallet: str, message: str, signature: Dict) -> "RugCheckClient":
        """
        Create a client instance by logging in with a Solana wallet.
        
        Args:
            wallet (str): Solana wallet address
            message (str): Message that was signed
            signature (Dict): Signature data
            
        Returns:
            RugCheckClient: Authenticated client instance
        """
        base_url = "https://api.rugcheck.xyz/v1"
        url = f"{base_url}/auth/login/solana"
        
        payload = {
            "wallet": wallet,
            "message": {
                "message": message,
                "publicKey": wallet,
                "timestamp": int(datetime.now().timestamp())
            },
            "signature": signature
        }
        
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            token = result.get("token")
            
            if not token:
                raise Exception("No token returned from login")
                
            return cls(token, base_url)
        except requests.exceptions.RequestException as e:
            error_msg = f"Login failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg += f". Details: {json.dumps(error_data)}"
                except:
                    error_msg += f". Status code: {e.response.status_code}"
            raise Exception(error_msg)
    
    # Token Analysis Endpoints
    
    def get_token_report(self, token_mint: str) -> Dict:
        """
        Get a detailed report for a token.
        
        Args:
            token_mint (str): Token mint address
            
        Returns:
            Dict: Detailed token report
        """
        return self._make_request(f"tokens/{token_mint}/report")
    
    def get_token_report_summary(self, token_mint: str, cache_only: bool = False) -> Dict:
        """
        Get a summary report for a token.
        
        Args:
            token_mint (str): Token mint address
            cache_only (bool, optional): Only return cached reports. Defaults to False.
            
        Returns:
            Dict: Token report summary
        """
        params = {"cacheOnly": "true" if cache_only else "false"}
        return self._make_request(f"tokens/{token_mint}/report/summary", params=params)
    
    def get_token_insider_graph(self, token_mint: str) -> Dict:
        """
        Generate an insider graph for a token.
        
        Args:
            token_mint (str): Token mint address
            
        Returns:
            Dict: Token insider graph data
        """
        return self._make_request(f"tokens/{token_mint}/insiders/graph")
    
    # Token Verification Endpoints
    
    def check_token_eligibility(self, token_mint: str) -> Dict:
        """
        Check if a token is eligible for verification.
        
        Args:
            token_mint (str): Token mint address
            
        Returns:
            Dict: Token eligibility status
        """
        data = {"mint": token_mint}
        return self._make_request("tokens/verify/eligible", method="POST", data=data)
    
    def verify_token(self, token_mint: str, payer: str, description: str, 
                   links: Dict[str, str], signature: str) -> Dict:
        """
        Submit a token for verification.
        
        Args:
            token_mint (str): Token mint address
            payer (str): Payer address
            description (str): Token description
            links (Dict[str, str]): Social media and website links
            signature (str): Transaction signature
            
        Returns:
            Dict: Verification submission result
        """
        data = {
            "mint": token_mint,
            "payer": payer,
            "signature": signature,
            "data": {
                "description": description,
                "links": links,
                "termsAccepted": True,
                "dataIntegrityAccepted": True
            }
        }
        return self._make_request("tokens/verify", method="POST", data=data)
    
    # Token Voting Endpoints
    
    def get_token_votes(self, token_mint: str) -> Dict:
        """
        Get voting statistics for a token.
        
        Args:
            token_mint (str): Token mint address
            
        Returns:
            Dict: Token voting statistics
        """
        return self._make_request(f"tokens/{token_mint}/votes")
    
    # Statistics Endpoints
    
    def get_recently_detected_tokens(self) -> List[Dict]:
        """
        Get recently detected tokens.
        
        Returns:
            List[Dict]: Recently detected tokens
        """
        return self._make_request("stats/new_tokens")
    
    def get_trending_tokens(self) -> List[Dict]:
        """
        Get most voted for tokens in the past 24 hours.
        
        Returns:
            List[Dict]: Trending tokens
        """
        return self._make_request("stats/trending")
    
    def get_recently_verified_tokens(self) -> List[Dict]:
        """
        Get recently verified tokens.
        
        Returns:
            List[Dict]: Recently verified tokens
        """
        return self._make_request("stats/verified")