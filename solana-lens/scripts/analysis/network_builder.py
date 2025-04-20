import json
import pandas as pd
import networkx as nx
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import time
import logging # Use logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class NetworkBuilder:
    """
    Builder for creating network graphs from blockchain data.
    
    This class provides methods to construct network graphs for visualization
    and analysis of blockchain interactions including token flows, address
    relationships, and money laundering networks.
    """
    
    def __init__(self, range_client=None, helius_client=None, rugcheck_client=None, vybe_client=None):
        """
        Initialize the NetworkBuilder.
        
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
    
    def build_transaction_graph(self, transactions: List[Dict]) -> nx.DiGraph:
        """
        Build a directed graph from transaction data (assuming Helius format).

        Args:
            transactions (List[Dict]): List of transactions from Helius getTransaction.

        Returns:
            nx.DiGraph: Transaction graph
        """
        G = nx.DiGraph()
        logging.info(f"Building transaction graph from {len(transactions)} transactions...")

        for tx_detail in transactions:
            # Extract transfers using the helper from AddressAnalyzer
            # Note: This requires AddressAnalyzer instance or moving the helper
            # For simplicity, let's assume a similar helper exists here or is passed.
            # transfers = self._extract_transfers_from_tx(tx_detail) # Assumes helper exists
            transfers = self._extract_transfers(tx_detail) # Use proper extraction method

            tx_hash = tx_detail.get("transaction", {}).get("signatures", [None])[0]
            block_time = tx_detail.get("blockTime")

            for transfer in transfers:
                sender = transfer.get("source")
                receiver = transfer.get("destination")
                amount = transfer.get("amount", 0)
                mint = transfer.get("mint", "SOL") # Default to SOL if mint not present

                if sender and receiver and sender != 'unknown' and receiver != 'unknown':
                    # Add nodes if they don't exist
                    if not G.has_node(sender): G.add_node(sender, type="address")
                    if not G.has_node(receiver): G.add_node(receiver, type="address")

                    # Add edge attributes
                    edge_attrs = {
                        "tx_hash": tx_hash,
                        "amount": amount,
                        "mint": mint,
                        "block_time": block_time
                    }

                    # Update existing edge or add new edge
                    if G.has_edge(sender, receiver):
                        edge_data = G.get_edge_data(sender, receiver)
                        if "transactions" not in edge_data: edge_data["transactions"] = []
                        edge_data["transactions"].append(edge_attrs)
                        edge_data["weight"] = len(edge_data["transactions"])
                        edge_data["total_amount"] = edge_data.get("total_amount", 0) + amount # Simplistic sum
                    else:
                        G.add_edge(sender, receiver,
                                  transactions=[edge_attrs],
                                  weight=1,
                                  total_amount=amount) # Simplistic sum

        logging.info(f"Built graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
        return G

    def build_token_creator_network(self, tokens_analysis: List[Dict]) -> nx.Graph:
        """
        Build a network of token creators and their tokens from analysis results.

        Args:
            tokens_analysis (List[Dict]): List of analysis results from TokenAnalyzer.analyze_token.

        Returns:
            nx.Graph: Token creator network
        """
        G = nx.Graph()
        logging.info(f"Building token creator network from {len(tokens_analysis)} token analyses...")

        for analysis in tokens_analysis:
            token_mint = analysis.get("token_mint")
            token_info = analysis.get("token_info", {})
            creator_info = analysis.get("creator_analysis", {})
            risk_info = analysis.get("risk_assessment", {})
            liquidity_info = analysis.get("liquidity_analysis", {})

            creator_address = creator_info.get("creator_address")

            if token_mint and creator_address:
                # Add token node with attributes
                if not G.has_node(token_mint):
                    G.add_node(token_mint,
                              type="token",
                              symbol=token_info.get("symbol", ""),
                              name=token_info.get("name", ""),
                              price_usd=token_info.get("price_usd"),
                              market_cap=token_info.get("market_cap"),
                              risk_score=risk_info.get("score"),
                              is_verified=risk_info.get("is_verified"),
                              liquidity_usd=liquidity_info.get("total_liquidity_usd"),
                              # Add other relevant attributes
                              )

                # Add creator node with attributes
                if not G.has_node(creator_address):
                    G.add_node(creator_address,
                              type="creator",
                              other_tokens_count=creator_info.get("other_tokens_count"),
                              is_suspicious=creator_info.get("is_suspicious"),
                              # Add labels/entity info if available from creator analysis
                              )

                # Add edge between creator and token
                G.add_edge(creator_address, token_mint, relation="created")

        logging.info(f"Built creator network with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
        return G


    def build_transaction_flow_network(self, start_address: str, depth: int = 2, days_history: int = 30) -> nx.DiGraph:
        """
        Build a transaction flow network starting from an address using Helius.

        Args:
            start_address (str): Starting address
            depth (int, optional): Depth of network to build. Defaults to 2.
            days_history (int): How many days of history to fetch.

        Returns:
            nx.DiGraph: Transaction flow network
        """
        G = nx.DiGraph()
        if not self.helius_client:
            logging.error("Helius client required for transaction flow network.")
            return G

        logging.info(f"Building transaction flow network for {start_address}, depth {depth}, history {days_history} days...")
        queue = [(start_address, 0)] # (address, current_depth)
        processed_addresses = {start_address} # Keep track of visited addresses

        cutoff_time = time.time() - days_history * 86400

        while queue:
            current_address, current_depth = queue.pop(0)

            if current_depth >= depth:
                continue

            # Add node if not already present (might be added as target before processing)
            if not G.has_node(current_address):
                 G.add_node(current_address, type="address", depth=current_depth)
            # Ensure depth is set/updated
            G.nodes[current_address]['depth'] = min(G.nodes[current_address].get('depth', float('inf')), current_depth)


            try:
                # Fetch recent signatures for the current address
                signatures_result = self.helius_client.get_signatures_for_address(current_address, limit=50) # Limit per address/depth
                signatures = signatures_result.get("result", [])
                recent_signatures = [s['signature'] for s in signatures if s.get('blockTime', 0) > cutoff_time]

                if not recent_signatures: continue

                # Fetch details and process transfers
                for sig in recent_signatures:
                    try:
                        tx_detail_res = self.helius_client.get_transaction(sig)
                        tx_detail = tx_detail_res.get("result")
                        if not tx_detail: continue

                        transfers = self._extract_transfers(tx_detail) # Use proper extraction method
                        block_time = tx_detail.get("blockTime")

                        for transfer in transfers:
                            sender = transfer.get("source")
                            receiver = transfer.get("destination")
                            amount = transfer.get("amount", 0)
                            mint = transfer.get("mint", "SOL")

                            if sender == current_address and receiver and receiver != 'unknown':
                                neighbor = receiver
                                direction = 'out'
                            elif receiver == current_address and sender and sender != 'unknown':
                                neighbor = sender
                                direction = 'in'
                            else:
                                continue # Skip if current_address is not sender or receiver

                            # Add neighbor node
                            if not G.has_node(neighbor):
                                 G.add_node(neighbor, type="address", depth=current_depth + 1)

                            # Add edge
                            edge_data = {
                                "tx_hash": sig, "amount": amount, "mint": mint,
                                "block_time": block_time, "direction": direction
                            }
                            # Simple edge representation (could aggregate)
                            G.add_edge(sender, receiver, **edge_data) # Use actual sender/receiver for direction

                            # Add neighbor to queue if depth allows and not processed
                            if neighbor not in processed_addresses and current_depth + 1 < depth:
                                queue.append((neighbor, current_depth + 1))
                                processed_addresses.add(neighbor)

                        time.sleep(0.1) # Rate limit
                    except Exception as tx_err:
                        logging.warning(f"Failed processing tx {sig} for flow network: {tx_err}")

            except Exception as e:
                logging.error(f"Error fetching transactions for {current_address} in flow network: {e}")

        logging.info(f"Built flow network with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
        return G

    def build_token_holder_network(self, token_mint: str, top_n: int = 100) -> nx.Graph:
        """
        Build a network of top token holders for a specific token using Vybe.

        Args:
            token_mint (str): Token mint address
            top_n (int): Number of top holders to include.

        Returns:
            nx.Graph: Token holder network
        """
        G = nx.Graph()
        if not self.vybe_client:
            logging.error("Vybe client required for token holder network.")
            return G

        logging.info(f"Building token holder network for {token_mint} (top {top_n})...")
        try:
            # Get token details (for context)
            token_details = self.vybe_client.get_token_details(token_mint)
            G.add_node(token_mint, type="token", **token_details) # Add details as attributes

            # Get top holders (handle pagination if top_n > Vybe limit)
            holders_data = self.vybe_client.get_token_top_holders(token_mint, query_params={"limit": top_n})
            holders = holders_data.get("data", []) # Adjust key based on Vybe response

            # Add holder nodes and edges
            for holder in holders:
                address = holder.get("address") # Adjust key
                if address:
                    # Add holder node (optionally enrich with Range labels later)
                    G.add_node(address, type="holder")

                    # Add edge with holding details
                    G.add_edge(address, token_mint,
                              amount=holder.get("amount", {}).get("raw"), # Adjust keys
                              ui_amount=holder.get("amount", {}).get("ui"), # Adjust keys
                              percentage=holder.get("percentage", 0)) # Adjust key

            logging.info(f"Built holder network with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

        except Exception as e:
            logging.error(f"Error building token holder network for {token_mint}: {e}")

        return G

    def build_insider_network(self, token_mint: str) -> nx.DiGraph:
        """
        Build an insider network for a token using RugCheck data.

        Args:
            token_mint (str): Token mint address

        Returns:
            nx.DiGraph: Insider network
        """
        G = nx.DiGraph()
        if not self.rugcheck_client:
            logging.error("RugCheck client required for insider network.")
            return G

        logging.info(f"Building insider network for {token_mint} using RugCheck...")
        try:
            # Fetch insider graph data from RugCheck
            insider_data = self.rugcheck_client.get_token_insider_graph(token_mint)

            # Process nodes (assuming RugCheck provides 'nodes' list)
            for node_info in insider_data.get("nodes", []):
                node_id = node_info.get("id") # Assuming 'id' is the address/identifier
                if node_id:
                    # Add node with all other info as attributes
                    attrs = {k: v for k, v in node_info.items() if k != "id"}
                    G.add_node(node_id, **attrs)

            # Process edges (assuming RugCheck provides 'edges' list)
            for edge_info in insider_data.get("edges", []):
                source = edge_info.get("source")
                target = edge_info.get("target")
                if source and target:
                    # Add edge with all other info as attributes
                    attrs = {k: v for k, v in edge_info.items() if k not in ["source", "target"]}
                    G.add_edge(source, target, **attrs)

            logging.info(f"Built insider network with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

        except Exception as e:
            logging.error(f"Error building insider network for {token_mint}: {e}")

        return G

    def export_graph_to_json(self, G: nx.Graph, filename: str) -> None:
        """
        Export NetworkX graph to JSON for visualization.
        
        Args:
            G (nx.Graph): NetworkX graph
            filename (str): Output filename
        """
        # Convert NetworkX graph to node-link format
        data = nx.node_link_data(G)
        
        # Write to JSON file
        with open(filename, 'w') as f:
            json.dump(data, f)
    
    def export_graph_to_d3_format(self, G: nx.Graph, filename: str) -> None:
        """
        Export NetworkX graph to D3.js-compatible JSON.
        
        Args:
            G (nx.Graph): NetworkX graph
            filename (str): Output filename
        """
        # Extract nodes and links in D3 format
        nodes = []
        for node, attrs in G.nodes(data=True):
            node_data = {"id": node}
            node_data.update(attrs)
            nodes.append(node_data)
        
        links = []
        for source, target, attrs in G.edges(data=True):
            link_data = {"source": source, "target": target}
            link_data.update(attrs)
            links.append(link_data)
        
        # Create D3 compatible data
        d3_data = {
            "nodes": nodes,
            "links": links
        }
        
        # Write to JSON file
        with open(filename, 'w') as f:
            json.dump(d3_data, f)
    
    # Helper methods
    
    def _extract_sender(self, tx: Dict) -> Optional[str]:
        """Extract sender address from transaction."""
        # Different APIs may format this differently
        if "sender" in tx:
            sender = tx.get("sender")
            if isinstance(sender, dict):
                return sender.get("wallet")
            return sender
        
        # Check common fields
        for field in ["from", "source", "authority"]:
            if field in tx:
                value = tx.get(field)
                if isinstance(value, dict):
                    return value.get("wallet")
                return value
        
        return None
    
    def _extract_receiver(self, tx: Dict) -> Optional[str]:
        """Extract receiver address from transaction."""
        # Different APIs may format this differently
        if "receiver" in tx:
            receiver = tx.get("receiver")
            if isinstance(receiver, dict):
                return receiver.get("wallet")
            return receiver
        
        # Check common fields
        for field in ["to", "destination", "recipient"]:
            if field in tx:
                value = tx.get(field)
                if isinstance(value, dict):
                    return value.get("wallet")
                return value
        
        return None
    
    def _extract_amount(self, tx: Dict) -> float:
        """Extract amount from transaction."""
        # Different APIs may format this differently
        for field in ["amount", "amount_usd", "value", "lamports"]:
            if field in tx:
                return float(tx.get(field, 0))
        
        return 0.0
    
    def _build_flow_network_recursive(self, G: nx.DiGraph, address: str, max_depth: int, 
                                    current_depth: int, processed: set) -> None:
        """
        Recursively build transaction flow network.
        
        Args:
            G (nx.DiGraph): NetworkX graph
            address (str): Current address
            max_depth (int): Maximum depth to explore
            current_depth (int): Current depth
            processed (set): Set of processed addresses
        """
        # Stop if we've reached max depth or already processed this address
        if current_depth >= max_depth or address in processed:
            return
        
        # Mark as processed
        processed.add(address)
        
        # Get transactions for this address if Range client is available
        if not self.range_client:
            return
        
        try:
            tx_data = self.range_client.get_address_transactions(address)
            transactions = tx_data.get("transactions", [])
            
            for tx in transactions:
                sender = self._extract_sender(tx)
                receiver = self._extract_receiver(tx)
                
                # Skip if sender or receiver is None or same as current address
                if not sender or not receiver:
                    continue
                
                # Determine outgoing or incoming
                if sender == address:
                    # Outgoing transaction
                    if not G.has_node(receiver):
                        G.add_node(receiver, type="address", depth=current_depth+1)
                    
                    # Add edge
                    amount = self._extract_amount(tx)
                    tx_hash = tx.get("signature") or tx.get("tx_hash")
                    block_time = tx.get("block_time")
                    
                    G.add_edge(sender, receiver, tx_hash=tx_hash, 
                              amount=amount, block_time=block_time,
                              depth=current_depth)
                    
                    # Recursive call for outgoing address
                    self._build_flow_network_recursive(G, receiver, max_depth, 
                                                    current_depth+1, processed)
        
        except Exception as e:
            print(f"Error in recursive network building: {str(e)}")

    def _extract_transfers(self, tx_detail: Dict) -> List[Dict]:
        """
        Extract all transfers (SOL and tokens) from transaction details.
        Handles both outer and inner instructions, including DEX operations.
        
        Args:
            tx_detail (Dict): Transaction details from Helius API
            
        Returns:
            List[Dict]: List of transfer objects with standardized fields
        """
        transfers = []
        meta = tx_detail.get("meta", {})
        instructions = tx_detail.get("transaction", {}).get("message", {}).get("instructions", [])
        inner_instructions = meta.get("innerInstructions", [])
        account_keys = tx_detail.get("transaction", {}).get("message", {}).get("accountKeys", [])
        log_messages = meta.get("logMessages", [])
        
        # Process outer instructions
        for ix_idx, ix in enumerate(instructions):
            program_id_idx = ix.get("programIdIndex")
            if program_id_idx is None or program_id_idx >= len(account_keys):
                continue
                
            program_id = account_keys[program_id_idx]
            
            # Parse different program instructions
            if program_id == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":  # SPL Token program
                self._extract_spl_token_transfers(ix, account_keys, transfers)
            elif program_id == "11111111111111111111111111111111":  # System program
                self._extract_system_transfers(ix, account_keys, transfers)
            
            # Process corresponding inner instructions
            for inner_ix_group in inner_instructions:
                if inner_ix_group.get("index") == ix_idx:
                    for inner_ix in inner_ix_group.get("instructions", []):
                        inner_program_id_idx = inner_ix.get("programIdIndex")
                        if inner_program_id_idx is None or inner_program_id_idx >= len(account_keys):
                            continue
                            
                        inner_program_id = account_keys[inner_program_id_idx]
                        
                        if inner_program_id == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":
                            self._extract_spl_token_transfers(inner_ix, account_keys, transfers)
                        elif inner_program_id == "11111111111111111111111111111111":
                            self._extract_system_transfers(inner_ix, account_keys, transfers)
        
        # Look for balance changes to catch any transfers we missed through instruction parsing
        self._extract_transfers_from_balance_changes(meta, account_keys, transfers)
        
        return transfers
    
    def _extract_spl_token_transfers(self, instruction: Dict, account_keys: List[str], transfers: List[Dict]) -> None:
        """Extract SPL token transfers from an instruction."""
        parsed = instruction.get("parsed", {})
        info = parsed.get("info", {})
        ix_type = parsed.get("type")
        
        if ix_type in ["transfer", "transferChecked"]:
            amount = 0
            if "amount" in info:
                amount = int(info.get("amount", "0"))
            elif "tokenAmount" in info:
                amount = int(info.get("tokenAmount", {}).get("amount", "0"))
            
            transfers.append({
                "type": "SPL",
                "mint": info.get("mint"),
                "source": info.get("source"),
                "destination": info.get("destination"),
                "authority": info.get("authority"),
                "amount": amount
            })
    
    def _extract_system_transfers(self, instruction: Dict, account_keys: List[str], transfers: List[Dict]) -> None:
        """Extract SOL transfers from System Program instructions."""
        parsed = instruction.get("parsed", {})
        info = parsed.get("info", {})
        ix_type = parsed.get("type")
        
        if ix_type == "transfer" or ix_type == "transferWithSeed":
            transfers.append({
                "type": "SOL",
                "mint": "SOL",  # Native SOL
                "source": info.get("source"),
                "destination": info.get("destination"),
                "amount": int(info.get("lamports", 0))
            })
    
    def _extract_transfers_from_balance_changes(self, meta: Dict, account_keys: List[str], transfers: List[Dict]) -> None:
        """Extract transfers from token balance changes when instruction parsing misses them."""
        pre_balances = meta.get("preTokenBalances", [])
        post_balances = meta.get("postTokenBalances", [])
        
        # Create maps for pre and post balances
        pre_map = {}  # {owner: {mint: {account_idx: amount}}}
        post_map = {}  # {owner: {mint: {account_idx: amount}}}
        
        for bal in pre_balances:
            owner = bal.get("owner")
            mint = bal.get("mint")
            idx = bal.get("accountIndex")
            amount = int(bal.get("uiTokenAmount", {}).get("amount", "0"))
            
            if owner and mint:
                if owner not in pre_map:
                    pre_map[owner] = {}
                if mint not in pre_map[owner]:
                    pre_map[owner][mint] = {}
                pre_map[owner][mint][idx] = amount
        
        for bal in post_balances:
            owner = bal.get("owner")
            mint = bal.get("mint")
            idx = bal.get("accountIndex")
            amount = int(bal.get("uiTokenAmount", {}).get("amount", "0"))
            
            if owner and mint:
                if owner not in post_map:
                    post_map[owner] = {}
                if mint not in post_map[owner]:
                    post_map[owner][mint] = {}
                post_map[owner][mint][idx] = amount
        
        # Detect transfers by comparing pre and post balances
        processed_pairs = set()  # Track processed (source, destination, mint) to avoid duplicates
        
        for owner, mints in post_map.items():
            for mint, accounts in mints.items():
                for acc_idx, post_amount in accounts.items():
                    pre_amount = pre_map.get(owner, {}).get(mint, {}).get(acc_idx, 0)
                    change = post_amount - pre_amount
                    
                    if change > 0:  # Received tokens
                        # Find who sent these tokens by looking for negative changes
                        for source_owner, source_mints in pre_map.items():
                            if source_owner == owner:  # Skip self-transfers within different accounts
                                continue
                                
                            if mint in source_mints:
                                for s_idx, s_pre_amount in source_mints[mint].items():
                                    s_post_amount = post_map.get(source_owner, {}).get(mint, {}).get(s_idx, 0)
                                    source_change = s_post_amount - s_pre_amount
                                    
                                    # Found matching negative change (allowing for fees)
                                    if source_change < 0 and abs(source_change) >= change and \
                                       (source_owner, owner, mint) not in processed_pairs:
                                        transfers.append({
                                            "type": "SPL",
                                            "mint": mint,
                                            "source": source_owner,
                                            "destination": owner,
                                            "amount": change,
                                            "detected_from_balances": True
                                        })
                                        processed_pairs.add((source_owner, owner, mint))
                                        break