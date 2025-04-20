import logging
import asyncio
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

class AddressPoisoningCollector:
    """
    Collector for data related to address poisoning attempts on Solana.
    Detects small dust transfers that might be attempts to trick users.
    """
    
    def __init__(self, helius_client=None):
        """
        Initialize the AddressPoisoningCollector.
        
        Args:
            helius_client: Helius API client instance for fetching transaction data
        """
        if not helius_client:
            raise ValueError("HeliusClient is required for AddressPoisoningCollector")
            
        self.helius_client = helius_client
        self.token_metadata_cache = {}  # Cache token metadata to avoid repeated lookups
        
        logging.info("AddressPoisoningCollector initialized")
    
    async def collect_address_transactions(self, addresses: List[str], limit_per_address: int = 200) -> List[Dict]:
        """
        Collect recent transactions for a list of addresses.
        
        Args:
            addresses: List of addresses to collect transactions for
            limit_per_address: Maximum number of transactions per address
            
        Returns:
            List of transaction details
        """
        from scripts.collectors.sandwich_collector import SandwichCollector
        
        sandwich_collector = SandwichCollector(self.helius_client)
        transactions_to_check = []
        
        for address in addresses:
            try:
                # Get recent signatures for this address
                signatures_result = self.helius_client.get_signatures_for_address(address, limit=limit_per_address)
                signatures = signatures_result.get("result", [])
                
                # Fetch transaction details
                for sig in signatures:
                    tx_detail = sandwich_collector.fetch_transaction_details(sig['signature'])
                    if tx_detail:
                        transactions_to_check.append(tx_detail)
                        await asyncio.sleep(0.1)  # Rate limit
            except Exception as e:
                logging.warning(f"Error fetching transactions for {address}: {e}")
                
        logging.info(f"Collected {len(transactions_to_check)} transactions for analysis")
        return transactions_to_check
    
    async def analyze_poisoning_attempts(self, transactions: List[Dict]) -> Dict:
        """
        Analyze transactions to detect potential address poisoning attempts.
        
        Args:
            transactions: List of transaction details to analyze
            
        Returns:
            Dictionary with potential poisoning transactions and statistics
        """
        from scripts.analysis.network_builder import NetworkBuilder
        
        results = {
            "potential_poisoning_txs": [],
            "statistics": {"checked_tx_count": 0, "potential_count": 0},
            "error": None
        }
        
        network_builder = NetworkBuilder(helius_client=self.helius_client)
        checked_count = 0
        potential_count = 0
        processed_tx_sigs = set()
        
        for tx in transactions:
            tx_hash = tx.get("transaction", {}).get("signatures", [None])[0]
            if not tx_hash or tx_hash in processed_tx_sigs:
                continue
                
            processed_tx_sigs.add(tx_hash)
            checked_count += 1
            
            transfers = network_builder._extract_transfers(tx)
            for t in transfers:
                # Heuristic: Small amount (e.g., 1 smallest unit) of an SPL token
                if t.get('type') == 'SPL' and t.get('amount') == 1:
                    mint = t.get('mint')
                    if not mint:
                        continue
                        
                    # Check token metadata (use cache)
                    is_suspicious_token = await self._check_token_suspicious(mint)
                    
                    if is_suspicious_token:
                        results["potential_poisoning_txs"].append({
                            "tx_hash": tx_hash,
                            "sender": t.get('source'),
                            "receiver": t.get('destination'),
                            "mint": mint,
                            "amount": t.get('amount'),
                            "timestamp": tx.get("blockTime"),
                            "token_symbol": await self._get_token_symbol(mint)
                        })
                        potential_count += 1
                        logging.info(f"Potential poisoning tx found: {tx_hash} (mint: {mint})")
                        break  # Flag transaction once
                        
        results["statistics"]["checked_tx_count"] = checked_count
        results["statistics"]["potential_count"] = potential_count
        
        logging.info(f"Checked {checked_count} transactions, found {potential_count} potential poisoning attempts")
        return results
    
    async def _check_token_suspicious(self, mint: str) -> bool:
        """Check if a token is suspicious based on its metadata."""
        if mint in self.token_metadata_cache:
            return self.token_metadata_cache[mint]
            
        try:
            # Use Helius method to get metadata
            if hasattr(self.helius_client, 'get_token_metadata_async'):
                metadata_res = await self.helius_client.get_token_metadata_async([mint])
            else:
                # Mock implementation if method doesn't exist
                # In real implementation, we would use a synchronous alternative
                metadata_res = {"result": [None]}
                
            metadata = metadata_res.get("result", [None])[0]
            
            # Criteria for suspicious: No metadata, no symbol, no name, etc.
            if not metadata or (not metadata.get('name') and not metadata.get('symbol')):
                is_suspicious = True
            else:
                is_suspicious = False
                
            self.token_metadata_cache[mint] = is_suspicious
            await asyncio.sleep(0.05)  # Rate limit metadata calls
            return is_suspicious
            
        except Exception as e:
            logging.debug(f"Failed to get metadata for mint {mint}: {e}")
            self.token_metadata_cache[mint] = False  # Assume not suspicious on error
            return False
    
    async def _get_token_symbol(self, mint: str) -> str:
        """Get token symbol from metadata if available."""
        try:
            if hasattr(self.helius_client, 'get_token_metadata_async'):
                metadata_res = await self.helius_client.get_token_metadata_async([mint])
                metadata = metadata_res.get("result", [None])[0]
                if metadata and metadata.get('symbol'):
                    return metadata.get('symbol')
            return mint[:6]  # Return first 6 chars of mint address as fallback
        except:
            return mint[:6]
