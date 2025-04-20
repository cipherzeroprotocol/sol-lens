/**
 * SolanaLens Data Loader
 * 
 * Utility for loading data from the scripts output directory into visualizations.
 * Provides a bridge between Python data collection scripts and JavaScript visualizations.
 */

/**
 * Base path to the data directory - adjust according to project structure
 * When deployed, this might be served from a CDN or API endpoint
 */
const DATA_BASE_PATH = '../data';
const VIZ_DATA_PATH = `${DATA_BASE_PATH}/viz`;

/**
 * Load visualization data from the data directory
 * 
 * @param {string} datasetName - Name of the dataset to load
 * @param {string} datasetType - Type of the dataset (e.g., 'network', 'mixer', 'security')
 * @param {boolean} latest - Whether to load the latest version (default: true)
 * @returns {Promise<Object>} - The loaded data
 */
async function loadVisualizationData(datasetName, datasetType = null, latest = true) {
  try {
    // Build the path to the data file
    let path;
    if (datasetType) {
      path = `${VIZ_DATA_PATH}/${datasetType}`;
    } else {
      path = VIZ_DATA_PATH;
    }
    
    const filename = latest 
      ? `${datasetName}_latest.json`
      : `${datasetName}_*.json`; // This would need server-side listing
    
    // Fetch the data
    const response = await fetch(`${path}/${filename}`);
    if (!response.ok) {
      throw new Error(`Failed to load ${datasetName} data: ${response.statusText}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`Error loading visualization data: ${error.message}`);
    throw error;
  }
}

/**
 * Load network graph data for D3 visualizations
 * 
 * @param {string} graphName - Name of the graph to load
 * @param {boolean} latest - Whether to load the latest version (default: true)
 * @returns {Promise<Object>} - The loaded graph data
 */
async function loadNetworkGraph(graphName, latest = true) {
  try {
    const path = `${VIZ_DATA_PATH}/network`;
    
    const filename = latest 
      ? `${graphName}_network_latest.json` 
      : `${graphName}_network_*.json`; // This would need server-side listing
    
    // Fetch the graph data
    const response = await fetch(`${path}/${filename}`);
    if (!response.ok) {
      throw new Error(`Failed to load ${graphName} network graph: ${response.statusText}`);
    }
    
    const graphData = await response.json();
    return graphData;
  } catch (error) {
    console.error(`Error loading network graph: ${error.message}`);
    throw error;
  }
}

/**
 * Get all available datasets
 * This would typically require a server or API endpoint that lists files
 * For now, we'll mock this functionality
 * 
 * @returns {Promise<Object>} - List of available datasets
 */
async function getAvailableDatasets() {
  try {
    // In a real implementation, this might call an API endpoint that scans the directory
    // For now, let's return a sample list
    return {
      networks: [
        { name: 'money_laundering', displayName: 'Money Laundering Network', path: 'network/money_laundering_network_latest.json' },
        { name: 'token_creators', displayName: 'Token Creator Network', path: 'network/token_creators_network_latest.json' }
      ],
      security: [
        { name: 'address_poisoning', displayName: 'Address Poisoning Analysis', path: 'security/address_poisoning_latest.json' },
        { name: 'sandwich_attacks', displayName: 'Sandwich Attack Analysis', path: 'security/sandwich_attacks_latest.json' }
      ],
      defi: [
        { name: 'staking_data', displayName: 'Staking Performance', path: 'defi/staking_data_latest.json' },
        { name: 'mixer_analysis', displayName: 'Mixer Analysis', path: 'mixer/mixer_analysis_latest.json' }
      ]
    };
  } catch (error) {
    console.error(`Error fetching available datasets: ${error.message}`);
    return {};
  }
}

/**
 * Convert Python timestamp format to JavaScript Date object
 * 
 * @param {string} pythonTimestamp - Timestamp string from Python (ISO format)
 * @returns {Date} - JavaScript Date object
 */
function convertPythonTimestamp(pythonTimestamp) {
  if (!pythonTimestamp) return null;
  return new Date(pythonTimestamp);
}

// Export functions for use in visualizations
export {
  loadVisualizationData,
  loadNetworkGraph,
  getAvailableDatasets,
  convertPythonTimestamp
};
