import time
import logging
import asyncio
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

class MixerCollector:
    """
    Collector for data related to mixer services and money laundering patterns on Solana.
    Responsible for identifying mixers, collecting transaction data, and analyzing interactions.
    """
    
    def __init__(self, helius_client=None, range_client=None, vybe_client=None):
        """
        Initialize the MixerCollector.
        
        Args:
            helius_client: Helius API client instance for fetching transaction data
            range_client: Range API client for risk assessment
            vybe_client: Vybe API client for analytics data
        """
        self.helius_client = helius_client
        self.range_client = range_client
        self.vybe_client = vybe_client
        
        # Known mixer service addresses
        self.known_mixers = {
            "tor1xzb2Zyy1cUxXmyJfR8aNXuWnwHG8AwgaG7UGD4K": "Tornado Cash Router (Wormhole)",
            "2cTfkPdJEKoZ4252vyscpuLMXxYNABSQMGyLQYvyKCNh": "Solana Mixer",
            "CJsLwbP1iu5DuUikHEJnLfANgKy6stB2uFgvBBHoyxwz": "Cyclos Mixer",
            # More mixers can be added here
        }
        
        # Known exchange addresses to filter out from potential mixer users
        self.known_exchanges = set([
            # Example exchange addresses
            "CEXaddr1111111111111111111111111111111111111",
            "CEXaddr2222222222222222222222222222222222222",
        ])
        
        logging.info(f"MixerCollector initialized with {len(self.known_mixers)} known mixer services")
    
    async def fetch_transactions_paginated(self, address: str, limit_total: int = 1000) -> List[Dict]:
        """
        Fetch transactions with pagination support for a specific address.
        
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
        max_pages = (limit_total // 100) + 1  # Helius limit is usually 100 per page
        
        logging.debug(f"Fetching up to {limit_total} signatures for {address}...")
        while len(all_signatures) < limit_total and pages < max_pages:
            try:
                options = {"limit": 100}
                if last_signature:
                    options["before"] = last_signature
                    
                # Use the async method if available, otherwise fallback to sync
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
                
        logging.debug(f"Fetching details for {len(all_signatures)} signatures...")
        transaction_details = []
        
        # Fetch details concurrently
        tasks = []
        for sig_info in all_signatures:
            # Use async method if available
            if hasattr(self.helius_client, 'get_transaction_async'):
                tasks.append(self.helius_client.get_transaction_async(sig_info['signature']))
            else:
                # Use synchronous method as fallback
                try:
                    tx_response = self.helius_client.get_transaction(sig_info['signature'])
                    if tx_response and tx_response.get("result"):
                        transaction_details.append(tx_response.get("result"))
                    await asyncio.sleep(0.1)  # Rate limit for sync requests
                except Exception as e:
                    logging.warning(f"Failed to fetch transaction detail: {e}")
        
        # If using async methods, gather results
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    logging.warning(f"Failed to fetch transaction detail: {res}")
                elif res and res.get("result"):
                    transaction_details.append(res["result"])
        
        logging.info(f"Fetched {len(transaction_details)} transaction details for {address}")
        return transaction_details
    
    async def analyze_mixers(self, limit_per_mixer: int = 500) -> Dict:
        """
        Analyze mixer services by fetching and analyzing recent transactions.
        
        Args:
            limit_per_mixer: Maximum number of transactions to fetch per mixer
            
        Returns:
            Dictionary containing mixer analysis results
        """
        results = {
            "mixer_services_summary": [],
            "potential_mixer_users": [],
            "error": None
        }
        
        if not self.helius_client:
            results["error"] = "HeliusClient required for mixer analysis"
            return results
            
        all_mixer_interactions = []
        mixer_fetch_tasks = []
        
        # Start fetching transactions for all known mixers
        for mixer_address, mixer_name in self.known_mixers.items():
            logging.info(f"Fetching transactions for mixer: {mixer_name} ({mixer_address})")
            mixer_fetch_tasks.append(self.fetch_transactions_paginated(mixer_address, limit_total=limit_per_mixer))
            
        fetched_tx_lists = await asyncio.gather(*mixer_fetch_tasks, return_exceptions=True)
        
        # Process results for each mixer
        for i, mixer_address in enumerate(self.known_mixers.keys()):
            mixer_name = self.known_mixers[mixer_address]
            mixer_summary = {"address": mixer_address, "name": mixer_name, "interactions": 0, "volume": 0.0, "error": None}
            
            if isinstance(fetched_tx_lists[i], Exception):
                mixer_summary["error"] = str(fetched_tx_lists[i])
                logging.error(f"Error fetching transactions for mixer {mixer_address}: {fetched_tx_lists[i]}")
            else:
                transactions = fetched_tx_lists[i]
                mixer_summary["interactions"] = len(transactions)
                all_mixer_interactions.extend(transactions)
                
                # Calculate volume from transactions
                total_volume = await self._calculate_mixer_volume(mixer_address, transactions)
                mixer_summary["volume"] = total_volume
                
            results["mixer_services_summary"].append(mixer_summary)
            
        # Identify potential users by analyzing transfers
        users = await self._identify_mixer_users(all_mixer_interactions)
        
        # Filter out known exchanges and mixer addresses
        filtered_users = users - set(self.known_mixers.keys()) - self.known_exchanges
        results["potential_mixer_users"] = list(filtered_users)
        
        logging.info(f"Identified {len(results['potential_mixer_users'])} potential unique mixer users")
        return results
    
    async def _calculate_mixer_volume(self, mixer_address: str, transactions: List[Dict]) -> float:
        """Calculate the total volume flowing through a mixer from transaction data."""
        from scripts.analysis.network_builder import NetworkBuilder
        
        total_volume = 0.0
        network_builder = NetworkBuilder(helius_client=self.helius_client)
        
        for tx in transactions:
            transfers = network_builder._extract_transfers(tx)
            for t in transfers:
                if t.get('source') == mixer_address or t.get('destination') == mixer_address:
                    # Convert amount to proper value based on decimals (simplified)
                    amount_value = float(t.get('amount', 0)) / 1e9  # Assuming SOL or 9 decimals
                    total_volume += amount_value
                    
        return total_volume
    
    async def _identify_mixer_users(self, mixer_transactions: List[Dict]) -> Set[str]:
        """Identify potential mixer users from transaction data."""
        from scripts.analysis.network_builder import NetworkBuilder
        
        users = set()
        network_builder = NetworkBuilder(helius_client=self.helius_client)
        
        for tx in mixer_transactions:
            transfers = network_builder._extract_transfers(tx)
            for t in transfers:
                # Check if source or destination is a known mixer
                if t.get('source') in self.known_mixers:
                    users.add(t.get('destination'))
                if t.get('destination') in self.known_mixers:
                    users.add(t.get('source'))
                    
        return users
    
    def get_known_exchange_addresses(self) -> Set[str]:
        """Return the set of known exchange addresses to filter out from mixer users."""
        if self.vybe_client:
            try:
                # Try to get exchange addresses from Vybe API if available
                exchange_data = self.vybe_client.get_known_accounts({"labels": "exchange"})
                if exchange_data and "accounts" in exchange_data:
                    exchange_addresses = {account["address"] for account in exchange_data["accounts"]}
                    self.known_exchanges.update(exchange_addresses)
            except Exception as e:
                logging.warning(f"Failed to fetch exchange addresses from Vybe: {e}")
                
        return self.known_exchanges
