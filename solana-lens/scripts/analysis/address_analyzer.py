import json
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import time
import logging # Use logging for better control

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AddressAnalyzer:
    """
    Analyzer for detecting suspicious patterns in blockchain addresses.
    
    This class provides methods to analyze addresses for money laundering,
    address poisoning, and other suspicious activities.
    """
    
    def __init__(self, range_client=None, helius_client=None, rugcheck_client=None, vybe_client=None):
        """
        Initialize the AddressAnalyzer.
        
        Args:
            range_client: Range API client
            helius_client: Helius API client
            rugcheck_client: RugCheck API client
            vybe_client: Vybe API client
        """
        self.range_client = range_client
        self.helius_client = helius_client
        self.rugcheck_client = rugcheck_client
        self.vybe_client = vybe_client
    
    def analyze_address(self, address: str) -> Dict:
        """
        Perform comprehensive analysis of an address.
        
        Args:
            address (str): The address to analyze
            
        Returns:
            Dict: Analysis results
        """
        results = {
            "address": address,
            "timestamp": datetime.now().isoformat(),
            "risk_assessment": {},
            "activity_patterns": {},
            "entity_information": {},
            "counterparty_analysis": {},
            "token_holdings": {},
            "transaction_summary": {}
        }
        
        # Get risk assessment if Range client is available
        if self.range_client:
            try:
                risk_data = self.range_client.get_address_risk_score(address)
                results["risk_assessment"] = {
                    "risk_score": risk_data.get("riskScore", 0), # Adjusted key based on potential API response
                    "risk_level": risk_data.get("riskLevel", "unknown"), # Adjusted key
                    "risk_factors": risk_data.get("factors", []) # Adjusted key
                }
                logging.info(f"Range risk assessment for {address}: Score {results['risk_assessment'].get('risk_score')}")
            except Exception as e:
                logging.error(f"Error getting Range risk assessment for {address}: {e}")
                results["risk_assessment"] = {"error": str(e)}
        else:
            logging.warning("Range client not available for risk assessment.")

        # Get entity information if Range client is available
        if self.range_client:
            try:
                address_info = self.range_client.get_address_info(address)
                results["entity_information"] = {
                    "labels": address_info.get("labels", []),
                    "entity": address_info.get("entity", {})
                }
                logging.info(f"Range entity info for {address}: Labels {results['entity_information'].get('labels')}")
            except Exception as e:
                logging.error(f"Error getting Range entity info for {address}: {e}")
                results["entity_information"] = {"error": str(e)}
        else:
            logging.warning("Range client not available for entity information.")

        # Get token holdings if Helius client is available
        if self.helius_client:
            try:
                # Note: Helius might require pagination for large numbers of tokens
                token_accounts = self.helius_client.get_token_accounts_by_owner(address)
                results["token_holdings"] = self._process_token_accounts(token_accounts)
                logging.info(f"Helius token holdings for {address}: Found {results['token_holdings'].get('total_accounts')} token accounts.")
            except Exception as e:
                logging.error(f"Error getting Helius token holdings for {address}: {e}")
                results["token_holdings"] = {"error": str(e)}
        else:
            logging.warning("Helius client not available for token holdings.")

        # Get transaction history summary if Helius client is available
        if self.helius_client:
            try:
                # Note: Helius getSignaturesForAddress is limited (max 1000); pagination needed for full history
                signatures_result = self.helius_client.get_signatures_for_address(address, limit=100) # Limit for example
                signatures = signatures_result.get("result", [])
                results["transaction_summary"] = self._summarize_transactions(signatures)
                logging.info(f"Helius transaction summary for {address}: Found {results['transaction_summary'].get('total_transactions')} recent transactions.")
            except Exception as e:
                logging.error(f"Error getting Helius transaction summary for {address}: {e}")
                results["transaction_summary"] = {"error": str(e)}
        else:
            logging.warning("Helius client not available for transaction summary.")

        # Get counterparty analysis if Range client is available
        if self.range_client:
             try:
                 counterparties_data = self.range_client.get_address_counterparties(address)
                 results["counterparty_analysis"] = self._analyze_counterparties(counterparties_data)
                 logging.info(f"Range counterparty analysis for {address}: Found {results['counterparty_analysis'].get('unique_counterparties')} counterparties.")
             except Exception as e:
                 logging.error(f"Error getting Range counterparties for {address}: {e}")
                 results["counterparty_analysis"] = {"error": str(e)}
        else:
            logging.warning("Range client not available for counterparty analysis.")


        # Detect suspicious patterns using available data
        results["activity_patterns"] = self._detect_suspicious_patterns(address, results)

        return results
    
    def analyze_transaction_flow(self, tx_hash: str) -> Dict:
        """
        Analyze the flow of funds in a transaction.
        
        Args:
            tx_hash (str): Transaction hash
            
        Returns:
            Dict: Analysis of fund flow
        """
        results = {
            "tx_hash": tx_hash,
            "timestamp": datetime.now().isoformat(),
            "transaction_details": {},
            "fund_flow": {},
            "risk_assessment": {},
            "participants": {}
        }
        
        # Get transaction details if Helius client is available
        if self.helius_client:
            try:
                tx_data = self.helius_client.get_transaction(tx_hash)
                if tx_data.get("result"):
                    results["transaction_details"] = self._extract_transaction_details(tx_data)
                    logging.info(f"Helius transaction details fetched for {tx_hash}")
                else:
                    raise ValueError("Transaction not found or error in Helius response")
            except Exception as e:
                logging.error(f"Error getting Helius transaction details for {tx_hash}: {e}")
                results["transaction_details"] = {"error": str(e)}
        else:
            logging.warning("Helius client not available for transaction details.")

        # Get transaction risk if Range client is available
        if self.range_client:
            try:
                risk_data = self.range_client.get_transaction_risk_score(tx_hash)
                results["risk_assessment"] = {
                    "risk_score": risk_data.get("riskScore", 0), # Adjusted key
                    "risk_level": risk_data.get("riskLevel", "unknown"), # Adjusted key
                    "risk_factors": risk_data.get("factors", []) # Adjusted key
                }
                logging.info(f"Range risk assessment for tx {tx_hash}: Score {results['risk_assessment'].get('risk_score')}")
            except Exception as e:
                logging.error(f"Error getting Range risk assessment for tx {tx_hash}: {e}")
                results["risk_assessment"] = {"error": str(e)}
        else:
            logging.warning("Range client not available for transaction risk assessment.")

        # Analyze fund flow from transaction details
        if results["transaction_details"] and "error" not in results["transaction_details"]:
            results["fund_flow"] = self._analyze_fund_flow(results["transaction_details"])
            # Extract information about participants
            results["participants"] = self._extract_participants(results["transaction_details"])
        else:
             results["fund_flow"] = {"error": "Transaction details not available"}
             results["participants"] = {"error": "Transaction details not available"}


        return results
    
    def detect_money_laundering_routes(self, address: str, max_depth: int = 3, days_history: int = 90) -> Dict:
        """
        Detect potential money laundering routes originating from an address.
        
        Args:
            address (str): Starting address
            max_depth (int, optional): Maximum depth to analyze. Defaults to 3.
            days_history (int): How many days of history to consider.
            
        Returns:
            Dict: Detected money laundering routes
        """
        results = {
            "address": address,
            "timestamp": datetime.now().isoformat(),
            "routes": [],
            "risk_score": 0,
            "patterns_detected": []
        }
        
        if not self.helius_client and not self.range_client:
             results["error"] = "Helius or Range client is required for route detection"
             return results

        try:
            transactions = []
            # Prioritize Helius for transaction history if available
            if self.helius_client:
                logging.info(f"Fetching transaction history for {address} using Helius (last {days_history} days approx)...")
                # Need pagination logic here for full history
                signatures_result = self.helius_client.get_signatures_for_address(address, limit=1000) # Max limit
                signatures = signatures_result.get("result", [])
                # Filter signatures by time (approximate)
                cutoff_time = time.time() - days_history * 86400
                recent_signatures = [s['signature'] for s in signatures if s.get('blockTime', 0) > cutoff_time]

                logging.info(f"Found {len(recent_signatures)} recent signatures. Fetching details...")
                # Fetch details for recent transactions (can be slow and rate-limited)
                for sig in recent_signatures:
                    try:
                        tx_detail = self.helius_client.get_transaction(sig)
                        if tx_detail.get("result"):
                            transactions.append(tx_detail["result"])
                        time.sleep(0.1) # Basic rate limiting
                    except Exception as tx_err:
                        logging.warning(f"Failed to fetch details for tx {sig}: {tx_err}")

            # Fallback or supplement with Range if needed (Range might have different data/limits)
            elif self.range_client:
                 logging.info(f"Fetching transaction history for {address} using Range...")
                 # Range API might have different structure/limits
                 tx_data = self.range_client.get_address_transactions(address) # Assuming Range provides sufficient history
                 transactions = tx_data.get("transactions", []) # Adjust based on actual Range response

            if not transactions:
                logging.warning(f"No transactions found for {address} within the specified period.")
                return results

            logging.info(f"Analyzing {len(transactions)} transactions for laundering routes...")
            # Extract routes by pattern matching
            mixer_routes = self._detect_mixer_routes(address, transactions)
            bridge_routes = self._detect_bridge_routes(address, transactions)
            exchange_routes = self._detect_exchange_routes(address, transactions)
            # p2p_routes = self._detect_p2p_routes(address, transactions) # P2P is harder to define, often overlaps

            # Combine all routes
            results["routes"] = mixer_routes + bridge_routes + exchange_routes # + p2p_routes
            logging.info(f"Detected {len(results['routes'])} potential routes.")

            # Calculate overall risk score based on detected routes
            route_scores = [route.get("risk_score", 0) for route in results["routes"]]
            results["risk_score"] = max(route_scores) if route_scores else 0

            # Identify patterns
            results["patterns_detected"] = self._identify_laundering_patterns(results["routes"])

        except Exception as e:
            logging.error(f"Error detecting laundering routes for {address}: {e}")
            results["error"] = str(e)

        return results
    
    def analyze_address_similarity(self, address: str, known_addresses: List[str]) -> Dict:
        """
        Analyze address similarity to detect potential address poisoning.
        
        Args:
            address (str): Address to check
            known_addresses (List[str]): List of known addresses to compare against
            
        Returns:
            Dict: Similarity analysis results
        """
        results = {
            "address": address,
            "timestamp": datetime.now().isoformat(),
            "similar_addresses": [],
            "poisoning_risk": 0
        }
        
        # Check for prefix matching (common in address poisoning)
        for known_address in known_addresses:
            similarity = self._calculate_address_similarity(address, known_address)
            
            if similarity["score"] > 0.7:  # High similarity threshold
                results["similar_addresses"].append({
                    "address": known_address,
                    "similarity_score": similarity["score"],
                    "similarity_type": similarity["type"],
                    "common_prefix_length": similarity["common_prefix_length"],
                    "common_suffix_length": similarity["common_suffix_length"]
                })
        
        # Calculate poisoning risk based on number and score of similar addresses
        if results["similar_addresses"]:
            max_similarity = max([a["similarity_score"] for a in results["similar_addresses"]])
            count_factor = min(1.0, len(results["similar_addresses"]) / 5)  # Cap at 5 similar addresses
            results["poisoning_risk"] = max_similarity * 0.7 + count_factor * 0.3
        
        return results
    
    def detect_layering_patterns(self, address: str, days_history: int = 90) -> Dict:
        """
        Detect fund layering patterns (splitting and recombining funds).

        Args:
            address (str): Address to analyze
            days_history (int): How many days of history to consider.

        Returns:
            Dict: Detected layering patterns
        """
        results = {
            "address": address,
            "timestamp": datetime.now().isoformat(),
            "layering_detected": False,
            "confidence": 0.0,
            "patterns": [],
            "error": None
        }

        if not self.helius_client:
            results["error"] = "Helius client required for transaction analysis."
            return results

        try:
            logging.info(f"Analyzing layering patterns for {address} (last {days_history} days)...")
            # Fetch recent transactions (needs pagination for full history)
            signatures_result = self.helius_client.get_signatures_for_address(address, limit=1000)
            signatures = signatures_result.get("result", [])
            cutoff_time = time.time() - days_history * 86400
            recent_signatures = [s for s in signatures if s.get('blockTime', 0) > cutoff_time]

            if not recent_signatures:
                logging.info("No recent transactions found for layering analysis.")
                return results

            # Basic Layering Detection Heuristics:
            # 1. Splitting: Look for transactions sending funds from the address to multiple new/low-activity addresses.
            # 2. Aggregation: Look for transactions receiving funds into the address from multiple sources shortly after splitting.
            # 3. Temporal Correlation: Check if splitting and aggregation happen within a short time window.

            split_events = []
            aggregation_events = []

            # Analyze recent transactions (fetching details is needed for amounts/destinations)
            for sig_info in recent_signatures:
                sig = sig_info['signature']
                block_time = sig_info.get('blockTime')
                try:
                    tx_detail_res = self.helius_client.get_transaction(sig)
                    tx_detail = tx_detail_res.get("result")
                    if not tx_detail: continue

                    transfers = self._extract_transfers_from_tx(tx_detail) # Helper to get SOL/SPL transfers

                    # Check for splitting
                    outgoing_transfers = [t for t in transfers if t['source'] == address]
                    if len(outgoing_transfers) > 2: # Simple heuristic: sending to 3+ destinations
                         # Further check if destinations are new/low activity (requires more API calls)
                         split_events.append({
                             "tx_hash": sig,
                             "time": block_time,
                             "destinations": [t['destination'] for t in outgoing_transfers],
                             "amount": sum(t['amount'] for t in outgoing_transfers)
                         })

                    # Check for aggregation
                    incoming_transfers = [t for t in transfers if t['destination'] == address]
                    if len(incoming_transfers) > 2: # Simple heuristic: receiving from 3+ sources
                         aggregation_events.append({
                             "tx_hash": sig,
                             "time": block_time,
                             "sources": [t['source'] for t in incoming_transfers],
                             "amount": sum(t['amount'] for t in incoming_transfers)
                         })
                    time.sleep(0.1) # Rate limit
                except Exception as tx_err:
                    logging.warning(f"Failed to process tx {sig} for layering: {tx_err}")

            # Correlate split and aggregation events (simple temporal check)
            for split in split_events:
                for aggr in aggregation_events:
                    time_diff = abs(split['time'] - aggr['time'])
                    # If aggregation happens within, e.g., 1 hour of splitting
                    if 0 < time_diff < 3600:
                        # Basic check if amounts are roughly similar (e.g., within 20%)
                        if abs(split['amount'] - aggr['amount']) / max(split['amount'], aggr['amount'], 1) < 0.2:
                             results["layering_detected"] = True
                             results["confidence"] = max(results["confidence"], 0.6) # Assign confidence score
                             results["patterns"].append({
                                 "type": "split_aggregate_correlation",
                                 "split_tx": split['tx_hash'],
                                 "aggregate_tx": aggr['tx_hash'],
                                 "time_diff_seconds": time_diff
                             })
                             # Break inner loop once a correlation is found for a split event
                             break

            if results["layering_detected"]:
                 logging.info(f"Potential layering detected for {address}.")

        except Exception as e:
            logging.error(f"Error detecting layering patterns for {address}: {e}")
            results["error"] = str(e)

        return results

    # Helper methods
    
    def _process_token_accounts(self, token_accounts_data: Dict) -> Dict:
        """Process token accounts data into a more usable format."""
        accounts = token_accounts_data.get("result", {}).get("value", [])
        
        processed = {
            "total_accounts": len(accounts),
            "tokens": []
        }
        
        for account in accounts:
            try:
                account_data = account.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
                mint = account_data.get("mint", "")
                amount = account_data.get("tokenAmount", {})
                
                processed["tokens"].append({
                    "mint": mint,
                    "amount": amount.get("amount"),
                    "ui_amount": amount.get("uiAmount"),
                    "decimals": amount.get("decimals")
                })
            except Exception:
                continue
        
        return processed
    
    def _summarize_transactions(self, signatures: List[Dict]) -> Dict:
        """Summarize transaction signatures data."""
        summary = {
            "total_transactions": len(signatures),
            "earliest_transaction": None,
            "latest_transaction": None,
            "error_count": 0
        }
        
        block_times = []
        
        for sig in signatures:
            block_time = sig.get("blockTime")
            if block_time:
                block_times.append(block_time)
            
            if sig.get("err"):
                summary["error_count"] += 1
        
        if block_times:
            summary["earliest_transaction"] = min(block_times)
            summary["latest_transaction"] = max(block_times)
        
        return summary
    
    def _extract_transaction_details(self, tx_data: Dict) -> Dict:
        """Extract relevant details from transaction data."""
        result = tx_data.get("result", {})
        
        details = {
            "block_time": result.get("blockTime"),
            "slot": result.get("slot"),
            "fee": result.get("meta", {}).get("fee"),
            "success": result.get("meta", {}).get("status", {}).get("Ok") is not None,
            "log_messages": result.get("meta", {}).get("logMessages", []),
            "signers": [],
            "token_transfers": []
        }
        
        # Extract signers
        tx = result.get("transaction", {}).get("message", {})
        account_keys = tx.get("accountKeys", [])
        
        for i, key in enumerate(account_keys):
            if key.get("signer", False):
                details["signers"].append(key.get("pubkey"))
        
        # Extract token transfers from inner instructions
        inner_instructions = result.get("meta", {}).get("innerInstructions", [])
        
        for inner_ix in inner_instructions:
            for ix in inner_ix.get("instructions", []):
                if ix.get("program") == "spl-token" and ix.get("parsed", {}).get("type") == "transfer":
                    info = ix.get("parsed", {}).get("info", {})
                    details["token_transfers"].append({
                        "source": info.get("source"),
                        "destination": info.get("destination"),
                        "authority": info.get("authority"),
                        "amount": info.get("amount")
                    })
        
        return details
    
    def _analyze_fund_flow(self, tx_details: Dict) -> Dict:
        """Analyze the flow of funds within a transaction using extracted details."""
        flow = {
            "type": "unknown",
            "complexity": "low", # low, medium, high
            "net_sol_flow": {}, # {address: change}
            "net_token_flow": {} # {mint: {address: change}}
        }
        transfers = self._extract_transfers_from_tx(tx_details) # Use the helper

        if not transfers:
            flow["type"] = "no_transfer"
            return flow

        # Basic classification (can be expanded)
        unique_mints = set(t['mint'] for t in transfers if t['type'] == 'SPL')
        unique_sources = set(t['source'] for t in transfers if t['source'] != 'unknown')
        unique_destinations = set(t['destination'] for t in transfers if t['destination'] != 'unknown')

        if len(unique_sources) == 1 and len(unique_destinations) == 1:
            flow["type"] = "simple_transfer"
        elif len(unique_sources) == 1 and len(unique_destinations) > 1:
            flow["type"] = "split"
            flow["complexity"] = "medium" if len(unique_destinations) <= 5 else "high"
        elif len(unique_sources) > 1 and len(unique_destinations) == 1:
            flow["type"] = "aggregation"
            flow["complexity"] = "medium" if len(unique_sources) <= 5 else "high"
        else:
            flow["type"] = "complex"
            flow["complexity"] = "high"

        # Calculate net flow (simplified)
        for t in transfers:
             if t['type'] == 'SPL':
                  mint = t['mint']
                  if mint not in flow["net_token_flow"]:
                       flow["net_token_flow"][mint] = {}
                  if t['source'] != 'unknown':
                       flow["net_token_flow"][mint][t['source']] = flow["net_token_flow"][mint].get(t['source'], 0) - t['amount']
                  if t['destination'] != 'unknown':
                       flow["net_token_flow"][mint][t['destination']] = flow["net_token_flow"][mint].get(t['destination'], 0) + t['amount']
             # SOL flow calculation needs refinement based on pre/post balances

        return flow
    
    def _extract_participants(self, tx_details: Dict) -> Dict:
        """Extract and potentially enrich participant information."""
        participants = set(tx_details.get("signers", []))
        transfers = self._extract_transfers_from_tx(tx_details)

        for t in transfers:
            if t['source'] != 'unknown': participants.add(t['source'])
            if t['destination'] != 'unknown': participants.add(t['destination'])
            if t.get('authority') and t['authority'] != 'unknown': participants.add(t['authority'])

        participant_info = {}
        # Optionally enrich with Range labels if client available
        if self.range_client:
            for addr in participants:
                try:
                    info = self.range_client.get_address_info(addr)
                    participant_info[addr] = {
                        "labels": info.get("labels", []),
                        "entity": info.get("entity", {})
                    }
                    time.sleep(0.1) # Rate limit
                except Exception as e:
                    logging.warning(f"Failed to get info for participant {addr}: {e}")
                    participant_info[addr] = {"error": str(e)}
        else:
             for addr in participants:
                  participant_info[addr] = {} # No enrichment

        return participant_info
    
    def _detect_suspicious_patterns(self, address: str, analysis_results: Dict) -> Dict:
        """Detect suspicious patterns based on aggregated analysis results."""
        patterns = []
        confidence = 0.0

        # High Risk Score
        risk_score = analysis_results.get("risk_assessment", {}).get("risk_score", 0)
        if risk_score > 75:
            patterns.append({
                "type": "high_risk_score",
                "score": risk_score,
                "factors": analysis_results.get("risk_assessment", {}).get("risk_factors", [])
            })
            confidence = max(confidence, 0.7)

        # Interaction with known illicit entities (requires Range labels)
        entity_labels = analysis_results.get("entity_information", {}).get("labels", [])
        illicit_labels = ['sanctioned', 'darknet_service', 'scam', 'phishing'] # Example labels
        if any(label in illicit_labels for label in entity_labels):
             patterns.append({
                 "type": "associated_with_illicit_entity",
                 "labels": [label for label in entity_labels if label in illicit_labels]
             })
             confidence = max(confidence, 0.9)

        # Counterparty risk (requires counterparty analysis & risk scores)
        # suspicious_counterparties = analysis_results.get("counterparty_analysis", {}).get("suspicious_counterparties", [])
        # if suspicious_counterparties:
        #      patterns.append({"type": "interacted_with_high_risk_counterparties", "count": len(suspicious_counterparties)})
        #      confidence = max(confidence, 0.5)

        # Rapid token turnover (requires token holding history)
        # ...

        # High transaction frequency (from transaction summary)
        tx_summary = analysis_results.get("transaction_summary", {})
        if tx_summary.get("total_transactions", 0) > 500: # Arbitrary threshold for recent history
             # Check time range to calculate frequency
             first_tx = tx_summary.get("earliest_transaction")
             last_tx = tx_summary.get("latest_transaction")
             if first_tx and last_tx and (last_tx - first_tx) > 0:
                  duration_hours = (last_tx - first_tx) / 3600
                  tx_per_hour = tx_summary["total_transactions"] / duration_hours if duration_hours > 0 else float('inf')
                  if tx_per_hour > 10: # Arbitrary threshold
                       patterns.append({"type": "high_transaction_frequency", "tx_per_hour": tx_per_hour})
                       confidence = max(confidence, 0.4)


        return {
            "suspicious_patterns_detected": len(patterns) > 0,
            "overall_confidence": confidence,
            "patterns": patterns
        }
    
    def _calculate_address_similarity(self, address1: str, address2: str) -> Dict:
        """
        Calculate similarity between two addresses for poisoning detection.
        
        Args:
            address1 (str): First address
            address2 (str): Second address
            
        Returns:
            Dict: Similarity metrics
        """
        # Calculate common prefix length
        common_prefix_length = 0
        for i in range(min(len(address1), len(address2))):
            if address1[i] == address2[i]:
                common_prefix_length += 1
            else:
                break
        
        # Calculate common suffix length
        common_suffix_length = 0
        for i in range(min(len(address1), len(address2))):
            if address1[-(i+1)] == address2[-(i+1)]:
                common_suffix_length += 1
            else:
                break
        
        # Calculate similarity score with emphasis on prefix (common in poisoning)
        prefix_weight = 0.8
        suffix_weight = 0.2
        
        # Normalize for comparison
        prefix_similarity = common_prefix_length / min(8, min(len(address1), len(address2)))
        suffix_similarity = common_suffix_length / min(4, min(len(address1), len(address2)))
        
        similarity_score = prefix_weight * prefix_similarity + suffix_weight * suffix_similarity
        
        # Determine similarity type
        similarity_type = "none"
        if common_prefix_length >= 8:
            similarity_type = "prefix"
        elif common_suffix_length >= 4:
            similarity_type = "suffix"
        elif common_prefix_length >= 4 and common_suffix_length >= 2:
            similarity_type = "both"
        
        return {
            "score": similarity_score,
            "type": similarity_type,
            "common_prefix_length": common_prefix_length,
            "common_suffix_length": common_suffix_length
        }
    
    def _analyze_counterparties(self, counterparties_data: Dict) -> Dict:
        """Analyze counterparty data from Range."""
        counterparties = counterparties_data.get("counterparties", [])
        summary = {
            "total_interactions": 0,
            "unique_counterparties": len(counterparties),
            "top_counterparties_by_volume": [],
            "top_counterparties_by_count": [],
            "suspicious_counterparties": []
        }
        if not counterparties:
            return summary

        df = pd.DataFrame(counterparties)
        summary["total_interactions"] = df['count'].sum()

        # Sort and get top counterparties
        df_sorted_volume = df.sort_values('volume', ascending=False)
        df_sorted_count = df.sort_values('count', ascending=False)

        summary["top_counterparties_by_volume"] = df_sorted_volume.head(5).to_dict('records')
        summary["top_counterparties_by_count"] = df_sorted_count.head(5).to_dict('records')

        # Identify potentially suspicious counterparties (e.g., high risk score from Range)
        # This requires fetching risk scores for counterparties - potentially many API calls
        # summary["suspicious_counterparties"] = [...]

        return summary

    def _extract_transfers_from_tx(self, tx_detail: Dict) -> List[Dict]:
        """Extract SOL and SPL transfers from a detailed Helius transaction."""
        transfers = []
        meta = tx_detail.get("meta", {})
        message = tx_detail.get("transaction", {}).get("message", {})
        account_keys = [acc['pubkey'] for acc in message.get("accountKeys", [])]

        # SOL transfers (System Program)
        pre_balances = meta.get("preBalances", [])
        post_balances = meta.get("postBalances", [])
        if len(pre_balances) == len(post_balances) == len(account_keys):
            for i, key in enumerate(account_keys):
                diff = post_balances[i] - pre_balances[i]
                # Identify simple transfers (ignoring fees for now)
                # This heuristic is basic and might misinterpret complex instructions
                if diff != 0 and abs(diff) != meta.get("fee", 0):
                     # Find corresponding sender/receiver based on balance change sign
                     # This part is complex and requires careful mapping; simplified here
                     # Assuming a simple transfer for illustration
                     if diff < 0: # Potential sender
                          # Need to find receiver(s) with positive diff
                          pass
                     else: # Potential receiver
                          # Need to find sender(s) with negative diff
                          pass
                     # Simplified: Add potential transfer info (needs refinement)
                     # transfers.append({
                     #      "type": "SOL",
                     #      "source": "unknown", # Requires mapping logic
                     #      "destination": "unknown", # Requires mapping logic
                     #      "amount": abs(diff) / 1e9 # Lamports to SOL
                     # })
                     pass # Skip SOL for now due to complexity

        # SPL Token transfers
        pre_token_balances = meta.get("preTokenBalances", [])
        post_token_balances = meta.get("postTokenBalances", [])

        # Process pre balances
        pre_map = {}
        for bal in pre_token_balances:
            key = (bal.get("owner"), bal.get("mint"))
            pre_map[key] = int(bal.get("uiTokenAmount", {}).get("amount", 0))

        # Process post balances and identify transfers
        for bal in post_token_balances:
            key = (bal.get("owner"), bal.get("mint"))
            post_amount = int(bal.get("uiTokenAmount", {}).get("amount", 0))
            pre_amount = pre_map.get(key, 0)
            diff = post_amount - pre_amount

            if diff != 0:
                 # Find corresponding source/destination based on diff sign
                 # This requires matching changes for the same mint
                 # Simplified: Add potential transfer info (needs refinement)
                 transfers.append({
                     "type": "SPL",
                     "mint": bal.get("mint"),
                     "source": "unknown" if diff > 0 else bal.get("owner"), # Basic guess
                     "destination": bal.get("owner") if diff > 0 else "unknown", # Basic guess
                     "amount": abs(diff) # Amount in token's smallest unit
                     # "uiAmount": abs(diff) / (10**bal.get("uiTokenAmount", {}).get("decimals", 0)) # Requires decimals
                 })

        return transfers

    def _detect_mixer_routes(self, address: str, transactions: List[Dict]) -> List[Dict]:
        """Detect routes involving known mixer addresses."""
        routes = []
        # Define known mixer addresses (should be updated regularly)
        known_mixers = {
            "tor1xzb2Zyy1cUxXmyJfR8aNXuWnwHG8AwgaG7UGD4K": "Tornado Cash Router (Wormhole)",
            # Add more known Solana mixers
        }

        for tx in transactions:
            transfers = self._extract_transfers_from_tx(tx)
            for transfer in transfers:
                # Check if destination is a known mixer
                if transfer['destination'] in known_mixers and transfer['source'] == address:
                    routes.append({
                        "type": "mixer_deposit",
                        "tx_hash": tx.get("signature"), # Assuming Helius structure
                        "mixer_address": transfer['destination'],
                        "mixer_name": known_mixers[transfer['destination']],
                        "amount": transfer['amount'],
                        "mint": transfer.get('mint'),
                        "timestamp": tx.get("blockTime"),
                        "risk_score": 80 # Assign risk score
                    })
                # Check if source is a known mixer (withdrawal)
                elif transfer['source'] in known_mixers and transfer['destination'] == address:
                     routes.append({
                        "type": "mixer_withdrawal",
                        "tx_hash": tx.get("signature"),
                        "mixer_address": transfer['source'],
                        "mixer_name": known_mixers[transfer['source']],
                        "amount": transfer['amount'],
                        "mint": transfer.get('mint'),
                        "timestamp": tx.get("blockTime"),
                        "risk_score": 70 # Lower risk than deposit for the receiver
                    })
        return routes

    def _detect_bridge_routes(self, address: str, transactions: List[Dict]) -> List[Dict]:
        """Detect routes involving known cross-chain bridges."""
        routes = []
        # Define known bridge addresses (should be updated regularly)
        known_bridges = {
            "wormDTUJ6AWPNvk59vGQbDvGJmqbDTdgWgAqcLBCgUb": "Wormhole: Solana Lock",
            "worm2ZoG2kUd4vFXhvjh93UUH596ayRfgQ2MgjNMTth": "Wormhole: Solana Claim",
            # Add other bridges like Portal, Allbridge, etc.
        }

        for tx in transactions:
            transfers = self._extract_transfers_from_tx(tx)
            for transfer in transfers:
                # Check interaction with known bridges
                if transfer['destination'] in known_bridges and transfer['source'] == address:
                    routes.append({
                        "type": "bridge_outbound",
                        "tx_hash": tx.get("signature"),
                        "bridge_address": transfer['destination'],
                        "bridge_name": known_bridges[transfer['destination']],
                        "amount": transfer['amount'],
                        "mint": transfer.get('mint'),
                        "timestamp": tx.get("blockTime"),
                        "risk_score": 60 # Moderate risk, depends on destination chain context
                    })
                elif transfer['source'] in known_bridges and transfer['destination'] == address:
                     routes.append({
                        "type": "bridge_inbound",
                        "tx_hash": tx.get("signature"),
                        "bridge_address": transfer['source'],
                        "bridge_name": known_bridges[transfer['source']],
                        "amount": transfer['amount'],
                        "mint": transfer.get('mint'),
                        "timestamp": tx.get("blockTime"),
                        "risk_score": 50 # Moderate risk, depends on source chain context
                    })
        return routes

    def _detect_exchange_routes(self, address: str, transactions: List[Dict]) -> List[Dict]:
        """Detect routes involving known CEX/DEX addresses."""
        routes = []
        # Use Range labels if available to identify exchanges
        if not self.range_client: return routes

        # This requires fetching labels for counterparties, which can be slow.
        # A better approach might be to pre-fetch labels for counterparties.
        # Simplified: Check if counterparties *might* be exchanges based on transaction patterns.

        # Example Heuristic: Large volume transfers to/from addresses with many interactions
        # This is very basic and needs refinement.
        for tx in transactions:
             transfers = self._extract_transfers_from_tx(tx)
             for transfer in transfers:
                  counterparty = None
                  direction = None
                  if transfer['source'] == address and transfer['destination'] != 'unknown':
                       counterparty = transfer['destination']
                       direction = "exchange_deposit"
                  elif transfer['destination'] == address and transfer['source'] != 'unknown':
                       counterparty = transfer['source']
                       direction = "exchange_withdrawal"

                  if counterparty:
                       # Basic check: Is the amount significant? (e.g., > $1000)
                       # Requires price data or assuming stablecoins/SOL
                       is_significant = transfer['amount'] > 1000 # Placeholder check

                       # In a real implementation, check Range labels for 'exchange'
                       # try:
                       #      info = self.range_client.get_address_info(counterparty)
                       #      is_exchange = any(lbl.get('label') == 'exchange' for lbl in info.get('labels', []))
                       # except: is_exchange = False

                       # Simplified check based on amount
                       if is_significant: # and is_exchange:
                            routes.append({
                                "type": direction,
                                "tx_hash": tx.get("signature"),
                                "exchange_address": counterparty, # Potentially an exchange
                                "amount": transfer['amount'],
                                "mint": transfer.get('mint'),
                                "timestamp": tx.get("blockTime"),
                                "risk_score": 40 # Lower risk unless exchange is high-risk itself
                            })
        return routes

    def _identify_laundering_patterns(self, routes: List[Dict]) -> List[str]:
        """Identify common money laundering patterns from detected routes."""
        patterns = set()
        has_mixer_deposit = any(r['type'] == 'mixer_deposit' for r in routes)
        has_mixer_withdrawal = any(r['type'] == 'mixer_withdrawal' for r in routes)
        has_bridge_out = any(r['type'] == 'bridge_outbound' for r in routes)
        has_bridge_in = any(r['type'] == 'bridge_inbound' for r in routes)
        has_exchange_deposit = any(r['type'] == 'exchange_deposit' for r in routes)
        has_exchange_withdrawal = any(r['type'] == 'exchange_withdrawal' for r in routes)

        if has_mixer_deposit: patterns.add("Mixer Usage (Deposit)")
        if has_mixer_withdrawal: patterns.add("Mixer Usage (Withdrawal)")
        if has_bridge_out: patterns.add("Cross-Chain Bridging (Outbound)")
        if has_bridge_in: patterns.add("Cross-Chain Bridging (Inbound)")
        if has_exchange_deposit: patterns.add("Exchange Interaction (Deposit)")
        if has_exchange_withdrawal: patterns.add("Exchange Interaction (Withdrawal)")

        # More complex patterns combining routes:
        # Example: Bridge Out -> Mixer -> Bridge In (requires cross-chain tracking)
        # Example: Exchange Deposit -> Mixer -> Exchange Withdrawal

        return list(patterns)