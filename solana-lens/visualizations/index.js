/**
 * SolanaLens Visualizations
 * 
 * Main entry point for the visualization components of the SolanaLens project.
 * Provides an integration layer for visualizations across notebooks and D3.
 */

// Import core utilities
import { VisualizationLoader } from './utils/visualization-loader.js';
import { createVisualizationGallery } from './utils/dom-utils.js';
import { 
  allVisualizations, 
  notebooks, 
  d3Visualizations,
  findVisualization,
  getVisualizationsByTag,
  getVisualizationsByBounty
} from './utils/visualization-registry.js';

// Export for external use
export {
  VisualizationLoader,
  allVisualizations,
  notebooks,
  d3Visualizations,
  findVisualization,
  getVisualizationsByTag,
  getVisualizationsByBounty,
  createVisualizationGallery
};

// Initialize when loaded directly
if (typeof window !== 'undefined') {
  window.SolanaLens = window.SolanaLens || {};
  
  // Add visualization components to global namespace
  window.SolanaLens.Viz = {
    VisualizationLoader,
    visualizations: allVisualizations,
    findVisualization,
    getVisualizationsByTag,
    getVisualizationsByBounty,
    createGallery: createVisualizationGallery,
    
    // Initialize all visualizations on a page
    initAll(options = {}) {
      const vizElements = document.querySelectorAll('[data-viz-type]');
      
      vizElements.forEach(element => {
        const vizType = element.getAttribute('data-viz-type');
        const vizSubtype = element.getAttribute('data-viz-subtype');
        const dataSource = element.getAttribute('data-source');
        
        if (!vizType || !vizSubtype) {
          console.error('Missing data-viz-type or data-viz-subtype attribute', element);
          return;
        }
        
        const loader = new VisualizationLoader(element, options);
        loader.load(vizType, vizSubtype, dataSource)
          .catch(error => console.error(`Error initializing visualization: ${vizType}/${vizSubtype}`, error));
      });
      
      return vizElements.length;
    }
  };
  
  // Auto-initialize if requested
  document.addEventListener('DOMContentLoaded', () => {
    const script = document.currentScript || 
      document.querySelector('script[src*="index.js"][data-auto-init]');
      
    if (script && script.hasAttribute('data-auto-init')) {
      window.SolanaLens.Viz.initAll();
    }
  });
}
