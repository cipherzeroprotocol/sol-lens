/**
 * Visualization Registry
 * 
 * A central registry of all visualizations available in the SolanaLens project.
 * This allows for easy discovery and integration of visualizations across the application.
 */

// Catalog of notebook visualizations
export const notebooks = [
  {
    id: 'sandwich_attacks',
    name: 'Sandwich Attack Analysis',
    description: 'Visualizes MEV sandwich attacks on Solana DEXs, showing patterns and profits.',
    type: 'notebook',
    tags: ['security', 'mev', 'defi'],
    bounty: 'Helius Malicious MEV',
    thumbnail: 'assets/images/thumbnails/sandwich.png',
    data: 'sandwich_attacks.js'
  },
  {
    id: 'dusting_analysis',
    name: 'Dusting Attack Analysis',
    description: 'Analyzes dusting attacks used for tracking and deanonymizing Solana addresses.',
    type: 'notebook',
    tags: ['security', 'privacy', 'tracking'],
    bounty: 'Helius Account Dusting',
    thumbnail: 'assets/images/thumbnails/dusting.png',
    data: 'dusting_analysis.js'
  },
  {
    id: 'token_network',
    name: 'Token Creator Network',
    description: 'Network visualization showing relationships between token creators and tokens.',
    type: 'notebook',
    tags: ['tokens', 'network', 'scam-detection'],
    bounty: 'RugCheck Onchain Analysis',
    thumbnail: 'assets/images/thumbnails/token_network.png',
    data: 'token_network.js'
  },
  {
    id: 'staking_dashboard',
    name: 'Staking Dashboard',
    description: 'Interactive dashboard showing Solana validator staking metrics and rewards.',
    type: 'notebook',
    tags: ['staking', 'validators', 'rewards'],
    bounty: 'Nebula Node Staking',
    thumbnail: 'assets/images/thumbnails/staking.png',
    data: 'staking_dashboard.js'
  }
];

// Catalog of D3 visualizations
export const d3Visualizations = [
  {
    id: 'ecosystem_map',
    name: 'Solana Ecosystem Map',
    description: 'Interactive map of the Solana ecosystem and project relationships.',
    type: 'd3',
    tags: ['ecosystem', 'projects', 'categories'],
    bounty: 'Ded Monkes Visualization',
    thumbnail: 'assets/images/thumbnails/ecosystem.png',
    data: 'ecosystem_map.js',
    createFunction: 'createEcosystemMap'
  },
  {
    id: 'attack_timeline',
    name: 'Security Incident Timeline',
    description: 'Timeline visualization of major security incidents affecting Solana.',
    type: 'd3',
    tags: ['security', 'timeline', 'incidents'],
    bounty: 'Helius History of Security Incidents',
    thumbnail: 'assets/images/thumbnails/timeline.png',
    data: 'attack_timeline.js',
    createFunction: 'createAttackTimeline'
  },
  {
    id: 'token_network_d3',
    name: 'Token Network (D3 Version)',
    description: 'D3-based token network visualization with enhanced interactivity.',
    type: 'd3',
    tags: ['tokens', 'network', 'interactive'],
    bounty: 'RugCheck Onchain Analysis',
    thumbnail: 'assets/images/thumbnails/token_network_d3.png',
    data: 'token_network.js',
    createFunction: 'createTokenCreatorNetwork'
  }
];

// Combined list of all visualizations
export const allVisualizations = [...notebooks, ...d3Visualizations];

/**
 * Find a visualization by ID
 * @param {string} id - The visualization ID to look for
 * @returns {Object|null} - The visualization object or null if not found
 */
export function findVisualization(id) {
  return allVisualizations.find(viz => viz.id === id) || null;
}

/**
 * Get visualizations by tag
 * @param {string} tag - Tag to filter by
 * @returns {Array} - Array of visualizations with the specified tag
 */
export function getVisualizationsByTag(tag) {
  return allVisualizations.filter(viz => viz.tags.includes(tag));
}

/**
 * Get visualizations by bounty
 * @param {string} bountyName - Name of the bounty
 * @returns {Array} - Array of visualizations for the specified bounty
 */
export function getVisualizationsByBounty(bountyName) {
  return allVisualizations.filter(viz => viz.bounty === bountyName);
}
