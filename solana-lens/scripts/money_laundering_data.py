#!/usr/bin/env python3
"""
Money Laundering Data Collection Script

This script collects and analyzes data related to potential money laundering
patterns on Solana using the Range, Helius, RugCheck, and Vybe APIs.
"""

import os
import json
import time
import argparse
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import asyncio # For potential async operations

# Import custom API clients
from collectors.range_client import RangeClient
from collectors.helius_client import HeliusClient
from collectors.rug_check_client import RugCheckClient
from collectors.vybe_client import VybeClient

# Import specialized collectors
from collectors.mixer_collector import MixerCollector
from collectors.address_poisoning_collector import AddressPoisoningCollector
from collectors.transaction_collector import TransactionCollector
from collectors.sandwich_collector import SandwichCollector

# Import analysis utilities
from analysis.address_analyzer import AddressAnalyzer
from analysis.network_builder import NetworkBuilder
from export.data_exporter import DataExporter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set up command line arguments
parser = argparse.ArgumentParser(description='Collect and analyze money laundering data on Solana')
parser.add_argument('--output-dir', type=str, default='data/money_laundering', 
                   help='Directory to save output data')
parser.add_argument('--addresses', type=str, default=None,
                   help='File containing addresses to analyze (JSON)')
parser.add_argument('--days', type=int, default=30,
                   help='Number of days of history to analyze')
parser.add_argument('--mixer-analysis', action='store_true',
                   help='Perform mixer service analysis')
parser.add_argument('--bridge-analysis', action='store_true',
                   help='Perform cross-chain bridge analysis')
parser.add_argument('--address-poisoning', action='store_true',
                   help='Analyze address poisoning attempts')
parser.add_argument('--verbose', action='store_true',
                   help='Enable verbose output')
args = parser.parse_args()

# Ensure output directory exists
os.makedirs(args.output_dir, exist_ok=True)

# Load API keys from environment variables
range_api_key = os.environ.get('RANGE_API_KEY')
helius_api_key = os.environ.get('HELIUS_API_KEY')
rugcheck_jwt_token = os.environ.get('RUGCHECK_JWT_TOKEN')
vybe_api_key = os.environ.get('VYBE_API_KEY')

# Initialize API clients
logging.info("Initializing API clients...")
try:
    range_client = RangeClient(range_api_key) if range_api_key else None
    logging.info(f"RangeClient initialized: {'Yes' if range_client else 'No'}")
except Exception as e:
    logging.error(f"Failed to initialize RangeClient: {e}")
    range_client = None

try:
    helius_client = HeliusClient(helius_api_key) if helius_api_key else None
    logging.info(f"HeliusClient initialized: {'Yes' if helius_client else 'No'}")
except Exception as e:
    logging.error(f"Failed to initialize HeliusClient: {e}")
    helius_client = None

try:
    rugcheck_client = RugCheckClient(rugcheck_jwt_token) if rugcheck_jwt_token else None
    logging.info(f"RugCheckClient initialized: {'Yes' if rugcheck_client else 'No'}")
except Exception as e:
    logging.error(f"Failed to initialize RugCheckClient: {e}")
    rugcheck_client = None

try:
    vybe_client = VybeClient(vybe_api_key) if vybe_api_key else None
    logging.info(f"VybeClient initialized: {'Yes' if vybe_client else 'No'}")
except Exception as e:
    logging.error(f"Failed to initialize VybeClient: {e}")
    vybe_client = None

# Initialize collectors
transaction_collector = TransactionCollector(helius_client=helius_client, range_client=range_client)
mixer_collector = MixerCollector(helius_client=helius_client, range_client=range_client, vybe_client=vybe_client)
address_poisoning_collector = AddressPoisoningCollector(helius_client=helius_client)
sandwich_collector = SandwichCollector(helius_client=helius_client)

# Initialize analysis utilities - still helpful for complex analysis
address_analyzer = AddressAnalyzer(
    range_client=range_client,
    helius_client=helius_client,
    rugcheck_client=rugcheck_client,
    vybe_client=vybe_client,
    fetch_detailed_txs=True # Add flag to fetch full details in analyzer
)

network_builder = NetworkBuilder(
    range_client=range_client,
    helius_client=helius_client,
    rugcheck_client=rugcheck_client,
    vybe_client=vybe_client
)

# Initialize data exporter
data_exporter = DataExporter(output_dir=args.output_dir)

# Load addresses to analyze
addresses_to_analyze = []
if args.addresses:
    try:
        with open(args.addresses, 'r') as f:
            addresses_data = json.load(f)
            
        if isinstance(addresses_data, list):
            addresses_to_analyze = addresses_data
        elif isinstance(addresses_data, dict) and 'addresses' in addresses_data:
            addresses_to_analyze = addresses_data['addresses']
            
        logging.info(f"Loaded {len(addresses_to_analyze)} addresses for analysis")
    except Exception as e:
        logging.error(f"Error loading addresses file: {str(e)}")

# If no addresses provided, use some known high-risk addresses
# In a real implementation, these would be sourced from the APIs or a database
if not addresses_to_analyze:
    logging.info("No addresses provided, using sample high-risk addresses")
    addresses_to_analyze = [
        # These are example addresses and would be replaced with real data
        "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin",
        "VinesRG7K3ubzKLbxXz197c1RHV3cACkvGr9Zca7BSw",
        "tor1xzb2Zyy1cUxXmyJfR8aNXuWnwHG8AwgaG7UGD4K"
    ]

# Main collection functions

