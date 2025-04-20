# Solana Lens Visualizations

This directory contains visualization components for the Solana Lens project, providing interactive data visualization tools for Solana blockchain analysis.

## Directory Structure

```
visualizations/
├── assets/           # Static assets (CSS, images, etc.)
├── d3/               # D3.js-based visualizations
├── notebooks/        # Observable-style notebook visualizations
├── utils/            # Utility scripts for visualization handling
├── index.js          # Main entry point for the visualization library
├── index.html        # Demo page showcasing available visualizations
└── package.json      # Project dependencies
```

## Visualization Types

### Observable Notebooks

Interactive notebook-style visualizations with reactive displays:
- `sandwich_attacks.js` - Visualizes sandwich attacks on Solana DEXs
- `dusting_analysis.js` - Analyzes dusting attack patterns
- `staking_dashboard.js` - Dashboards for Solana staking metrics
- `token_network.js` - Interactive token relationship explorer

### D3 Visualizations

Standalone D3-based visualizations:
- `token_network.js` - Network graph of token creators and token relationships
- `ecosystem_map.js` - Map of projects in the Solana ecosystem
- `attack_timeline.js` - Timeline of security incidents affecting Solana protocols

## Usage

### Basic Integration

Add the visualization library to your HTML page:

```html
<script type="module" src="path/to/visualizations/index.js" data-auto-init></script>

<!-- Create a container with data attributes -->
<div data-viz-type="notebook" data-viz-subtype="sandwich_attacks" style="height: 600px;"></div>
```

The `data-auto-init` attribute will automatically initialize all visualizations with the appropriate data attributes on the page.

### Manual Initialization

```html
<div id="visualization-container"></div>

<script type="module">
  import { VisualizationLoader } from './path/to/visualizations/index.js';
  
  const container = document.getElementById('visualization-container');
  const loader = new VisualizationLoader(container);
  
  // Load a notebook visualization
  loader.load('notebook', 'sandwich_attacks');
  
  // Or load a D3 visualization with custom data
  fetch('/api/token-network-data')
    .then(response => response.json())
    .then(data => {
      loader.load('d3', 'token_network', data);
    });
</script>
```

## Development

### Setup

```bash
cd visualizations
npm install
```

### Running the Demo

```bash
npm start
```

This will start a local development server at http://localhost:8080 where you can view the visualization gallery.

### Adding New Visualizations

1. **For notebooks**: Add your notebook file to the `notebooks/` directory following the structure in the existing examples.
2. **For D3 visualizations**: Add your D3 visualization to the `d3/` directory with a main creation function.
3. Update the demo page (`index.html`) to include your new visualization.

## Dependencies

- D3.js (v7.x)
- Chart.js (v4.x)
- Observable Runtime
