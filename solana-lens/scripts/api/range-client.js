/**
 * Range API Client
 * 
 * Client for interacting with Range API for cross-chain data and risk assessment
 */

import fetch from 'isomorphic-fetch';

export class RangeClient {
  /**
   * Create a new RangeClient
   * @param {string} apiKey - Range API key
   * @param {string} baseUrl - Base URL for the Range API
   */
  constructor(apiKey, baseUrl = 'https://api.range.org') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    this.isDemoMode = apiKey === 'demo';
    
    if (this.isDemoMode) {
      console.warn('RangeClient initialized in demo mode. API functionality will be limited.');
    }
  }

  /**
   * Get transactions by address across multiple chains
   * @param {string} address - Wallet address
   * @param {Object} options - Query options
   * @returns {Promise<Object>} - Transaction data
   */
  async getTransactionsByAddress(address, options = {}) {
    const params = new URLSearchParams({
      address,
      ...options
    }).toString();
    
    return this._makeRequest(`/transactions?${params}`);
  }

  /**
   * Check risk score for an address
   * @param {string} address - Wallet address to check
   * @param {string} chain - Blockchain name (e.g., 'solana', 'ethereum')
   * @returns {Promise<Object>} - Risk assessment data
   */
  async getRiskScore(address, chain = 'solana') {
    return this._makeRequest(`/risk/${chain}/${address}`);
  }

  /**
   * Get bridging activity for an address
   * @param {string} address - Wallet address
   * @param {Object} options - Query options
   * @returns {Promise<Object>} - Bridging activity data
   */
  async getBridgeActivity(address, options = {}) {
    const params = new URLSearchParams({
      address,
      ...options
    }).toString();
    
    return this._makeRequest(`/bridges/activity?${params}`);
  }

  /**
   * Get sanctioned addresses list
   * @returns {Promise<Array>} - List of sanctioned addresses
   */
  async getSanctionedAddresses() {
    return this._makeRequest('/risk/sanctioned');
  }

  /**
   * Make a request to the Range API
   * @private
   * @param {string} path - API endpoint path
   * @param {string} method - HTTP method (GET, POST, etc)
   * @param {Object} body - Request body for POST requests
   * @returns {Promise<any>} - API response
   */
  async _makeRequest(path, method = 'GET', body = null) {
    if (this.isDemoMode) {
      return this._getMockResponse(path, method, body);
    }

    const url = `${this.baseUrl}${path}`;
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey
      }
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(url, options);
      
      if (!response.ok) {
        throw new Error(`Range API responded with status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Range API request failed: ${error.message}`);
      throw error;
    }
  }

  /**
   * Provide mock responses for demo mode
   * @private
   * @param {string} path - API endpoint path
   * @param {string} method - HTTP method
   * @param {Object} body - Request body
   * @returns {Promise<Object>} - Mock response data
   */
  async _getMockResponse(path, method, body) {
    // Return limited mock data for demo mode
    if (path.includes('/transactions')) {
      return {
        transactions: [
          // Sample cross-chain transactions
          {
            hash: 'mock_tx_hash_1',
            from: 'mock_address_1',
            to: 'mock_address_2',
            chain: 'solana',
            amount: 10,
            token: 'SOL',
            timestamp: Date.now() - 100000
          }
        ]
      };
    }
    
    if (path.includes('/risk/')) {
      return {
        address: path.split('/').pop(),
        risk_score: 0.5,
        risk_factors: ['exchange_interaction']
      };
    }
    
    if (path.includes('/bridges/activity')) {
      return {
        activity: [
          {
            source_chain: 'solana',
            destination_chain: 'ethereum',
            bridge: 'wormhole',
            amount: 5.5,
            token: 'SOL',
            timestamp: Date.now() - 150000
          }
        ]
      };
    }
    
    return {}; // Default empty response
  }
}
