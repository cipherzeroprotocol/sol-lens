import logging
import asyncio
from typing import Dict, List, Any, Optional, Set, Union
from datetime import datetime, timedelta

class TransactionCollector:
    """
    General-purpose collector for Solana transactions data.
    Provides methods for fetching and organizing transaction data.
    """
    
    def __init__(self, helius_client=None, range_client=None):
        """
        Initialize the TransactionCollector.
        
        Args:
            helius_client: Helius API client for transaction data
            range_client: Range API client for cross-chain data
        """
        self.helius_client = helius_client
        self.range_client = range_client
        
        logging.info("TransactionCollector initialized")
    
    async def fetch_address_data(self, address: str, fetch_details: bool = True, 
                                days: int = 30) -> Dict:
        """
        Collect comprehensive data about an address.
        
        Args:
            address: The address to analyze
            fetch_details: Whether to fetch detailed transaction data
            days: How many days of history to analyze
            
        Returns:
            Dictionary containing address data and analytics
        """
        result = {
            "address": address,
            "timestamp": datetime.now().isoformat(),
            "basic_info": None,
            "risk_score": None,
            "transaction_summary": None,
            "balances": None,
            "detailed_transactions": []
        }
        
        # Get basic address info using Range if available
        if self.range_client:
            try:
                address_info = self.range_client.get_address_info(address)
                risk_score = self.range_client.get_address_risk_score(address)
                
                result["basic_info"] = address_info
                result["risk_score"] = risk_score
            except Exception as e:
                logging.warning(f"Failed to get address info from Range: {e}")
        
        # Get transaction signatures
        if self.helius_client:
            try:
                # Get transaction signatures
                signatures = self.helius_client.get_signatures_for_address(address, limit=100)
                result["transaction_summary"] = signatures.get("result", [])
                
                # Get token balances
                if hasattr(self.helius_client, 'get_token_accounts_by_owner'):
                    token_accounts = self.helius_client.get_token_accounts_by_owner(address)
                    result["balances"] = token_accounts
                
                # Optionally fetch detailed transaction data
                if fetch_details and signatures.get("result"):
                    detailed_txs = []
                    for sig_info in signatures.get("result", [])[:30]:  # Limit to 30 for performance
                        try:
                            tx_detail = self.helius_client.get_transaction(sig_info['signature'])
                            if tx_detail and tx_detail.get("result"):
                                detailed_txs.append(tx_detail.get("result"))
                            await asyncio.sleep(0.1)  # Rate limit
                        except Exception as tx_err:
                            logging.debug(f"Failed to fetch tx detail: {tx_err}")
                    
                    result["detailed_transactions"] = detailed_txs
                
            except Exception as e:
                logging.error(f"Error fetching transaction data for {address}: {e}")
                result["error"] = str(e)
        
        return result
    
    async def fetch_transactions_paginated(self, address: str, limit_total: int = 1000) -> List[Dict]:
        """
        Fetch transactions with pagination support.
        
        Args:
            address: Address to fetch transactions for
            limit_total: Maximum number of transactions to fetch
            
        Returns:
            List of transaction details
        """
        if not self.helius_client:
            raise ValueError("HeliusClient is required for transaction fetching")
            
        all_signatures = []
        last_signature = None
        pages = 0
        max_pages = (limit_total // 100) + 1
        
        logging.debug(f"Fetching up to {limit_total} signatures for {address}...")
        while len(all_signatures) < limit_total and pages < max_pages:
            try:
                options = {"limit": 100}
                if last_signature:
                    options["before"] = last_signature
                
                # Use async method if available, otherwise fallback to sync
                if hasattr(self.helius_client, 'get_signatures_for_address_async'):
                    result = await self.helius_client.get_signatures_for_address_async(address, **options)
                else:
                    result = self.helius_client.get_signatures_for_address(address, **options)
                
                signatures = result.get("result", [])
                if not signatures:
                    break
                    
                all_signatures.extend(signatures)
                last_signature = signatures[-1].get("signature")
                pages += 1
                logging.debug(f"Fetched page {pages}, total signatures: {len(all_signatures)}")
                await asyncio.sleep(0.1)  # Rate limit
                
            except Exception as e:
                logging.warning(f"Error fetching signatures page {pages+1} for {address}: {e}")
                break
        
        # Fetch transaction details
        transaction_details = []
        
        # Process in batches to avoid overwhelming the API
        batch_size = 20
        for i in range(0, len(all_signatures), batch_size):
            batch = all_signatures[i:i+batch_size]
            batch_tasks = []
            
            for sig_info in batch:
                if hasattr(self.helius_client, 'get_transaction_async'):
                    batch_tasks.append(self.helius_client.get_transaction_async(sig_info['signature']))
                else:
                    # Fallback to sync method
                    try:
                        tx_detail = self.helius_client.get_transaction(sig_info['signature'])
                        if tx_detail and tx_detail.get("result"):
                            transaction_details.append(tx_detail.get("result"))
                    except Exception as e:
                        logging.debug(f"Failed to fetch tx detail: {e}")
            
            if batch_tasks:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                for res in batch_results:
                    if isinstance(res, Exception):
                        logging.debug(f"Failed to fetch transaction detail: {res}")
                    elif res and res.get("result"):
                        transaction_details.append(res.get("result"))
            
            # Rate limit between batches
            if i + batch_size < len(all_signatures):
                await asyncio.sleep(0.5)
        
        logging.info(f"Fetched {len(transaction_details)} transaction details for {address}")
        return transaction_details
    
    def build_transaction_graph(self, transactions: List[Dict]) -> Dict:
        """
        Build a transaction graph from a list of transactions.
        
        Args:
            transactions: List of transaction details
            
        Returns:
            Network graph data structure
        """
        from scripts.analysis.network_builder import NetworkBuilder
        
        network_builder = NetworkBuilder(helius_client=self.helius_client)
        
        graph = network_builder.build_transaction_graph(transactions)
        graph_data = network_builder._export_graph_to_d3_format_data(graph)
        
        return graph_data
