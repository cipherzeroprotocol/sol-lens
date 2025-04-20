import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

class SandwichCollector:
    """
    Collector for data related to potential sandwich attacks on DEXs.
    Responsible for fetching and pre-processing transaction data from DEXs.
    """
    
    def __init__(self, helius_client=None):
        """
        Initialize the SandwichCollector.
        
        Args:
            helius_client: Helius API client instance for fetching transaction data.
        """
        if not helius_client:
            raise ValueError("HeliusClient is required for SandwichCollector")
        self.helius_client = helius_client
        
        # Known DEX program IDs (add more as needed)
        self.dex_programs = {
            "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": "Raydium AMM V4",
            "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4": "Jupiter Aggregator V6", 
            "9W959DqEETiGZoccpwsBqyK9XMSoMViNBPwzCbXKmnUy": "Orca Aquafarm",
            "CURVGoZn8zycx6FXwwevgBTB2gVvdbGTEpvMJDbgs2t4": "Orca Whirlpools",
            "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": "Orca Legacy Pools",
            "srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX": "Openbook V1",
            "22Y43yTVxuUkoRKdm9thyRhQ3SdgQS7c7kB6UNCiaczD": "Serum Swap",
          
        }
        
        logging.info(f"SandwichCollector initialized with {len(self.dex_programs)} DEX programs")
    
    def collect_potential_victim_txs(self, time_window_minutes: int = 10, limit_per_dex: int = 500) -> List[Dict]:
        """
        Collect recent transactions from DEXs that could be potential victims of sandwich attacks.
        
        Args:
            time_window_minutes: Time window in minutes to look back for transactions
            limit_per_dex: Maximum number of transactions to retrieve per DEX
            
        Returns:
            List of transaction signatures with metadata
        """
        potential_victims = []
        cutoff_time = time.time() - (time_window_minutes * 60)
        
        for program_id, dex_name in self.dex_programs.items():
            try:
                logging.info(f"Collecting transactions from {dex_name} ({program_id})")
                signatures_result = self.helius_client.get_signatures_for_address(program_id, limit=limit_per_dex)
                signatures = signatures_result.get("result", [])
                
                # Filter recent, successful transactions
                recent_signatures = [s for s in signatures if s.get('blockTime', 0) > cutoff_time and not s.get('err')]
                
                # Add DEX name to each signature for easier identification
                for sig in recent_signatures:
                    sig['dex_name'] = dex_name
                    sig['program_id'] = program_id
                
                potential_victims.extend(recent_signatures)
                logging.info(f"Found {len(recent_signatures)} recent signatures for {dex_name}")
                
                # Basic rate limiting
                time.sleep(0.2)
                
            except Exception as e:
                logging.error(f"Error fetching transactions from {dex_name}: {e}")
        
        # Deduplicate in case some transactions appeared in multiple DEXs
        unique_victims = {v['signature']: v for v in potential_victims}
        result = list(unique_victims.values())
        
        logging.info(f"Collected {len(result)} unique potential victim transactions across all DEXs")
        return result
    
    def fetch_transaction_details(self, signature: str) -> Optional[Dict]:
        """
        Fetch detailed transaction data for a given signature.
        
        Args:
            signature: Transaction signature
            
        Returns:
            Transaction details or None if not found/error
        """
        try:
            tx_response = self.helius_client.get_transaction(signature)
            if not tx_response or not tx_response.get("result"):
                logging.warning(f"No data returned for transaction {signature}")
                return None
            
            return tx_response.get("result")
            
        except Exception as e:
            logging.error(f"Error fetching transaction {signature}: {e}")
            return None
    
    def fetch_block_transactions(self, slot: int) -> List[Dict]:
        """
        Fetch all transactions in a specific block/slot to find related transactions.
        
        Args:
            slot: Block slot number
            
        Returns:
            List of transaction details in the block
        """
        try:
            block_response = self.helius_client.get_block(slot)
            if not block_response or not block_response.get("result"):
                logging.warning(f"No data returned for block {slot}")
                return []
            
            transactions = block_response.get("result", {}).get("transactions", [])
            logging.info(f"Fetched {len(transactions)} transactions from block {slot}")
            return transactions
            
        except Exception as e:
            logging.error(f"Error fetching block {slot}: {e}")
            return []
    
    def collect_swap_batch_data(self, time_window_minutes: int = 10, batch_size: int = 50) -> Dict:
        """
        Collect a batch of data for sandwich attack analysis, including potential victims and related transactions.
        
        Args:
            time_window_minutes: Time window to look back
            batch_size: Number of potential victim transactions to analyze deeply
            
        Returns:
            Dictionary containing collected data
        """
        # Step 1: Get potential victim transactions
        potential_victims = self.collect_potential_victim_txs(time_window_minutes)
        
        # Step 2: Sample a batch for detailed analysis
        analysis_batch = potential_victims[:batch_size] if len(potential_victims) > batch_size else potential_victims
        
        # Step 3: Fetch transaction details for the batch
        tx_details = []
        for victim in analysis_batch:
            details = self.fetch_transaction_details(victim['signature'])
            if details:
                # Merge DEX info from the signature data
                details['dex_name'] = victim.get('dex_name', 'Unknown DEX')
                tx_details.append(details)
            
            # Rate limiting
            time.sleep(0.1)
        
        # Step 4: Get associated block data for a smaller subset if needed
        # This is expensive, so we might limit it further
        block_tx_details = {}
        sample_for_blocks = tx_details[:10]  # Analyze blocks for just a few transactions
        
        for tx in sample_for_blocks:
            slot = tx.get("slot")
            if slot and slot not in block_tx_details:
                block_transactions = self.fetch_block_transactions(slot)
                block_tx_details[slot] = block_transactions
                time.sleep(0.5)  # More aggressive rate limiting for block requests
        
        return {
            "potential_victims_count": len(potential_victims),
            "analyzed_transactions": tx_details,
            "block_data": block_tx_details
        }