async def collect_address_data(address: str) -> Dict:
    """
    Collect comprehensive data about an address using TransactionCollector.
    Ensures detailed transaction info is fetched if needed.
    """
    logging.info(f"Analyzing address: {address}")
    try:
        # Use the transaction collector instead of analyzer directly
        analysis_result = await transaction_collector.fetch_address_data(address, fetch_details=True)
        return analysis_result
    except Exception as e:
        logging.error(f"Error collecting data for address {address}: {e}")
        return {
            "address": address,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

async def perform_mixer_analysis_enhanced() -> Dict:
    """Enhanced mixer analysis using the MixerCollector."""
    logging.info("Performing enhanced mixer service analysis...")
    
    if not mixer_collector:
        return {
            "mixer_services_summary": [],
            "potential_mixer_users": [],
            "error": "MixerCollector not initialized"
        }
    
    # Use the dedicated mixer collector
    return await mixer_collector.analyze_mixers(limit_per_mixer=500)

async def analyze_address_poisoning_enhanced() -> Dict:
    """Enhanced address poisoning analysis using AddressPoisoningCollector."""
    logging.info("Analyzing address poisoning attempts (enhanced)...")
    
    if not address_poisoning_collector:
        return {
            "potential_poisoning_txs": [],
            "statistics": {"checked_tx_count": 0, "potential_count": 0},
            "error": "AddressPoisoningCollector not initialized"
        }
    
    # Collect transactions for the addresses we're analyzing
    transactions_to_check = await address_poisoning_collector.collect_address_transactions(
        [data.get('address') for data in address_data_list if data.get('address') and 'error' not in data]
    )
    
    # Analyze the transactions
    return await address_poisoning_collector.analyze_poisoning_attempts(transactions_to_check)

def create_transaction_graph(address_data_list: List[Dict]) -> Dict:
    """
    Create a transaction graph from collected address data.
    """
    logging.info("Creating transaction graph from collected data...")
    all_transactions_details = []

    for data in address_data_list:
        # Check if detailed transactions are stored directly 
        if data and "error" not in data:
             # Assuming details are stored under a key like 'detailed_transactions'
             details = data.get("detailed_transactions", [])
             if not details and "transaction_summary" in data:
                  logging.warning(f"Detailed transactions not found for {data.get('address')}, graph may be incomplete.")
             all_transactions_details.extend(details)

    if not all_transactions_details:
         logging.warning("No transaction details available to build graph. Graph will be empty.")
         return {"nodes": [], "links": [], "message": "No transaction details found."}

    # Deduplicate transactions by signature
    unique_transactions = {tx.get("transaction", {}).get("signatures", [None])[0]: tx
                           for tx in all_transactions_details if tx.get("transaction", {}).get("signatures", [None])[0]}

    logging.info(f"Building graph from {len(unique_transactions)} unique transactions...")
    
    # Use TransactionCollector to build the graph
    graph_data = transaction_collector.build_transaction_graph(list(unique_transactions.values()))
    
    logging.info(f"Created graph with {len(graph_data['nodes'])} nodes and {len(graph_data['links'])} links.")
    return graph_data

# --- Main Execution ---
async def main():
    logging.info("Starting data collection process")
    global address_data_list # Use the global list modified in the loop
    address_data_list = []

    # Collect data for each address using the transaction collector
    for address in addresses_to_analyze:
        try:
            data = await collect_address_data(address)
            address_data_list.append(data)
            time.sleep(0.2)  # Small wait between addresses
        except Exception as e:
            logging.error(f"Error processing address {address}: {str(e)}")

    # Perform additional analyses concurrently using specialized collectors
    mixer_task = asyncio.create_task(perform_mixer_analysis_enhanced()) if args.mixer_analysis else None
    # bridge_task = asyncio.create_task(perform_bridge_analysis_enhanced()) if args.bridge_analysis else None # Add enhanced version
    poisoning_task = asyncio.create_task(analyze_address_poisoning_enhanced()) if args.address_poisoning else None

    results = {
        "addresses_analyzed": address_data_list,
        "mixer_analysis": await mixer_task if mixer_task else {},
        # "bridge_analysis": await bridge_task if bridge_task else {},
        "bridge_analysis": {}, # Placeholder until enhanced bridge analysis is added
        "address_poisoning": await poisoning_task if poisoning_task else {}
    }

    # Create transaction graph using the transaction collector
    transaction_graph = create_transaction_graph(address_data_list)
    results["transaction_graph"] = transaction_graph

    # Save results
    logging.info("Saving final results")

    # Save complete results
    data_exporter.export_json(results, "money_laundering_analysis_results.json")

    # Export specific datasets for visualizations
    if transaction_graph and transaction_graph.get("nodes"):
        data_exporter.export_graph_data(
            nodes=transaction_graph.get("nodes", []),
            links=transaction_graph.get("links", []),
            name="money_laundering",
            metadata={
                "description": "Money laundering transaction graph",
                "address_count": len(addresses_to_analyze),
                "generated_at": datetime.now().isoformat()
            }
        )

    # Export mixer analysis data if available
    if args.mixer_analysis and results.get("mixer_analysis"):
        data_exporter.export_for_visualization(
            results["mixer_analysis"],
            "mixer_analysis",
            "mixer"
        )

    # Export address poisoning data if available
    if args.address_poisoning and results.get("address_poisoning"):
        data_exporter.export_for_visualization(
            results["address_poisoning"],
            "address_poisoning",
            "security"
        )

    logging.info("Data collection and analysis complete")

if __name__ == "__main__":
    # Run the main function in an event loop
    asyncio.run(main())