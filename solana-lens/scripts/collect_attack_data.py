import os
import json
import logging
import argparse
from datetime import datetime

# Import custom API clients
from collectors.helius_client import HeliusClient
# Import analysis utilities
from analysis.sandwich_detector import SandwichDetector
from export.data_exporter import DataExporter # Assuming this exists for saving

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Argument Parsing ---
parser = argparse.ArgumentParser(description='Detect and collect sandwich attack data on Solana.')
parser.add_argument('--output-dir', type=str, default='data/attacks', help='Directory to save output data.')
parser.add_argument('--time-window', type=int, default=15, help='Time window in minutes to look back for attacks.')
parser.add_argument('--filename', type=str, default='sandwich_attacks.json', help='Output JSON filename.')
args = parser.parse_args()

# --- Initialization ---
logging.info("Initializing...")
os.makedirs(args.output_dir, exist_ok=True)

# Load API keys
helius_api_key = os.environ.get('HELIUS_API_KEY')
if not helius_api_key:
    logging.error("HELIUS_API_KEY environment variable not set. Exiting.")
    exit(1)

# Initialize clients and detector
try:
    helius_client = HeliusClient(helius_api_key)
    sandwich_detector = SandwichDetector(helius_client=helius_client)
    # Assuming DataExporter exists and has a save_json method
    exporter = DataExporter(args.output_dir)
except Exception as e:
    logging.error(f"Failed to initialize clients or detector: {e}")
    exit(1)

# --- Main Detection Logic ---
logging.info(f"Starting sandwich attack detection (window: {args.time_window} mins)...")

try:
    detected_attacks = sandwich_detector.detect_sandwich_attacks(
        time_window_minutes=args.time_window
    )
    logging.info(f"Detection finished. Found {len(detected_attacks)} potential attacks.")

    # --- Save Data ---
    output_path = os.path.join(args.output_dir, args.filename)
    logging.info(f"Saving detected attacks to {output_path}...")
    # Use exporter or simple json dump
    try:
        with open(output_path, 'w') as f:
            json.dump(detected_attacks, f, indent=2)
        # exporter.save_json(detected_attacks, args.filename) # If using exporter
        logging.info("Data saved successfully.")
    except Exception as e:
        logging.error(f"Failed to save data: {e}")

except Exception as e:
    logging.error(f"An error occurred during sandwich detection: {e}")

logging.info("Script finished.")
