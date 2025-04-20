/**
 * Visualization Loader
 * 
 * Handles loading and rendering of different visualization types:
 * - Observable notebooks
 * - D3 visualizations
 */

import { findVisualization, notebooks, d3Visualizations } from './visualization-registry.js';
import { loadStyleSheet } from './dom-utils.js';

export class VisualizationLoader {
  /**
   * Create a new visualization loader
   * @param {HTMLElement|string} container - DOM element or selector for the container
   * @param {Object} options - Configuration options
   */
  constructor(container, options = {}) {
    // Handle string selectors or direct DOM elements
    this.container = typeof container === 'string' 
      ? document.querySelector(container) 
      : container;
      
    if (!this.container) {
      throw new Error('Invalid container specified for visualization');
    }
    
    this.options = {
      loadCSS: true,
      width: '100%',
      height: '600px',
      ...options
    };
    
    this.visualization = null;
    this.currentVizId = null;
    
    // Apply container styling
    Object.assign(this.container.style, {
      width: this.options.width,
      height: this.options.height,
      position: 'relative'
    });
    
    // Load CSS if requested
    if (this.options.loadCSS) {
      loadStyleSheet('../assets/css/styles.css');
    }
  }
  
  /**
   * Load a visualization by ID
   * @param {string} vizId - ID of the visualization from the registry
   * @param {Object|string} data - Optional data or URL to load data from
   * @returns {Promise} - Promise resolving to the loaded visualization
   */
  async loadById(vizId, data = null) {
    const vizInfo = findVisualization(vizId);
    
    if (!vizInfo) {
      throw new Error(`Visualization with ID "${vizId}" not found in registry`);
    }
    
    if (vizInfo.type === 'notebook') {
      return this.loadNotebook(vizInfo, data);
    } else if (vizInfo.type === 'd3') {
      return this.loadD3Visualization(vizInfo, data);
    } else {
      throw new Error(`Unknown visualization type: ${vizInfo.type}`);
    }
  }
  
  /**
   * Load a visualization by type and subtype
   * @param {string} type - Type of visualization ('notebook' or 'd3')
   * @param {string} subtype - Specific visualization name
   * @param {Object|string} data - Optional data or URL to load data from
   * @returns {Promise} - Promise resolving to the loaded visualization
   */
  async load(type, subtype, data = null) {
    // Clear existing visualization
    this.clear();
    this.showLoading();
    
    try {
      if (type === 'notebook') {
        const vizInfo = notebooks.find(viz => viz.id === subtype);
        if (!vizInfo) {
          throw new Error(`Notebook "${subtype}" not found`);
        }
        return await this.loadNotebook(vizInfo, data);
      } else if (type === 'd3') {
        const vizInfo = d3Visualizations.find(viz => viz.id === subtype);
        if (!vizInfo) {
          throw new Error(`D3 visualization "${subtype}" not found`);
        }
        return await this.loadD3Visualization(vizInfo, data);
      } else {
        throw new Error(`Unsupported visualization type: ${type}`);
      }
    } catch (error) {
      this.showError(error);
      throw error;
    } finally {
      this.hideLoading();
    }
  }
  
  /**
   * Load a notebook visualization
   * @param {Object} vizInfo - Visualization info from registry
   * @param {Object|string} data - Optional data or URL
   * @returns {Promise} - Promise resolving to the notebook instance
   */
  async loadNotebook(vizInfo, data = null) {
    try {
      // Dynamic import of Observable Runtime
      const { Runtime, Inspector } = await import('@observablehq/runtime');
      
      // Dynamic import of the notebook module
      const notebookModule = await import(`../notebooks/${vizInfo.data}`);
      
      // Get notebook data from the module
      const notebookData = notebookModule.default || notebookModule.notebookData || notebookModule.notebook;
      
      if (!notebookData || !notebookData.cells) {
        throw new Error(`Invalid notebook data for ${vizInfo.name}`);
      }
      
      // Create a new runtime
      const runtime = new Runtime();
      
      // Create container for notebook
      const notebookContainer = document.createElement('div');
      notebookContainer.className = 'solana-lens-notebook';
      this.container.appendChild(notebookContainer);
      
      // Create the notebook module
      const notebook = runtime.module(define, Inspector.into(notebookContainer));
      
      // Function to define the notebook module
      function define(runtime, observer) {
        const cellOutputs = {};
        
        notebookData.cells.forEach((cell, i) => {
          if (cell.cell_type === 'code' && cell.source) {
            const cellDiv = document.createElement('div');
            cellDiv.className = 'notebook-cell';
            
            // Convert source to string if it's an array
            const source = Array.isArray(cell.source) ? cell.source.join('') : cell.source;
            
            try {
              // Handle special variables for data injection
              let processedSource = source;
              if (data && source.includes('sampleData')) {
                // Replace sample data references with the provided data
                processedSource = source.replace(/sampleData/g, 'injectedData');
              }
              
              // Evaluate the cell code
              const output = runtime.module().variable(observer(cellDiv)).define(
                cell.metadata?.id || `cell${i}`,
                ['injectedData'].concat(Object.keys(cellOutputs).map(key => key)),
                Function('injectedData', ...Object.keys(cellOutputs), `return ${processedSource}`)(
                  data, ...Object.keys(cellOutputs).map(key => cellOutputs[key])
                )
              );
              
              // Store named outputs for reactive variables
              const viewofMatch = source.match(/^viewof\s+(\w+)\s*=/);
              if (viewofMatch) {
                cellOutputs[`viewof ${viewofMatch[1]}`] = output;
                runtime.module().variable().define(viewofMatch[1], ["Generators", `viewof ${viewofMatch[1]}`], (G, _) => G.input(_));
              } else {
                const nameMatch = source.match(/^(\w+)\s*=/);
                if (nameMatch) {
                  cellOutputs[nameMatch[1]] = output;
                }
              }
              
              notebookContainer.appendChild(cellDiv);
            } catch (error) {
              console.error(`Error evaluating cell ${i}:`, error);
              cellDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
              notebookContainer.appendChild(cellDiv);
            }
          } else if (cell.cell_type === 'markdown' && cell.source) {
            const cellDiv = document.createElement('div');
            cellDiv.className = 'notebook-markdown-cell';
            
            // Convert source to string if it's an array
            const markdownText = Array.isArray(cell.source) ? cell.source.join('') : cell.source;
            
            // Simple markdown rendering (could be enhanced with a proper markdown library)
            cellDiv.innerHTML = this.renderMarkdown(markdownText);
            notebookContainer.appendChild(cellDiv);
          }
        });
        
        return Object.keys(cellOutputs);
      }
      
      this.visualization = notebook;
      this.currentVizId = vizInfo.id;
      
      return notebook;
    } catch (error) {
      console.error(`Failed to load notebook ${vizInfo.name}:`, error);
      throw error;
    }
  }
  
