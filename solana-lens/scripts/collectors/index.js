/**
 * Collectors Registry
 * 
 * This module initializes and exports all data collectors, making them
 * available to the visualization components.
 */

import { clientProvider } from '../api/client-provider.js';
import { BridgeCollector } from './bridge-collector.js';
import { DustingCollector } from './dusting-collector.js';
import { SandwichCollector } from './sandwich-collector.js';
import { TokenNetworkCollector } from './token-network-collector.js';
import { StakingCollector } from './staking-collector.js';

// Initialize API clients (will use demo mode if no API keys provided)
clientProvider.init();

// Initialize all collectors with API clients
export const bridgeCollector = new BridgeCollector(clientProvider.helius, clientProvider.range);
export const dustingCollector = new DustingCollector(clientProvider.helius);
export const sandwichCollector = new SandwichCollector(clientProvider.helius);
export const tokenNetworkCollector = new TokenNetworkCollector(clientProvider.helius);
export const stakingCollector = new StakingCollector(clientProvider.helius);

// Export named collectors as an object for easier access
export const collectors = {
  bridge: bridgeCollector,
  dusting: dustingCollector,
  sandwich: sandwichCollector,
  tokenNetwork: tokenNetworkCollector,
  staking: stakingCollector
};

// Export utility to check if we have real API access
export const hasRealApiAccess = () => clientProvider.hasRealApiAccess();

/**
 * Get a collector by name
 * @param {string} name - Name of the collector
 * @returns {Object|null} - Collector instance or null if not found
 */
export function getCollector(name) {
  return collectors[name] || null;
}

// Default export for convenience
export default collectors;
