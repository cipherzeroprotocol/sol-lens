/**
 * SolanaLens - Main Entry Point
 * 
 * This module initializes the SolanaLens application by setting up API clients
 * and data collectors, making them available for visualizations and reports.
 */

import { HeliusClient } from './scripts/api/helius-client.js';
import { RangeClient } from './scripts/api/range-client.js';
import * as collectors from './scripts/collectors/index.js';

// Create the main SolanaLens object
const SolanaLens = {
  // API clients
  clients: {
    helius: null,
    range: null
  },
  
  // Data collectors
  collectors,
  
  // Initialize the application with API keys
  init(config = {}) {
    console.log('Initializing SolanaLens...');
    
    // Initialize API clients
    const heliusApiKey = config.apiKeys?.helius || 'demo';
    const rangeApiKey = config.apiKeys?.range || 'demo';
    
    this.clients.helius = new HeliusClient(heliusApiKey);
    this.clients.range = new RangeClient(rangeApiKey);
    
    // Store API keys in environment variables or global scope
    if (typeof process !== 'undefined' && process.env) {
      process.env.HELIUS_API_KEY = heliusApiKey;
      process.env.RANGE_API_KEY = rangeApiKey;
    } else if (typeof window !== 'undefined') {
      window.SOLANA_LENS_CONFIG = {
        apiKeys: {
          helius: heliusApiKey,
          range: rangeApiKey
        }
      };
    }
    
    console.log('SolanaLens initialized successfully.');
    return true;
  },
  
  // Get version info
  version: {
    number: '0.1.0',
    name: 'Alpha',
    buildDate: new Date().toISOString()
  },
  
  // Check if using demo mode or real API keys
  isUsingRealApis() {
    return !(this.clients.helius.isDemoMode && this.clients.range.isDemoMode);
  }
};

// Export SolanaLens
export default SolanaLens;

// Attach to window object in browser
if (typeof window !== 'undefined') {
  window.SolanaLens = SolanaLens;
  
  // Auto-initialize with any provided API keys
  document.addEventListener('DOMContentLoaded', () => {
    const apiKeyElements = {
      helius: document.querySelector('meta[name="helius-api-key"]'),
      range: document.querySelector('meta[name="range-api-key"]')
    };
    
    const apiKeys = {};
    if (apiKeyElements.helius) apiKeys.helius = apiKeyElements.helius.getAttribute('content');
    if (apiKeyElements.range) apiKeys.range = apiKeyElements.range.getAttribute('content');
    
    SolanaLens.init({ apiKeys });
  });
}
