import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from decimal import Decimal

# Assuming HeliusClient has methods to parse transactions or provides parsed data
# If not, specific parsing logic for DEX instructions would be needed here.

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SandwichDetector:
    """
    Detects potential sandwich attacks on Solana DEXs using heuristics.
    Note: This is a simplified detector and may not capture all attacks accurately.
    """

    def __init__(self, helius_client=None):
        """
        Initialize the SandwichDetector.

        Args:
            helius_client: Helius API client instance.
        """
        if not helius_client:
            raise ValueError("HeliusClient is required for SandwichDetector")
        self.helius_client = helius_client
        # Known DEX program IDs (add more as needed)
        self.dex_programs = {
            "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": "Raydium AMM V4",
            "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4": "Jupiter Aggregator V6",
            "9W959DqEETiGZoccpwsBqyK9XMSoMViNBPwzCbXKmnUy": "Orca Aquafarm", # Example, check actual Orca swap program
            # Add other relevant DEX program IDs
        }

    def detect_sandwich_attacks(self, time_window_minutes: int = 10, limit_per_dex: int = 500) -> List[Dict]:
        """
        Detect potential sandwich attacks within a recent time window.
        Focuses on analyzing transaction sequences around potential victim swaps.
        Uses SandwichCollector to fetch and prepare data for analysis.
        """
        from scripts.collectors.sandwich_collector import SandwichCollector
        
        logging.info(f"Starting enhanced sandwich attack detection for the last {time_window_minutes} minutes...")
        detected_attacks = []
        processed_victim_signatures = set() # Avoid re-analyzing the same victim tx
        
        # Initialize the collector
        sandwich_collector = SandwichCollector(self.helius_client)
        
        # 1. Identify potential victim transactions using the collector
        potential_victims = sandwich_collector.collect_potential_victim_txs(time_window_minutes, limit_per_dex)
        logging.info(f"Identified {len(potential_victims)} potential victim transactions to analyze.")

        # 2. Analyze transactions around each potential victim
        for victim_tx_info in potential_victims:
            victim_sig = victim_tx_info['signature']
            if victim_sig in processed_victim_signatures:
                continue

            logging.debug(f"Analyzing potential victim transaction: {victim_sig}")
            try:
                # Fetch victim transaction details through the collector
                victim_tx_detail = sandwich_collector.fetch_transaction_details(victim_sig)
                if not victim_tx_detail or victim_tx_detail.get("meta", {}).get("err"):
                    continue # Skip failed or unavailable txs

                processed_victim_signatures.add(victim_sig)
                victim_slot = victim_tx_detail.get("slot")
                victim_block_time = victim_tx_detail.get("blockTime")

                # --- Enhanced Sandwich Detection Logic ---
                # a. Extract swap details from the victim transaction.
                victim_swaps = self._extract_swaps_from_tx(victim_tx_detail)
                if not victim_swaps: continue

                # Assume the primary swap for the victim
                victim_swap = victim_swaps[0] # Simplification
                victim_signer = victim_swap.get("signer")
                victim_pool = victim_swap.get("pool_id") # Needs robust extraction

                # This requires fetching and analyzing neighboring transactions, which is complex.
                # Let's refine the single-transaction analysis first using balance changes.
                potential_attack = self._analyze_tx_with_balance_changes(victim_tx_detail, victim_swap)
                if potential_attack:
                    detected_attacks.append(potential_attack)

                time.sleep(0.1) # Basic rate limiting

            except Exception as analysis_err:
                logging.warning(f"Failed to analyze victim transaction {victim_sig}: {analysis_err}")

        logging.info(f"Detected {len(detected_attacks)} potential sandwich attacks.")
        return detected_attacks

    def _analyze_tx_with_balance_changes(self, tx_detail: Dict, victim_swap: Dict) -> Optional[Dict]:
        """
        Analyzes a single transaction using token balance changes for sandwich patterns.
        Assumes the transaction *might* contain the full sandwich (front-run, victim, back-run).
        """
        meta = tx_detail.get("meta", {})
        instructions = tx_detail.get("transaction", {}).get("message", {}).get("instructions", [])
        inner_instructions = meta.get("innerInstructions", [])
        pre_balances = meta.get("preTokenBalances", [])
        post_balances = meta.get("postTokenBalances", [])
        account_keys = tx_detail.get("transaction", {}).get("message", {}).get("accountKeys", [])

        # Combine instructions for easier parsing
        all_instructions = instructions + [
            inner_ix for outer_ix in inner_instructions for inner_ix in outer_ix.get("instructions", [])
        ]

        # 1. Extract all swaps within this transaction
        swaps = self._extract_swaps_from_tx(tx_detail) # Use the improved extractor
        if len(swaps) < 2: # Need at least a potential front/back run around *some* swap
            return None

        # 2. Identify potential attacker and victim swaps based on sequence and signers
        #    This requires robust swap extraction including signer info.
        #    Heuristic: Look for pairs of swaps involving the same pool, different directions.
        for i, swap1 in enumerate(swaps):
            for j, swap2 in enumerate(swaps):
                if i >= j: continue # Ensure swap1 happens before swap2

                # Check if swaps involve the same pool and are reverse operations by the same signer
                if (swap1.get("pool_id") == swap2.get("pool_id") and
                    swap1.get("signer") == swap2.get("signer") and
                    swap1.get("input_token_mint") == swap2.get("output_token_mint") and
                    swap1.get("output_token_mint") == swap2.get("input_token_mint")):

                    attacker_signer = swap1.get("signer")
                    pool_id = swap1.get("pool_id")
                    token_a_mint = swap1.get("input_token_mint") # Token attacker sells in back-run
                    token_b_mint = swap1.get("output_token_mint") # Token attacker buys in front-run

                    # Check if there's another swap between swap1 and swap2 by a different signer (victim)
                    victim_found = False
                    potential_victim_swap = None
                    for k, mid_swap in enumerate(swaps):
                        if k > i and k < j:
                            if mid_swap.get("pool_id") == pool_id and mid_swap.get("signer") != attacker_signer:
                                victim_found = True
                                potential_victim_swap = mid_swap
                                break # Found a potential victim swap in between

                    if victim_found:
                        # 3. Calculate Profit using Balance Changes
                        profit_amount, profit_token_mint = self._calculate_profit(
                            attacker_signer, token_a_mint, token_b_mint, pre_balances, post_balances, account_keys
                        )

                        if profit_amount > 0:
                            # 4. Estimate Slippage (Hard without expected price, use proxy)
                            # Compare victim's execution price vs price before front-run (if possible)
                            slippage_pct_est = self._estimate_slippage(potential_victim_swap, swaps) # Placeholder

                            # Convert profit to SOL/USD (requires price feed)
                            profit_sol_est, profit_usd_est = self._get_profit_value(profit_amount, profit_token_mint, tx_detail.get("blockTime"))

                            dex_name = self.dex_programs.get(tx_detail.get("transaction", {}).get("message", {}).get("instructions", [{}])[0].get("programId"), "Unknown DEX")

                            attack_info = {
                                "timestamp": datetime.fromtimestamp(tx_detail.get("blockTime", 0)).isoformat() + "Z",
                                "dex": dex_name,
                                "token_pair": f"{potential_victim_swap.get('input_token_symbol', '?')}/{potential_victim_swap.get('output_token_symbol', '?')}", # Needs symbol mapping
                                "attacker_address": attacker_signer,
                                "victim_address": potential_victim_swap.get("signer"),
                                "victim_tx": tx_detail.get("transaction", {}).get("signatures", [None])[0],
                                # In this single-tx model, front/back are same tx
                                "front_tx": tx_detail.get("transaction", {}).get("signatures", [None])[0],
                                "back_tx": tx_detail.get("transaction", {}).get("signatures", [None])[0],
                                "profit_sol": profit_sol_est,
                                "profit_usd": profit_usd_est,
                                "slippage_pct": slippage_pct_est,
                                "block_time": tx_detail.get("blockTime"),
                                "slot": tx_detail.get("slot")
                            }
                            logging.info(f"Potential sandwich detected in tx {attack_info['victim_tx']} by {attacker_signer}")
                            return attack_info
        return None

    def _extract_swaps_from_tx(self, tx_detail: Dict) -> List[Dict]:
        """
        Extracts swap information from transaction details, including inner instructions.
        Requires specific parsers for different DEX programs (Raydium, Orca, Jupiter).
        """
        swaps = []
        meta = tx_detail.get("meta", {})
        instructions = tx_detail.get("transaction", {}).get("message", {}).get("instructions", [])
        inner_instructions = meta.get("innerInstructions", [])
        account_keys = tx_detail.get("transaction", {}).get("message", {}).get("accountKeys", [])
        log_messages = meta.get("logMessages", [])
        # Extract token balances for enrichment
        pre_balances = meta.get("preTokenBalances", [])
        post_balances = meta.get("postTokenBalances", [])

        # Combine instructions
        instruction_groups = [(instructions, None)] # Outer instructions
        for inner_ix_group in inner_instructions:
             instruction_groups.append((inner_ix_group.get("instructions", []), inner_ix_group.get("index")))

        for ix_list, outer_ix_index in instruction_groups:
            for ix in ix_list:
                program_id = account_keys[ix.get("programIdIndex")]
                dex_name = self.dex_programs.get(program_id)

                # Placeholder: Need actual parsing logic per DEX
                # Example for Raydium AMM Swap (Base V4) - Instruction 9
                if dex_name == "Raydium AMM V4" and ix.get("data") and ix["data"].startswith("09"): # Check instruction discriminator
                    try:
                        # Decode Raydium instruction data (requires borsh or similar)
                        # Extract accounts involved (pool, authority, user accounts, token accounts)
                        # Extract amounts from log messages or balance changes if needed
                        # Identify signer (usually the fee payer or specific account in ix)
                        signer = account_keys[tx_detail.get("transaction", {}).get("message", {}).get("accountKeys",[]).index(tx_detail.get("transaction",{}).get("message",{}).get("feePayer"))] # Simplification: assume fee payer is signer

                        # Placeholder data - replace with actual parsed values
                        swap_info = {
                            "program": dex_name,
                            "program_id": program_id,
                            "signer": signer, # Needs accurate identification
                            "pool_id": account_keys[ix.get("accounts", [])[1]], # Example index for pool ID
                            "input_token_mint": "MintA", # Extract from pool info or accounts
                            "output_token_mint": "MintB", # Extract from pool info or accounts
                            "input_token_symbol": "TOKENA", # Needs mapping
                            "output_token_symbol": "TOKENB", # Needs mapping
                            "input_amount": 100, # Extract from instruction data or logs
                            "output_amount": 50, # Extract from instruction data or logs
                        }
                        swaps.append(swap_info)
                    except Exception as parse_err:
                        logging.debug(f"Failed to parse Raydium swap instruction: {parse_err}")

                # Add parsers for Orca, Jupiter Route, etc.
                # Jupiter parsing is complex due to routing across multiple pools.

        # Enhance swaps with amount details from balance changes if possible
        swaps = self._enrich_swaps_with_balance_changes(swaps, pre_balances, post_balances, account_keys)

        return swaps

    def _enrich_swaps_with_balance_changes(self, swaps: List[Dict], pre_balances: List[Dict], post_balances: List[Dict], account_keys: List[str]) -> List[Dict]:
        """Attempt to add input/output amounts using token balance changes."""
        if not swaps or not pre_balances or not post_balances:
            return swaps
        
        # Create lookup dictionaries for pre and post balances by mint and owner
        pre_balances_map = {}  # {mint: {owner: {account_idx: amount}}}
        post_balances_map = {}  # {mint: {owner: {account_idx: amount}}}
        
        # Map pre balances
        for bal in pre_balances:
            mint = bal.get("mint")
            owner = bal.get("owner")
            account_idx = bal.get("accountIndex")
            amount = bal.get("uiTokenAmount", {}).get("uiAmount", 0)
            
            if not mint or not owner:
                continue
                
            if mint not in pre_balances_map:
                pre_balances_map[mint] = {}
            if owner not in pre_balances_map[mint]:
                pre_balances_map[mint][owner] = {}
            
            pre_balances_map[mint][owner][account_idx] = amount
        
        # Map post balances
        for bal in post_balances:
            mint = bal.get("mint")
            owner = bal.get("owner")
            account_idx = bal.get("accountIndex")
            amount = bal.get("uiTokenAmount", {}).get("uiAmount", 0)
            
            if not mint or not owner:
                continue
                
            if mint not in post_balances_map:
                post_balances_map[mint] = {}
            if owner not in post_balances_map[mint]:
                post_balances_map[mint][owner] = {}
            
            post_balances_map[mint][owner][account_idx] = amount
        
        # Enrich each swap with actual amounts based on balance changes
        for i, swap in enumerate(swaps):
            signer = swap.get("signer")
            input_mint = swap.get("input_token_mint")
            output_mint = swap.get("output_token_mint")
            
            if not signer or not input_mint or not output_mint:
                continue
            
            # Find balance changes for input token (negative change for signer)
            input_amount = 0
            if input_mint in pre_balances_map and signer in pre_balances_map[input_mint]:
                for idx, pre_amount in pre_balances_map[input_mint][signer].items():
                    post_amount = post_balances_map.get(input_mint, {}).get(signer, {}).get(idx, 0)
                    diff = post_amount - pre_amount
                    if diff < 0:  # Signer spent this token (negative change)
                        input_amount -= diff  # Convert negative diff to positive amount
            
            # Find balance changes for output token (positive change for signer)
            output_amount = 0
            if output_mint in post_balances_map and signer in post_balances_map[output_mint]:
                for idx, post_amount in post_balances_map[output_mint][signer].items():
                    pre_amount = pre_balances_map.get(output_mint, {}).get(signer, {}).get(idx, 0)
                    diff = post_amount - pre_amount
                    if diff > 0:  # Signer received this token (positive change)
                        output_amount += diff
            
            # Update swap with actual amounts if found
            if input_amount > 0:
                swaps[i]["input_amount"] = input_amount
                logging.debug(f"Updated swap input amount: {input_amount}")
            
            if output_amount > 0:
                swaps[i]["output_amount"] = output_amount
                logging.debug(f"Updated swap output amount: {output_amount}")
            
            # Calculate price impact if both amounts are available
            if input_amount > 0 and output_amount > 0:
                swaps[i]["execution_price"] = output_amount / input_amount
                logging.debug(f"Calculated execution price: {swaps[i]['execution_price']}")
        
        return swaps

    def _calculate_profit(self, attacker_signer: str, token_a_mint: str, token_b_mint: str, pre_balances: List[Dict], post_balances: List[Dict], account_keys: List[str]) -> tuple[Decimal, str]:
        """Calculates the attacker's profit in one of the tokens using balance changes."""
        profit_amount = Decimal(0)
        profit_token_mint = None

        attacker_token_accounts = {} # Map mint to attacker's token account address

        # Find attacker's token accounts and initial/final balances
        pre_map = {} # {account_index: {mint: amount_decimal}}
        post_map = {} # {account_index: {mint: amount_decimal}}

        for bal in pre_balances:
            idx = bal.get("accountIndex")
            owner = bal.get("owner")
            mint = bal.get("mint")
            amount = Decimal(bal.get("uiTokenAmount", {}).get("uiAmountString", "0"))
            if owner == attacker_signer:
                 attacker_token_accounts[mint] = account_keys[idx] # Store account address
            if idx not in pre_map: pre_map[idx] = {}
            pre_map[idx][mint] = amount

        for bal in post_balances:
            idx = bal.get("accountIndex")
            mint = bal.get("mint")
            amount = Decimal(bal.get("uiTokenAmount", {}).get("uiAmountString", "0"))
            if idx not in post_map: post_map[idx] = {}
            post_map[idx][mint] = amount

        # Calculate net change for the attacker for both tokens
        change_a = Decimal(0)
        change_b = Decimal(0)

        for idx, mint_balances in post_map.items():
             if account_keys[idx] == attacker_token_accounts.get(token_a_mint): # Attacker's account for token A
                  pre_amount = pre_map.get(idx, {}).get(token_a_mint, 0)
                  post_amount = mint_balances.get(token_a_mint, 0)
                  change_a = post_amount - pre_amount
             if account_keys[idx] == attacker_token_accounts.get(token_b_mint): # Attacker's account for token B
                  pre_amount = pre_map.get(idx, {}).get(token_b_mint, 0)
                  post_amount = mint_balances.get(token_b_mint, 0)
                  change_b = post_amount - pre_amount

        # Determine profit (usually the token they end up with more of)
        if change_a > 0 and change_b < 0: # Gained token A, spent token B
            profit_amount = change_a
            profit_token_mint = token_a_mint
        elif change_b > 0 and change_a < 0: # Gained token B, spent token A
            profit_amount = change_b
            profit_token_mint = token_b_mint
        # Handle cases where profit might be in SOL (fees) or other complex scenarios if needed

        return profit_amount, profit_token_mint

    def _estimate_slippage(self, victim_swap: Dict, all_swaps_in_tx: List[Dict]) -> float:
        """Estimates slippage percentage suffered by the victim."""
        # Very difficult without knowing the expected price or pool state before front-run.
        # Proxy: Compare victim's rate vs attacker's back-run rate (if available and comparable).
        # Or, if pool state is logged, calculate price impact of front-run.
        # Placeholder: Return a fixed estimate or calculate based on available swap amounts.
        try:
            victim_input = Decimal(victim_swap.get("input_amount", 0))
            victim_output = Decimal(victim_swap.get("output_amount", 0))
            if victim_input > 0:
                victim_rate = victim_output / victim_input
                # Find attacker's front-run swap for comparison (if possible)
                # ... logic to find front-run swap ...
                # If found, compare rates. This is complex.
                return 1.5 # Placeholder value
            return 0.0
        except:
            return 0.0 # Return 0 if calculation fails

    def _get_profit_value(self, amount: Decimal, mint: str, block_time: int) -> tuple[float, float]:
        """Get SOL and USD value of the profit amount using price feeds."""
        # Requires integration with a price oracle or API (e.g., Jupiter price API, Birdeye)
        # Fetch price of `mint` in SOL and USD around `block_time`.
        # Placeholder values
        price_in_sol = 0.01 # Example: 1 profit token = 0.01 SOL
        price_in_usd = 0.60 # Example: 1 profit token = $0.60

        profit_sol = float(amount * Decimal(price_in_sol))
        profit_usd = float(amount * Decimal(price_in_usd))
        return profit_sol, profit_usd
