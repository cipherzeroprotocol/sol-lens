/**
 * Collector Connector
 * 
 * This module provides access to data collectors from visualization components.
 * It handles the integration between notebooks/visualizations and data collectors.
 */

import { 
  bridgeCollector, 
  dustingCollector, 
  sandwichCollector, 
  tokenNetworkCollector,
  stakingCollector,
  hasRealApiAccess
} from '../../scripts/collectors/index.js';

// Map collector names to actual collector instances
const collectors = {
  bridge: bridgeCollector,
  dusting: dustingCollector,
  sandwich: sandwichCollector,
  tokenNetwork: tokenNetworkCollector,
  staking: stakingCollector
};

/**
 * Fetch data from a collector with caching
 * @param {string} collectorName - Name of the collector
 * @param {string} method - Method to call on the collector
 * @param {Array} args - Arguments to pass to the method
 */
export async function fetchFromCollector(collectorName, method, ...args) {
  try {
    // Check if we have the collector
    const collector = collectors[collectorName];
    if (!collector) {
      throw new Error(`Collector '${collectorName}' not found`);
    }

    // Check if the collector has the requested method
    if (!collector[method] || typeof collector[method] !== 'function') {
      throw new Error(`Method '${method}' not found on collector '${collectorName}'`);
    }

    // Check if we're using real API access
    if (!hasRealApiAccess()) {
      console.warn(`Using demo API keys for ${collectorName}. Data may be limited.`);
    }

    // Cache key for storing results
    const cacheKey = `solana_lens_${collectorName}_${method}_${JSON.stringify(args)}`;
    
    // Check cache first (if in browser environment)
    if (typeof localStorage !== 'undefined') {
      const cachedData = localStorage.getItem(cacheKey);
      if (cachedData) {
        try {
          const { data, timestamp } = JSON.parse(cachedData);
          // Cache valid for 1 hour
          if (Date.now() - timestamp < 60 * 60 * 1000) {
            console.log(`Using cached data for ${collectorName}.${method}`);
            return data;
          }
        } catch (e) {
          console.warn('Cache parse error', e);
        }
      }
    }

    // Call the collector method with the provided arguments
    console.log(`Fetching data from ${collectorName}.${method}...`);
    const result = await collector[method](...args);
    
    // Save to cache if in browser environment
    if (typeof localStorage !== 'undefined' && result) {
      try {
        localStorage.setItem(cacheKey, JSON.stringify({
          data: result,
          timestamp: Date.now()
        }));
      } catch (e) {
        console.warn('Cache save error', e);
      }
    }

    return result;
  } catch (error) {
    console.error(`Error fetching from ${collectorName}.${method}:`, error);
    throw error;
  }
}

/**
 * Check if a collector is available
 * @param {string} collectorName - Name of the collector to check
 */
export function hasCollector(collectorName) {
  return !!collectors[collectorName];
}

/**
 * Get list of available collectors
 */
export function getAvailableCollectors() {
  return Object.keys(collectors);
}
