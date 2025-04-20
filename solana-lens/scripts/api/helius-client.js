/**
 * Helius API Client
 * 
 * Client for interacting with Helius API to fetch Solana data
 */

import fetch from 'isomorphic-fetch';

export class HeliusClient {
  /**
   * Create a new HeliusClient
   * @param {string} apiKey - Helius API key
   * @param {string} baseUrl - Base URL for the Helius API
   */
  constructor(apiKey, baseUrl = 'https://api.helius-rpc.com/v0') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    this.isDemoMode = apiKey === 'demo';
    
    if (this.isDemoMode) {
      console.warn('HeliusClient initialized in demo mode. API functionality will be limited.');
    }
  }

  /**
   * Get transaction details for a given signature
   * @param {string} signature - Transaction signature
   * @returns {Promise<Object>} - Transaction details
   */
  async getTransaction(signature) {
    return this._makeRequest(`/transactions/${signature}`);
  }

  /**
   * Get transaction details for a given signature (async version)
   * @param {string} signature - Transaction signature
   * @returns {Promise<Object>} - Transaction details
   */
  async getTransactionAsync(signature) {
    return this.getTransaction(signature);
  }

  /**
   * Get signatures for an address
   * @param {string} address - Account address
   * @param {Object} options - Options for the request
   * @returns {Promise<Object>} - Signature information
   */
  async getSignaturesForAddress(address, options = {}) {
    const params = new URLSearchParams(options).toString();
    return this._makeRequest(`/addresses/${address}/transactions?${params}`);
  }

  /**
   * Get signatures for an address (async version)
   * @param {string} address - Account address
   * @param {Object} options - Options for the request
   * @returns {Promise<Object>} - Signature information
   */
  async getSignaturesForAddressAsync(address, options = {}) {
    return this.getSignaturesForAddress(address, options);
  }

  /**
   * Get parsed transaction details with enhanced data
   * @param {string} signature - Transaction signature
   * @returns {Promise<Object>} - Enhanced transaction details
   */
  async getEnhancedTransaction(signature) {
    return this._makeRequest(`/transactions/parsed/${signature}`);
  }

  /**
   * Search for transactions by specified filters
   * @param {Object} query - Search query parameters
   * @returns {Promise<Array>} - Matching transactions
   */
  async searchTransactions(query) {
    return this._makeRequest('/transactions/search', 'POST', query);
  }

  /**
   * Make a request to the Helius API
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

    const url = `${this.baseUrl}${path}${path.includes('?') ? '&' : '?'}api-key=${this.apiKey}`;
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(url, options);
      
      if (!response.ok) {
        throw new Error(`Helius API responded with status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Helius API request failed: ${error.message}`);
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
    if (path.includes('/transactions/search')) {
      return {
        result: [
          // Sample transaction data
          { /* mock transaction data */ }
        ]
      };
    }
    
    if (path.includes('/transactions/')) {
      return {
        result: { /* mock single transaction data */ }
      };
    }
    
    if (path.includes('/addresses/')) {
      return {
        result: [
          // Sample signatures
          { signature: 'mock_signature_1', blockTime: Date.now() - 100000 },
          { signature: 'mock_signature_2', blockTime: Date.now() - 200000 }
        ]
      };
    }
    
    return { result: [] }; // Default empty response
  }
}
