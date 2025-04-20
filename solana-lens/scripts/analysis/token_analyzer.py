import json
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import time
import logging # Use logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TokenAnalyzer:
    """
    Analyzer for Solana tokens to assess risks and detect suspicious activity.
    
    This class provides methods to analyze token data for rug pull risks,
    insider activity, and token security patterns.
    """
    
    def __init__(self, range_client=None, helius_client=None, rugcheck_client=None, vybe_client=None):
        """
        Initialize the TokenAnalyzer.
        
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
        
        # Known risk factors for tokens
        self.risk_factors = {
            "mint_authority": {
                "description": "Mint authority is set which allows minting unlimited tokens",
                "severity": "high"
            },
            "freeze_authority": {
                "description": "Freeze authority is set which allows freezing token accounts",
                "severity": "medium"
            },
            "transfer_fee": {
                "description": "Token has a transfer fee",
                "severity": "medium"
            },
            "low_liquidity": {
                "description": "Token has low liquidity relative to market cap",
                "severity": "high"
            },
            "insider_concentration": {
                "description": "Token is heavily concentrated among insider wallets",
                "severity": "high"
            },
            "suspicious_creator": {
                "description": "Token creator has created other suspicious tokens",
                "severity": "high"
            }
        }
    
    def analyze_token(self, token_mint: str) -> Dict:
        """
        Perform comprehensive analysis of a token.
        
        Args:
            token_mint (str): Token mint address
            
        Returns:
            Dict: Analysis results
        """
        results = {
            "token_mint": token_mint,
            "timestamp": datetime.now().isoformat(),
            "token_info": {},
            "risk_assessment": {},
            "holder_analysis": {},
            "creator_analysis": {},
            "liquidity_analysis": {},
            "historical_activity": {}
        }
        
        # Get token information if Vybe client is available
        if self.vybe_client:
            try:
                token_info = self.vybe_client.get_token_details(token_mint)
                # Assuming Vybe response structure, adjust keys as needed
                results["token_info"] = {
                    "name": token_info.get("name", ""),
                    "symbol": token_info.get("symbol", ""),
                    "decimals": token_info.get("decimals", 0),
                    "supply": token_info.get("supply", 0),
                    "price_usd": token_info.get("price", {}).get("usd", 0), # Nested price
                    "market_cap": token_info.get("market_cap", {}).get("usd", 0), # Nested market cap
                    "description": token_info.get("description", ""),
                    "image_uri": token_info.get("image_uri", ""),
                    "website": token_info.get("website", ""),
                    "tags": token_info.get("tags", [])
                }
                logging.info(f"Vybe token info fetched for {token_mint}")
            except Exception as e:
                logging.error(f"Error getting Vybe token info for {token_mint}: {e}")
                results["token_info"] = {"error": str(e)}
        else:
            logging.warning("Vybe client not available for token info.")

        # Get risk assessment if RugCheck client is available
        if self.rugcheck_client:
            try:
                # Use summary first for efficiency
                risk_summary = self.rugcheck_client.get_token_report_summary(token_mint)
                results["risk_assessment"] = {
                    "score": risk_summary.get("score", 0),
                    "score_normalized": risk_summary.get("score_normalised", 0), # Note spelling
                    "token_type": risk_summary.get("tokenType", ""),
                    "risk_factors": risk_summary.get("risks", []),
                    "is_verified": risk_summary.get("verified", False),
                    "rugcheck_url": f"https://rugcheck.xyz/tokens/{token_mint}"
                }
                logging.info(f"RugCheck risk summary fetched for {token_mint}: Score {results['risk_assessment'].get('score')}")

                # Fetch full report for more details if needed later
                # token_report = self.rugcheck_client.get_token_report(token_mint)
                # results["risk_assessment"]["full_report_data"] = token_report # Store if needed

            except Exception as e:
                logging.error(f"Error getting RugCheck risk assessment for {token_mint}: {e}")
                results["risk_assessment"] = {"error": str(e)}
        else:
            logging.warning("RugCheck client not available for risk assessment.")

        # Get holder analysis if Vybe client is available
        if self.vybe_client:
            try:
                # Note: Vybe might require pagination for full holder list
                holders_data = self.vybe_client.get_token_top_holders(token_mint, query_params={"limit": 100}) # Limit for example
                results["holder_analysis"] = self._analyze_token_holders(holders_data)
                logging.info(f"Vybe holder analysis for {token_mint}: Found {results['holder_analysis'].get('total_holders')} holders.")
            except Exception as e:
                logging.error(f"Error getting Vybe holder analysis for {token_mint}: {e}")
                results["holder_analysis"] = {"error": str(e)}
        else:
            logging.warning("Vybe client not available for holder analysis.")

        # Get creator and liquidity analysis using RugCheck (if available)
        if self.rugcheck_client:
            try:
                # Fetch full report only if needed and not already fetched
                if "full_report_data" not in results["risk_assessment"]:
                     token_report = self.rugcheck_client.get_token_report(token_mint)
                     logging.info(f"RugCheck full report fetched for {token_mint}")
                else:
                     token_report = results["risk_assessment"]["full_report_data"] # Reuse if fetched

                # Extract creator information
                creator = token_report.get("creator", "")
                creator_tokens_data = token_report.get("creatorTokens", []) # List of other tokens by creator

                results["creator_analysis"] = {
                    "creator_address": creator,
                    "other_tokens_count": len(creator_tokens_data),
                    # Optionally fetch details for other tokens if needed (can be slow)
                    # "creator_tokens_summary": [{"mint": t.get("mint"), "name": t.get("name")} for t in creator_tokens_data[:5]], # Example summary
                    "is_suspicious": self._is_creator_suspicious(creator, creator_tokens_data)
                }
                logging.info(f"RugCheck creator analysis for {token_mint}: Creator {creator}, {len(creator_tokens_data)} other tokens.")

                # Extract liquidity information
                markets = token_report.get("markets", [])
                results["liquidity_analysis"] = self._analyze_token_liquidity(markets)
                logging.info(f"RugCheck liquidity analysis for {token_mint}: Total Liq ${results['liquidity_analysis'].get('total_liquidity_usd'):.2f}, Locked {results['liquidity_analysis'].get('liquidity_locked_pct'):.1f}%")

            except Exception as e:
                logging.error(f"Error getting RugCheck creator/liquidity analysis for {token_mint}: {e}")
                # Avoid overwriting if only one part failed
                if "creator_analysis" not in results: results["creator_analysis"] = {"error": str(e)}
                if "liquidity_analysis" not in results: results["liquidity_analysis"] = {"error": str(e)}
        else:
            logging.warning("RugCheck client not available for creator/liquidity analysis.")


        # Get historical activity if Vybe client is available
        if self.vybe_client:
            try:
                # Get OHLCV data (e.g., daily for last 90 days)
                ohlcv_params = {"resolution": "1D", "limit": 90} # Example: Daily, 90 data points
                ohlcv_data = self.vybe_client.get_token_ohlcv(token_mint, query_params=ohlcv_params)

                # Get token holder count time series if available (Vybe might not have this specific endpoint)
                # holder_ts_data = {} # Placeholder

                results["historical_activity"] = {
                    "price_data": ohlcv_data.get("data", []), # Assuming 'data' contains OHLCV list
                    # "holder_data": holder_ts_data.get("data", [])
                }
                logging.info(f"Vybe historical activity fetched for {token_mint}")
            except Exception as e:
                logging.error(f"Error getting Vybe historical activity for {token_mint}: {e}")
                results["historical_activity"] = {"error": str(e)}
        else:
            logging.warning("Vybe client not available for historical activity.")

        # Clean up potentially large data from full report if stored
        if "full_report_data" in results.get("risk_assessment", {}):
            del results["risk_assessment"]["full_report_data"]

        return results

    def analyze_token_creator(self, creator_address: str) -> Dict:
        """
        Analyze a token creator's history and patterns.
        
        Args:
            creator_address (str): Creator's address
            
        Returns:
            Dict: Creator analysis results
        """
        results = {
            "creator_address": creator_address,
            "timestamp": datetime.now().isoformat(),
            "creator_info": {},
            "tokens_created": [],
            "pattern_analysis": {},
            "risk_assessment": {}
        }
        
        # Get creator information if Range client is available
        if self.range_client:
            try:
                address_info = self.range_client.get_address_info(creator_address)
                results["creator_info"] = {
                    "labels": address_info.get("labels", []),
                    "entity": address_info.get("entity", {})
                }
                logging.info(f"Range creator info fetched for {creator_address}")
            except Exception as e:
                logging.error(f"Error getting Range creator info for {creator_address}: {e}")
                results["creator_info"] = {"error": str(e)}
        else:
            logging.warning("Range client not available for creator info.")

        # Get tokens created using RugCheck (if available)
        # Note: RugCheck doesn't have a direct "get tokens by creator" endpoint.
        # We might need to infer this or use another source.
        # Using a placeholder approach - assuming we can get this list somehow.
        # A more robust solution might involve querying an indexer or parsing creation events.
        creator_tokens_list = []
        if self.rugcheck_client:
             logging.warning("Fetching tokens by creator directly is not supported by RugCheck API. Using indirect methods or other sources might be needed.")
             # Placeholder: Could try searching recent tokens and filtering by creator if available in stats endpoints
             try:
                 recent_tokens = self.rugcheck_client.get_recently_detected_tokens()
                 creator_tokens_list = [t for t in recent_tokens if t.get("creator") == creator_address]
                 logging.info(f"Found {len(creator_tokens_list)} tokens potentially created by {creator_address} in recent RugCheck stats.")
             except Exception as e:
                 logging.error(f"Error fetching recent tokens from RugCheck for creator analysis: {e}")
        else:
             logging.warning("RugCheck client not available to fetch creator's tokens.")

        results["tokens_created"] = creator_tokens_list # Store summary or full data

        # Analyze token creation patterns based on the fetched list
        results["pattern_analysis"] = self._analyze_creator_patterns(results["tokens_created"])

        # Assess creator risk based on available info
        results["risk_assessment"] = self._assess_creator_risk(creator_address, results)

        return results

    def detect_token_rug_patterns(self, token_mint: str) -> Dict:
        """
        Detect patterns associated with rug pulls for a token.
        
        Args:
            token_mint (str): Token mint address
            
        Returns:
            Dict: Detected rug patterns
        """
        results = {
            "token_mint": token_mint,
            "timestamp": datetime.now().isoformat(),
            "rug_risk_score": 0,
            "detected_patterns": [],
            "evidence": {}
        }
        
        if not self.rugcheck_client:
            # ... existing error handling ...
            logging.warning("RugCheck client not available for rug pattern detection.")
            return results

        try:
            token_report = self.rugcheck_client.get_token_report(token_mint)
            logging.info(f"Fetched RugCheck full report for rug pattern analysis of {token_mint}")

            # Extract risk factors from the report
            risks = token_report.get("risks", []) # Assuming 'risks' is the key for detailed factors

            # --- Pattern Detection Logic ---
            patterns = []
            evidence = {}
            rug_score_contribution = 0

            # 1. Mint Authority Check
            mint_authority = token_report.get("mintAuthority")
            if mint_authority:
                patterns.append("mint_authority_enabled")
                evidence["mint_authority"] = {
                    "address": mint_authority,
                    "description": "Mint authority is enabled, allowing unlimited minting."
                }
                rug_score_contribution += 25 # High risk

            # 2. Freeze Authority Check
            freeze_authority = token_report.get("freezeAuthority")
            if freeze_authority:
                patterns.append("freeze_authority_enabled")
                evidence["freeze_authority"] = {
                    "address": freeze_authority,
                    "description": "Freeze authority is enabled, allowing token account freezing."
                }
                rug_score_contribution += 15 # Medium risk

            # 3. Liquidity Analysis (using helper)
            markets = token_report.get("markets", [])
            liquidity_info = self._analyze_token_liquidity(markets)
            evidence["liquidity"] = liquidity_info
            if liquidity_info.get("total_liquidity_usd", 0) < 5000: # Arbitrary low liquidity threshold
                 patterns.append("low_liquidity")
                 rug_score_contribution += 20
            elif liquidity_info.get("liquidity_locked_pct", 100) < 80: # Arbitrary lock threshold
                 patterns.append("unlocked_liquidity")
                 rug_score_contribution += 25 # High risk if significant liquidity is unlocked

            # 4. Ownership Concentration (using RugCheck's top holders if available)
            top_holders = token_report.get("topHolders", []) # Assuming RugCheck provides this
            if top_holders:
                # Exclude known CEX/DEX/Bridge addresses if possible (requires label checking)
                non_infra_holders = [h for h in top_holders if not h.get("isExchange") and not h.get("isLp")] # Example filter keys
                top_pct_sum = sum(h.get("pct", 0) for h in non_infra_holders[:5]) # Sum top 5 non-infra
                if top_pct_sum > 40: # Arbitrary concentration threshold
                    patterns.append("concentrated_ownership")
                    evidence["ownership"] = {
                        "top_5_non_infra_pct": top_pct_sum,
                        "description": "Token ownership is highly concentrated among a few wallets (excluding known infra)."
                    }
                    rug_score_contribution += 20

            # 5. Insider Networks (using RugCheck's data)
            insider_networks = token_report.get("insiderNetworks", []) # Assuming this key exists
            if insider_networks:
                 total_insider_supply_pct = sum(net.get("supplyPct", 0) for net in insider_networks) # Check key name
                 if total_insider_supply_pct > 30: # Arbitrary threshold
                      patterns.append("insider_control")
                      evidence["insiders"] = {
                          "total_supply_pct": total_insider_supply_pct,
                          "network_count": len(insider_networks),
                          "description": "Significant portion of supply held by potential insider networks."
                      }
                      rug_score_contribution += 25

            # 6. Socials/Verification Check (from RugCheck)
            is_verified = token_report.get("verified", False)
            has_socials = any(token_report.get(link) for link in ["website", "twitter", "telegram", "discord"]) # Check common links
            if not is_verified and not has_socials:
                 patterns.append("missing_socials_or_verification")
                 evidence["socials"] = {"verified": is_verified, "has_socials": has_socials}
                 rug_score_contribution += 10


            # Calculate final rug risk score (capped at 100)
            results["rug_risk_score"] = min(100, int(rug_score_contribution))
            results["detected_patterns"] = patterns
            results["evidence"] = evidence
            logging.info(f"Rug pattern analysis for {token_mint}: Score {results['rug_risk_score']}, Patterns {patterns}")

        except Exception as e:
            logging.error(f"Error detecting rug patterns for {token_mint}: {e}")
            results["error"] = str(e)

        return results

    def analyze_token_transfers(self, token_mint: str, days: int = 7) -> Dict: # Shorten default for performance
        """
        Analyze token transfer patterns for suspicious activity.
        
        Args:
            token_mint (str): Token mint address
            days (int, optional): Number of days to analyze. Defaults to 30.
            
        Returns:
            Dict: Token transfer analysis
        """
        results = {
            "token_mint": token_mint,
            "timestamp": datetime.now().isoformat(),
            "transfer_count": 0,
            "volume_stats": {},
            "address_stats": {},
            "temporal_patterns": {},
            "suspicious_patterns": []
        }
        
        if not self.vybe_client:
            # ... existing error handling ...
            logging.warning("Vybe client not available for transfer analysis.")
            return results

        try:
            # Set up query parameters for time period
            end_time = int(datetime.now().timestamp())
            start_time = end_time - (days * 24 * 60 * 60)

            # Fetch transfers using Vybe (might need pagination)
            query_params = {
                "mintAddress": token_mint,
                "timeStart": start_time,
                "timeEnd": end_time,
                "limit": 1000 # Adjust limit as needed, handle pagination if necessary
            }
            logging.info(f"Fetching Vybe token transfers for {token_mint} (last {days} days)...")
            transfers_data = self.vybe_client.get_token_transfers(query_params=query_params)
            # Adjust key based on actual Vybe response structure
            transfers = transfers_data.get("data", []) # Assuming 'data' holds the list

            if not transfers:
                 logging.info(f"No transfers found for {token_mint} in the last {days} days.")
                 return results

            logging.info(f"Analyzing {len(transfers)} transfers...")
            results["transfer_count"] = len(transfers)

            # Volume statistics (ensure keys match Vybe response)
            volumes = [tx.get("amount", {}).get("usd", 0) for tx in transfers if tx.get("amount", {}).get("usd") is not None] # Use USD amount if available
            results["volume_stats"] = {
                "total_volume_usd": sum(volumes),
                "average_transfer_usd": sum(volumes) / len(volumes) if volumes else 0,
                "max_transfer_usd": max(volumes) if volumes else 0,
                "min_transfer_usd": min(volumes) if volumes else 0,
                "transfer_count_with_usd": len(volumes)
            }

            # Address statistics (ensure keys match Vybe response)
            senders = {}
            receivers = {}
            for tx in transfers:
                # Adjust keys based on Vybe response for sender/receiver
                sender = tx.get("from", {}).get("address") # Example key
                receiver = tx.get("to", {}).get("address") # Example key
                if sender: senders[sender] = senders.get(sender, 0) + 1
                if receiver: receivers[receiver] = receivers.get(receiver, 0) + 1

            results["address_stats"] = {
                "unique_senders": len(senders),
                "unique_receivers": len(receivers),
                "top_senders": self._get_top_items(senders, 5),
                "top_receivers": self._get_top_items(receivers, 5)
            }

            # Temporal patterns (ensure key match Vybe response for timestamp)
            block_times = [tx.get("blockTime", 0) for tx in transfers if tx.get("blockTime")] # Example key
            # ... (rest of temporal calculation remains similar) ...
            results["temporal_patterns"] = {
                 "earliest_transfer": min(block_times) if block_times else None,
                 "latest_transfer": max(block_times) if block_times else None,
                 # ... (avg/median time diff calculation) ...
            }


            # Detect suspicious patterns (implement specific logic)
            suspicious_patterns = self._detect_suspicious_transfer_patterns(transfers)
            results["suspicious_patterns"] = suspicious_patterns
            logging.info(f"Transfer analysis for {token_mint} complete. Found {len(suspicious_patterns)} suspicious patterns.")

        except Exception as e:
            logging.error(f"Error analyzing token transfers for {token_mint}: {e}")
            results["error"] = str(e)

        return results

    # Helper methods
    
    def _analyze_token_holders(self, holders_data: Dict) -> Dict:
        """Analyze token holder distribution."""
        holders = holders_data.get("holders", [])
        
        if not holders:
            return {
                "total_holders": 0,
                "concentration": {
                    "top_10_percent": 0,
                    "top_20_percent": 0,
                    "top_50_percent": 0
                }
            }
        
        # Calculate concentration metrics
        total_holders = len(holders)
        
        # Sort holders by percentage held
        sorted_holders = sorted(holders, key=lambda x: x.get("percentage", 0), reverse=True)
        
        # Calculate cumulative percentages
        cumulative_pct = 0
        top_10_count = 0
        top_20_count = 0
        top_50_count = 0
        
        for holder in sorted_holders:
            pct = holder.get("percentage", 0)
            cumulative_pct += pct
            
            if cumulative_pct <= 10:
                top_10_count += 1
            
            if cumulative_pct <= 20:
                top_20_count += 1
            
            if cumulative_pct <= 50:
                top_50_count += 1
        
        return {
            "total_holders": total_holders,
            "concentration": {
                "top_10_percent": top_10_count,
                "top_20_percent": top_20_count,
                "top_50_percent": top_50_count,
                "top_10_percent_ratio": top_10_count / total_holders if total_holders else 0,
                "top_20_percent_ratio": top_20_count / total_holders if total_holders else 0,
                "top_50_percent_ratio": top_50_count / total_holders if total_holders else 0
            },
            "top_holders": sorted_holders[:10] if len(sorted_holders) >= 10 else sorted_holders
        }
    
    def _is_creator_suspicious(self, creator: str, creator_tokens: List[Dict]) -> bool:
        """Determine if a token creator has suspicious patterns."""
        if not creator or not creator_tokens:
            return False
        
        # Check number of tokens
        if len(creator_tokens) > 20:
            return True
        
        # Check if creator has many short-lived tokens
        short_lived_count = 0
        for token in creator_tokens:
            created_at = token.get("createdAt", "")
            
            try:
                created_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                age_days = (datetime.now() - created_date).days
                
                if age_days < 30:
                    short_lived_count += 1
            except:
                pass
        
        if short_lived_count > 5:
            return True
        
        # More sophisticated checks would go here
        
        return False
    
    def _analyze_token_liquidity(self, markets: List[Dict]) -> Dict:
        """Analyze token liquidity from market data."""
        if not markets:
            return {
                "total_liquidity_usd": 0,
                "liquidity_locked_pct": 0,
                "liquidity_providers": 0
            }
        
        total_liquidity_usd = 0
        total_locked_liquidity_usd = 0
        total_lp_providers = 0
        
        for market in markets:
            lp = market.get("lp", {})
            
            # Add market liquidity
            base_usd = lp.get("baseUSD", 0)
            quote_usd = lp.get("quoteUSD", 0)
            market_liquidity = base_usd + quote_usd
            
            total_liquidity_usd += market_liquidity
            
            # Add locked liquidity
            locked_pct = lp.get("lpLockedPct", 0)
            total_locked_liquidity_usd += (market_liquidity * locked_pct / 100)
            
            # Count LP providers
            lp_holders = lp.get("holders", [])
            total_lp_providers += len(lp_holders)
        
        # Calculate overall locked percentage
        liquidity_locked_pct = (total_locked_liquidity_usd / total_liquidity_usd * 100) if total_liquidity_usd > 0 else 0
        
        return {
            "total_liquidity_usd": total_liquidity_usd,
            "liquidity_locked_usd": total_locked_liquidity_usd,
            "liquidity_locked_pct": liquidity_locked_pct,
            "liquidity_providers": total_lp_providers,
            "market_count": len(markets)
        }
    
    def _analyze_creator_patterns(self, tokens: List[Dict]) -> Dict:
        """Analyze token creation patterns from a list of tokens."""
        if not tokens:
            return {"message": "No tokens provided for pattern analysis."}

        creation_times = []
        lifespans = [] # Requires knowing when tokens died/rugged, hard to get reliably
        success_metrics = [] # Requires defining 'success' (e.g., market cap, volume)

        for token in tokens:
            # Assuming RugCheck stats format, adjust keys as needed
            created_at_str = token.get("createdAt")
            if created_at_str:
                try:
                    # Handle potential timezone info if present
                    if created_at_str.endswith('Z'):
                         created_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%S.%fZ") # Milliseconds format
                    else:
                         created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00')) # General ISO format
                    creation_times.append(created_at.timestamp())
                except ValueError:
                     try: # Try without milliseconds
                          created_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ")
                          creation_times.append(created_at.timestamp())
                     except ValueError:
                          logging.warning(f"Could not parse creation date: {created_at_str}")


            # Placeholder for success metric (e.g., using RugCheck score)
            success_metrics.append(token.get("score", 0))

        patterns = {}
        if creation_times:
            creation_times.sort()
            time_diffs = [creation_times[i+1] - creation_times[i] for i in range(len(creation_times)-1)]
            patterns["token_creation_frequency_median_seconds"] = self._median(time_diffs) if time_diffs else None
            patterns["token_creation_frequency_avg_seconds"] = sum(time_diffs) / len(time_diffs) if time_diffs else None
            patterns["creation_time_span_days"] = (max(creation_times) - min(creation_times)) / 86400 if len(creation_times) > 1 else 0

        # patterns["average_token_lifespan"] = ... # Hard to calculate
        patterns["average_rugcheck_score"] = sum(success_metrics) / len(success_metrics) if success_metrics else 0

        return patterns

    def _assess_creator_risk(self, creator_address: str, analysis_results: Dict) -> Dict:
        """Assess risk level of a token creator based on analysis."""
        risk_score = 0
        risk_factors = []

        # Factor 1: Number of tokens created
        token_count = len(analysis_results.get("tokens_created", []))
        if token_count > 10:
            risk_score += min(30, (token_count - 10) * 2) # Increase risk for high count
            risk_factors.append({"factor": "high_token_creation_count", "count": token_count})

        # Factor 2: Frequency of creation
        patterns = analysis_results.get("pattern_analysis", {})
        median_freq_sec = patterns.get("token_creation_frequency_median_seconds")
        if median_freq_sec is not None and median_freq_sec < 3600: # Median creation < 1 hour
             risk_score += 20
             risk_factors.append({"factor": "high_creation_frequency", "median_seconds": median_freq_sec})

        # Factor 3: Average quality/score of created tokens
        avg_score = patterns.get("average_rugcheck_score", 100) # Default to high if no score
        if avg_score < 50:
             risk_score += (50 - avg_score) # Add points for low average score
             risk_factors.append({"factor": "low_average_token_score", "average_score": avg_score})

        # Factor 4: Creator Labels (from Range)
        creator_labels = analysis_results.get("creator_info", {}).get("labels", [])
        if any(lbl in ['scammer', 'suspicious_creator'] for lbl in creator_labels): # Example labels
             risk_score += 50
             risk_factors.append({"factor": "suspicious_creator_labels", "labels": creator_labels})


        return {
            "risk_score": min(100, int(risk_score)),
            "risk_factors": risk_factors
        }
    
    def _extract_address(self, address_data: Any) -> Optional[str]:
        """Extract address from different data formats."""
        if isinstance(address_data, str):
            return address_data
        
        if isinstance(address_data, dict):
            return address_data.get("wallet") or address_data.get("address")
        
        return None
    
    def _get_top_items(self, items: Dict, count: int) -> List[Dict]:
        """Get top items from a dictionary by value."""
        sorted_items = sorted(items.items(), key=lambda x: x[1], reverse=True)
        return [{"address": k, "count": v} for k, v in sorted_items[:count]]
    
    def _median(self, values: List[float]) -> float:
        """Calculate median of a list of values."""
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n == 0:
            return 0.0
        
        if n % 2 == 1:
            return sorted_values[n // 2]
        else:
            return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
    
    def _detect_suspicious_transfer_patterns(self, transfers: List[Dict]) -> List[Dict]:
        """Detect suspicious patterns in token transfers (basic examples)."""
        patterns = []
        if not transfers: return patterns

        # Pattern 1: Wash Trading (Self-transfers or back-and-forth between few wallets)
        # This requires more sophisticated analysis tracking flows between specific pairs.
        # Placeholder: Detect direct self-transfers
        self_transfers = [tx for tx in transfers if tx.get("from", {}).get("address") == tx.get("to", {}).get("address")]
        if len(self_transfers) > 5: # Arbitrary threshold
             patterns.append({
                 "type": "potential_wash_trading_self",
                 "count": len(self_transfers),
                 "sample_tx": self_transfers[0].get("signature") # Example key
             })

        # Pattern 2: Pump and Dump Indicators (Rapid volume/price increase followed by large sell-offs from early holders)
        # Requires price data correlation, holder analysis over time. Complex.

        # Pattern 3: Large transfers to/from new wallets shortly after launch
        # Requires token launch date and wallet creation date/activity analysis.

        # Pattern 4: Sybil Transfers (Many small transfers from one source to many destinations or vice-versa)
        # Analyze sender/receiver counts from address_stats if calculated previously.
        # Example: If top sender accounts for > 50% of transfers and sends to > 100 unique receivers.

        return patterns