  /**
   * Load a D3 visualization
   * @param {Object} vizInfo - Visualization info from registry
   * @param {Object|string} data - Optional data or URL
   * @returns {Promise} - Promise resolving to the D3 visualization instance
   */
  async loadD3Visualization(vizInfo, data = null) {
    try {
      // Dynamic import of the D3 module
      const module = await import(`../d3/${vizInfo.data}`);
      
      // Determine the main function
      const createFunction = vizInfo.createFunction || 
        `create${vizInfo.id.charAt(0).toUpperCase() + vizInfo.id.slice(1)}`;
      
      let mainFunction;
      if (typeof module[createFunction] === 'function') {
        mainFunction = module[createFunction];
      } else if (typeof module.default === 'function') {
        mainFunction = module.default;
      } else {
        throw new Error(`Unable to find initialization function for ${vizInfo.name}`);
      }
      
      // Prepare data
      let vizData = data;
      
      // If data is a string URL, fetch it
      if (typeof data === 'string' && data.startsWith('http')) {
        const response = await fetch(data);
        if (!response.ok) {
          throw new Error(`Failed to fetch data from ${data}: ${response.statusText}`);
        }
        vizData = await response.json();
      }
      
      // If no data provided, use sample data if available
      if (!vizData) {
        vizData = module.sampleData;
      }
      
      // Create visualization container
      const vizContainer = document.createElement('div');
      vizContainer.className = 'solana-lens-d3-container';
      this.container.appendChild(vizContainer);
      
      // Initialize visualization
      this.visualization = mainFunction(vizData, vizContainer);
      this.currentVizId = vizInfo.id;
      
      return this.visualization;
    } catch (error) {
      console.error(`Failed to load D3 visualization ${vizInfo.name}:`, error);
      throw error;
    }
  }
  
  /**
   * Very simple markdown renderer (could be replaced with a proper library)
   * @param {string} markdown - Markdown text to render
   * @returns {string} - HTML representation of the markdown
   */
  renderMarkdown(markdown) {
    // This is a very basic implementation
    return markdown
      // Headers
      .replace(/^# (.*$)/gm, '<h1>$1</h1>')
      .replace(/^## (.*$)/gm, '<h2>$1</h2>')
      .replace(/^### (.*$)/gm, '<h3>$1</h3>')
      // Bold
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Emphasis
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      // Lists
      .replace(/^\- (.*$)/gm, '<li>$1</li>')
      // Paragraphs
      .replace(/^\s*$/gm, '</p><p>')
      // Wrap in paragraph to finish
      .replace(/^(.+)$/gm, '<p>$1</p>');
  }
  
  /**
   * Clear the container and cleanup resources
   */
  clear() {
    // Cleanup any existing content
    while (this.container.firstChild) {
      this.container.removeChild(this.container.firstChild);
    }
    
    this.visualization = null;
    this.currentVizId = null;
  }
  
  /**
   * Show loading indicator
   */
  showLoading() {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading-indicator';
    loadingDiv.innerHTML = `
      <div class="spinner"></div>
      <p>Loading visualization...</p>
    `;
    this.container.appendChild(loadingDiv);
  }
  
  /**
   * Hide the loading indicator
   */
  hideLoading() {
    const loadingDiv = this.container.querySelector('.loading-indicator');
    if (loadingDiv) {
      loadingDiv.remove();
    }
  }
  
  /**
   * Show an error message
   * @param {Error} error - Error object
   */
  showError(error) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `
      <h3>Error Loading Visualization</h3>
      <p>${error.message}</p>
      <button class="retry-button">Retry</button>
    `;
    
    const retryButton = errorDiv.querySelector('.retry-button');
    if (retryButton && this.currentVizId) {
      const vizId = this.currentVizId;
      retryButton.addEventListener('click', () => {
        errorDiv.remove();
        this.loadById(vizId);
      });
    }
    
    this.container.appendChild(errorDiv);
  }
}
