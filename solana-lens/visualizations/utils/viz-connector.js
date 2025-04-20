/**
 * Simple connector for Solana Lens visualizations
 * Links notebooks, D3 visualizations, and data sources
 */

// Simple registry of available visualizations
const visualizations = {
  notebooks: {
    "sandwich_attacks": { path: "../notebooks/sandwich_attacks.js", name: "Sandwich Attack Analysis" },
    "dusting_analysis": { path: "../notebooks/dusting_analysis.js", name: "Dusting Analysis" },
    "token_network": { path: "../notebooks/token_network.js", name: "Token Creator Network" },
    "staking_dashboard": { path: "../notebooks/staking_dashboard.js", name: "Staking Dashboard" }
  },
  d3: {
    "token_network": { path: "../d3/token_network.js", name: "Token Network Graph", creator: "createTokenCreatorNetwork" },
    "ecosystem_map": { path: "../d3/ecosystem_map.js", name: "Ecosystem Map", creator: "createEcosystemMap" },
    "attack_timeline": { path: "../d3/attack_timeline.js", name: "Attack Timeline", creator: "createAttackTimeline" }
  }
};

// Load a visualization by type and name
function loadVisualization(container, type, name, data = null) {
  if (!container) throw new Error("Container element is required");
  
  const viz = type === "notebook" 
    ? visualizations.notebooks[name]
    : visualizations.d3[name];
    
  if (!viz) throw new Error(`Visualization "${name}" not found`);
  
  // Display loading indicator
  container.innerHTML = '<div class="loading">Loading visualization...</div>';
  
  // Load the script
  return import(viz.path)
    .then(module => {
      // Clear container
      container.innerHTML = '';
      
      if (type === "notebook") {
        // For notebooks
        const notebook = module.default || module.notebook || module.notebookData;
        renderNotebook(container, notebook, data);
        return notebook;
      } else {
        // For D3 visualizations
        const createFn = module[viz.creator] || module.default;
        if (typeof createFn !== "function") {
          throw new Error(`Creator function not found in ${viz.path}`);
        }
        return createFn(data || {}, container);
      }
    })
    .catch(error => {
      container.innerHTML = `<div class="error">Error loading visualization: ${error.message}</div>`;
      console.error(`Failed to load ${type}/${name}:`, error);
      throw error;
    });
}

// Simple notebook renderer (minimal version)
function renderNotebook(container, notebook, data = null) {
  if (!notebook || !notebook.cells) {
    throw new Error("Invalid notebook format");
  }
  
  const notebookContainer = document.createElement('div');
  notebookContainer.className = 'notebook-container';
  container.appendChild(notebookContainer);
  
  notebook.cells.forEach(cell => {
    const cellDiv = document.createElement('div');
    cellDiv.className = `notebook-cell ${cell.cell_type}-cell`;
    
    if (cell.cell_type === 'markdown') {
      // Very simple markdown rendering
      cellDiv.innerHTML = Array.isArray(cell.source) 
        ? cell.source.join('') 
        : cell.source;
    } else if (cell.cell_type === 'code') {
      // Show code source (real execution would require Observable Runtime)
      cellDiv.innerHTML = `<pre>${Array.isArray(cell.source) 
        ? cell.source.join('') 
        : cell.source}</pre>`;
    }
    
    notebookContainer.appendChild(cellDiv);
  });
  
  // Add a note that this is a simplified renderer
  const note = document.createElement('div');
  note.className = 'renderer-note';
  note.textContent = 'Note: This is a simplified rendering. For full interactivity, Observable Runtime is required.';
  notebookContainer.appendChild(note);
}

// Auto-initialize visualizations on page load
function initVisualizations() {
  document.querySelectorAll('[data-viz-type]').forEach(el => {
    const type = el.getAttribute('data-viz-type');
    const name = el.getAttribute('data-viz-name');
    const dataUrl = el.getAttribute('data-viz-data');
    
    if (type && name) {
      if (dataUrl) {
        fetch(dataUrl)
          .then(response => response.json())
          .then(data => loadVisualization(el, type, name, data))
          .catch(error => console.error(`Failed to load data from ${dataUrl}:`, error));
      } else {
        loadVisualization(el, type, name);
      }
    }
  });
}

// Export functions for external use
export { 
  loadVisualization, 
  initVisualizations, 
  visualizations 
};
