import time
import logging
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta

class BridgeCollector:
    """
    Collector for data related to cross-chain bridges and money laundering patterns across blockchains.
    Responsible for identifying bridge transactions, tracking cross-chain flows, and detecting suspicious patterns.
    """
    
    def __init__(self, helius_client=None, range_client=None, vybe_client=None):
        """
        Initialize the BridgeCollector.
        
        Args:
            helius_client: Helius API client instance for fetching Solana transaction data
            range_client: Range API client for cross-chain data and risk assessment
            vybe_client: Vybe API client for analytics data
        """
        self.helius_client = helius_client
        self.range_client = range_client
        self.vybe_client = vybe_client
        
        # Known bridge program addresses and contracts on Solana
        self.known_bridges = {
            "wormhole": {
                "name": "Wormhole Bridge",
                "solana_addresses": [
                    "worm2ZoG2kUd4vFXhvjh93UUH596ayRfgQ2MgjNMTth",  # Core bridge
                    "wormDTUJ6AWPNvk59vGQbDvGJmqbDTdgWgAqcLBCgUb"   # Token bridge
                ],
                "supported_chains": ["ethereum", "bsc", "polygon", "avalanche", "arbitrum", "optimism"]
            },
            "allbridge": {
                "name": "Allbridge",
                "solana_addresses": [
                    "ALLBridnP1jw8WpG6SbRGZDhGQr8AQqXT4s1yjCHkwW"
                ],
                "supported_chains": ["ethereum", "bsc", "polygon", "avalanche", "tron"]
            },
            "portal": {
                "name": "Portal (Wormhole)",
                "solana_addresses": [
                    "Port7uDYB3wk6GJAw4KT1WpTeMtSu9bTcChBHkX2LfR"
                ],
                "supported_chains": ["ethereum", "bsc", "polygon", "avalanche"]
            },
            "sollet": {
                "name": "Sollet Bridge",
                "solana_addresses": [
                    "SLTyZpBEN9GNyGECiTLZXgsHRfbcey8bSoyX4NKtXeA"
                ],
                "supported_chains": ["ethereum"]
            }
        }
        
        # High-risk patterns to look for
        self.risk_patterns = {
            "amount_splitting": {
                "description": "Funds split into multiple smaller transactions before bridging",
                "risk_score": 0.7
            },
            "rapid_bridging": {
                "description": "Funds quickly moved to another chain after receiving",
                "risk_score": 0.6
            },
            "multiple_hops": {
                "description": "Funds moved across three or more chains in short time",
                "risk_score": 0.8
            },
            "round_amounts": {
                "description": "Perfectly round amounts (e.g., exactly 10 ETH, 100 SOL)",
                "risk_score": 0.5
            },
            "sanctioned_chain_route": {
                "description": "Route includes chains with weak AML enforcement",
                "risk_score": 0.9
            }
        }
        
        # Set of sanctioned or high-risk addresses
        self.sanctioned_addresses = set()
        # Try loading sanctioned addresses from Range client if available
        if self.range_client:
            try:
                self._load_sanctioned_addresses()
            except Exception as e:
                logging.warning(f"Failed to load sanctioned addresses: {e}")
        
        logging.info(f"BridgeCollector initialized with {len(self.known_bridges)} known bridge types")
    
    def _load_sanctioned_addresses(self):
        """Load sanctioned addresses from Range API if available."""
        # This would be implemented using the Range API's risk endpoint
        # For now, we'll use a simplified placeholder implementation
        if self.range_client:
            # Example implementation - would be replaced with actual API call
            self.sanctioned_addresses = set([
                "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin",  # Example sanctioned address
                # Add other known sanctioned addresses here
            ])
    
    async def fetch_bridge_transactions(self, days_back: int = 7, limit_per_bridge: int = 500) -> Dict[str, List[Dict]]:
        """
        Fetch transactions for all known bridges within a time period.
        
        Args:
            days_back: Number of days to look back
            limit_per_bridge: Maximum transactions to fetch per bridge address
            
        Returns:
            Dictionary with bridge name as key and list of transactions as value
        """
        if not self.helius_client:
            raise ValueError("HeliusClient is required for fetching bridge transactions")
        
        bridge_transactions = {}
        
        for bridge_id, bridge_info in self.known_bridges.items():
            bridge_transactions[bridge_id] = []
            
            for address in bridge_info["solana_addresses"]:
                try:
                    logging.info(f"Fetching transactions for bridge: {bridge_info['name']} ({address})")
                    txs = await self._fetch_transactions_paginated(address, limit_per_bridge)
                    
                    # Filter transactions by date if we have timestamp info
                    cutoff_time = int((datetime.now() - timedelta(days=days_back)).timestamp())
                    recent_txs = [tx for tx in txs if tx.get("blockTime", 0) >= cutoff_time]
                    
                    bridge_transactions[bridge_id].extend(recent_txs)
                    logging.info(f"Fetched {len(recent_txs)} recent transactions for {bridge_info['name']}")
                    
                except Exception as e:
                    logging.error(f"Error fetching transactions for {bridge_info['name']} ({address}): {e}")
        
        return bridge_transactions
    
    async def _fetch_transactions_paginated(self, address: str, limit_total: int = 500) -> List[Dict]:
        """Helper method to fetch transactions with pagination."""
        all_signatures = []
        last_signature = None
        max_pages = (limit_total // 100) + 1
        pages = 0
        
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
                await asyncio.sleep(0.1)  # Rate limit
                
            except Exception as e:
                logging.warning(f"Error fetching signatures for {address}: {e}")
                break
        
        # Fetch transaction details
        transaction_details = []
        
        # Process in smaller batches to avoid overwhelming the API
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
                        tx_response = self.helius_client.get_transaction(sig_info['signature'])
                        if tx_response and tx_response.get("result"):
                            transaction_details.append(tx_response.get("result"))
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
            await asyncio.sleep(0.5)
        
        return transaction_details
    
    async def analyze_bridge_activity(self, days_back: int = 7) -> Dict:
        """
        Analyze bridge activity to detect potential money laundering patterns.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Dictionary with analysis results
        """
        results = {
            "bridge_summary": {},
            "suspicious_transactions": [],
            "cross_chain_routes": [],
            "risk_scores": {},
            "error": None
        }
        
        try:
            # Fetch bridge transactions
            bridge_txs = await self.fetch_bridge_transactions(days_back=days_back)
            
            # Analyze each bridge
            for bridge_id, transactions in bridge_txs.items():
                bridge_info = self.known_bridges[bridge_id]
                
                # Summarize bridge activity
                bridge_summary = {
                    "name": bridge_info["name"],
                    "transaction_count": len(transactions),
                    "volume_estimate": 0.0,  # Will calculate this
                    "supported_chains": bridge_info["supported_chains"],
                    "most_active_chains": []  # Will calculate this
                }
                
                # Calculate volume and extract suspicious patterns
                suspicious_txs, volume = await self._analyze_bridge_transactions(bridge_id, transactions)
                bridge_summary["volume_estimate"] = volume
                results["suspicious_transactions"].extend(suspicious_txs)
                
                # Add to summary
                results["bridge_summary"][bridge_id] = bridge_summary
            
            # Track cross-chain routes for high-risk addresses
            if self.range_client:
                # This would use Range client to track cross-chain movements
                cross_chain_routes = await self._track_cross_chain_routes(results["suspicious_transactions"])
                results["cross_chain_routes"] = cross_chain_routes
            
        except Exception as e:
            logging.error(f"Error analyzing bridge activity: {e}")
            results["error"] = str(e)
        
        return results
    
    async def _analyze_bridge_transactions(self, bridge_id: str, transactions: List[Dict]) -> Tuple[List[Dict], float]:
        """
        Analyze bridge transactions to identify suspicious patterns and calculate volume.
        
        Args:
            bridge_id: ID of the bridge being analyzed
            transactions: List of bridge transactions
            
        Returns:
            Tuple of (suspicious transactions list, total volume)
        """
        from scripts.analysis.network_builder import NetworkBuilder
        
        suspicious_txs = []
        total_volume = 0.0
        network_builder = NetworkBuilder(helius_client=self.helius_client)
        
        # Group transactions by sender address to detect patterns
        sender_txs = {}
        
        for tx in transactions:
            # Extract transfers from transaction
            transfers = network_builder._extract_transfers(tx)
            
            # Process each transfer
            for transfer in transfers:
                source = transfer.get('source')
                destination = transfer.get('destination')
                amount = transfer.get('amount', 0)
                
                # Skip if source or destination is missing
                if not source or not destination:
                    continue
                
                # Add to sender's transaction history
                if source not in sender_txs:
                    sender_txs[source] = []
                
                sender_txs[source].append({
                    "tx_hash": tx.get("transaction", {}).get("signatures", [""])[0],
                    "blockTime": tx.get("blockTime", 0),
                    "destination": destination,
                    "amount": amount,
                    "mint": transfer.get("mint", "SOL"),
                    "bridge_id": bridge_id
                })
                
                # Add to total volume (simplified conversion)
                token_value = float(amount) / 1e9  # Simplified - would need token-specific decimal handling
                total_volume += token_value
        
        # Analyze patterns for each sender
        for sender, txs in sender_txs.items():
            # Skip if only one transaction
            if len(txs) < 2:
                continue
            
            # Sort by block time
            txs.sort(key=lambda x: x["blockTime"])
            
            # Check for amount splitting pattern
            if self._detect_amount_splitting(txs):
                suspicious_txs.extend(txs)
                continue
            
            # Check for rapid bridging
            if self._detect_rapid_bridging(txs):
                suspicious_txs.extend(txs)
                continue
            
            # Check for sanctioned addresses
            if sender in self.sanctioned_addresses:
                suspicious_txs.extend(txs)
                continue
            
            # Check for round amounts
            for tx in txs:
                if self._is_round_amount(tx["amount"]):
                    suspicious_txs.append(tx)
        
        return suspicious_txs, total_volume
    
    def _detect_amount_splitting(self, transactions: List[Dict]) -> bool:
        """
        Detect if a user is splitting amounts into multiple smaller transactions.
        This is a common money laundering pattern to avoid detection.
        
        Args:
            transactions: List of transactions for a single sender
            
        Returns:
            True if splitting pattern detected, False otherwise
        """
        # Simple detection: Multiple similar-sized transactions in short time
        if len(transactions) < 3:
            return False
        
        # Group transactions by time windows (e.g. 1 hour)
        time_windows = {}
        window_size = 3600  # 1 hour in seconds
        
        for tx in transactions:
            window = tx["blockTime"] // window_size
            if window not in time_windows:
                time_windows[window] = []
            time_windows[window].append(tx)
        
        # Check if any time window has multiple similar-sized transactions
        for window, window_txs in time_windows.items():
            if len(window_txs) < 3:
                continue
            
            # Calculate average and check if transactions are similar in size
            amounts = [tx["amount"] for tx in window_txs]
            avg_amount = sum(amounts) / len(amounts)
            similar_count = sum(1 for amount in amounts if 0.8 <= amount/avg_amount <= 1.2)
            
            if similar_count >= 3:
                return True
        
        return False
    
    def _detect_rapid_bridging(self, transactions: List[Dict]) -> bool:
        """
        Detect if funds are quickly moved after receiving.
        
        Args:
            transactions: List of transactions for a single sender
            
        Returns:
            True if rapid bridging detected, False otherwise
        """
        # Simple version: check if time between first and last transaction is short
        if len(transactions) < 2:
            return False
        
        first_tx_time = transactions[0]["blockTime"]
        last_tx_time = transactions[-1]["blockTime"]
        
        # If all transactions happened within a short window (e.g., 10 minutes)
        if last_tx_time - first_tx_time < 600:  # 10 minutes in seconds
            return True
        
        return False
    
    def _is_round_amount(self, amount: int) -> bool:
        """
        Check if an amount is suspiciously round (e.g., exactly 10 SOL, 100 SOL).
        
        Args:
            amount: Transaction amount in smallest units
            
        Returns:
            True if amount is suspiciously round, False otherwise
        """
        # Convert to SOL (or other major unit)
        major_unit = amount / 1e9  # For SOL, adjust for other tokens
        
        # Check if it's a round number
        if major_unit.is_integer():
            # More suspicious if it's a power of 10
            if major_unit in [1, 10, 100, 1000, 10000]:
                return True
            # Or a common round number
            if major_unit in [5, 20, 50, 200, 500]:
                return True
        
        return False
    
    async def _track_cross_chain_routes(self, suspicious_txs: List[Dict]) -> List[Dict]:
        """
        Track cross-chain routes for suspicious transactions.
        
        Args:
            suspicious_txs: List of suspicious bridge transactions
            
        Returns:
            List of cross-chain routes
        """
        cross_chain_routes = []
        
        # This method would use Range API to track cross-chain activity
        # For now, we'll return a simplified placeholder
        if not self.range_client:
            return cross_chain_routes
        
        # Group by sender
        senders = {tx["source"] for tx in suspicious_txs if "source" in tx}
        
        for sender in senders:
            try:
                # This would be implemented using Range's cross-chain explorer API
                if hasattr(self.range_client, 'get_transactions_by_address'):
                    cross_chain_txs = self.range_client.get_transactions_by_address(sender)
                    
                    # Process and extract routes
                    # (simplified placeholder implementation)
                    route = {
                        "address": sender,
                        "route": ["solana", "ethereum", "bsc"],  # Example route
                        "total_value_usd": 10000,  # Example value
                        "risk_score": 0.85,  # Example risk score
                        "transactions": []  # Would contain actual transaction hashes
                    }
                    
                    cross_chain_routes.append(route)
            except Exception as e:
                logging.warning(f"Failed to track cross-chain route for {sender}: {e}")
        
        return cross_chain_routes
    
    async def get_high_risk_bridge_routes(self, days_back: int = 30, min_risk_score: float = 0.7) -> List[Dict]:
        """
        Get high-risk bridge routes that may be used for money laundering.
        
        Args:
            days_back: Number of days to analyze
            min_risk_score: Minimum risk score to include
            
        Returns:
            List of high-risk routes
        """
        # Full implementation would analyze actual transaction data
        # For now, return a simplified example
        high_risk_routes = [
            {
                "route_id": "route-1",
                "path": ["solana", "ethereum", "bsc", "tron"],
                "risk_score": 0.92,
                "volume_usd": 1500000,
                "transaction_count": 37,
                "common_addresses": [
                    "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin",
                    "0x1234567890123456789012345678901234567890"
                ],
                "detection_criteria": ["multiple_hops", "sanctioned_chain_route"]
            },
            {
                "route_id": "route-2",
                "path": ["solana", "ethereum", "arbitrum", "optimism"],
                "risk_score": 0.75,
                "volume_usd": 870000,
                "transaction_count": 24,
                "common_addresses": [
                    "VinesRG7K3ubzKLbxXz197c1RHV3cACkvGr9Zca7BSw",
                    "0xabcdef1234567890abcdef1234567890abcdef12"
                ],
                "detection_criteria": ["rapid_bridging", "amount_splitting"]
            }
        ]
        
        return high_risk_routes
    
    def get_bridge_tokens_flow(self) -> Dict:
        """
        Get statistics on token flow across bridges.
        
        Returns:
            Dictionary with token flow statistics
        """
        # This would be implemented with actual data analysis in a full implementation
        # Returning placeholder data for now
        token_flows = {
            "USDC": {
                "solana_to_ethereum": 35000000,
                "ethereum_to_solana": 28000000,
                "solana_to_bsc": 12000000,
                "bsc_to_solana": 9000000,
            },
            "USDT": {
                "solana_to_ethereum": 42000000,
                "ethereum_to_solana": 31000000,
                "solana_to_bsc": 15000000,
                "bsc_to_solana": 11000000,
            },
            "SOL": {
                "solana_to_ethereum": 8500000,
                "ethereum_to_solana": 7200000,
            }
        }
        
        return token_flows
