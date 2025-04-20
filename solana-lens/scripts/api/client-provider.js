/**
 * API Client Provider
 * 
 * Central module that initializes and provides API clients
 * for use throughout the application.
 */

import { HeliusClient } from './helius-client.js';
import { RangeClient } from './range-client.js';

class ClientProvider {
  constructor() {
    this._initialized = false;
    this._clients = {
      helius: null,
      range: null
    };
  }
  
  /**
   * Initialize API clients with provided keys
   * @param {Object} config - Configuration with API keys
   */
  init(config = {}) {
    // Extract API keys from config
    const heliusApiKey = this._getApiKey('helius', config);
    const rangeApiKey = this._getApiKey('range', config);
    
    // Create API clients
    this._clients.helius = new HeliusClient(heliusApiKey);
    this._clients.range = new RangeClient(rangeApiKey);
    
    this._initialized = true;
    return this;
  }
  
  /**
   * Get API key from config or environment
   * @private
   * @param {string} name - Name of the API
   * @param {Object} config - Configuration object
   * @returns {string} - API key
   */
  _getApiKey(name, config) {
    // Check config object first
    if (config.apiKeys && config.apiKeys[name]) {
      return config.apiKeys[name];
    }
    
    // Check environment variables
    if (typeof process !== 'undefined' && process.env) {
      const envKey = process.env[`${name.toUpperCase()}_API_KEY`];
      if (envKey) {
        return envKey;
      }
    }
    
    // Check window object for browser environment
    if (typeof window !== 'undefined' && window.SOLANA_LENS_CONFIG) {
      const browserKey = window.SOLANA_LENS_CONFIG.apiKeys?.[name];
      if (browserKey) {
        return browserKey;
      }
    }
    
    // Use demo mode if no key provided
    console.warn(`No API key provided for ${name}, using demo mode`);
    return 'demo';
  }
  
  /**
   * Get the Helius API client
   * @returns {HeliusClient} - Helius client
   */
  get helius() {
    if (!this._initialized) {
      this.init();
    }
    return this._clients.helius;
  }
  
  /**
   * Get the Range API client
   * @returns {RangeClient} - Range client
   */
  get range() {
    if (!this._initialized) {
      this.init();
    }
    return this._clients.range;
  }
  
  /**
   * Check if using real APIs
   * @returns {boolean} - Whether real API access is available
   */
  hasRealApiAccess() {
    if (!this._initialized) {
      this.init();
    }
    
    return !(this._clients.helius.isDemoMode && this._clients.range.isDemoMode);
  }
}

// Create and export singleton instance
export const clientProvider = new ClientProvider();

// Default export for convenience
export default clientProvider;
