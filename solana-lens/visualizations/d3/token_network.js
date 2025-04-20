// Token Creator Network Visualization using D3.js
// This visualization shows the relationships between token creators and their tokens

// Main visualization function
function createTokenCreatorNetwork(data, container) {
    // Set up dimensions and colors
    const width = 960;
    const height = 600;
    const nodeBaseRadius = 5;
    const nodeMaxRadius = 25;

    // Color scheme for different node types
    const colorScale = d3.scaleOrdinal()
      .domain(['creator', 'token', 'suspicious', 'verified', 'default']) // Added default
      .range(['#4e79a7', '#f28e2c', '#e15759', '#59a14f', '#bab0ab']); // Added grey for default

    // Node size scale based on token values or transaction counts (log scale for better distribution)
    const sizeScale = d3.scaleLog()
      .domain([1, d3.max(data.nodes, d => d.value || 1) || 1]) // Ensure domain starts at 1 for log scale
      .range([nodeBaseRadius, nodeMaxRadius])
      .clamp(true); // Prevent extreme sizes

    // Create SVG container
    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%') // Make responsive
      .attr('height', '100%') // Make responsive
      .attr('viewBox', [0, 0, width, height])
      .style('display', 'block'); // Ensure SVG takes block space

    // Add zoom functionality
    const g = svg.append('g');

    const zoom = d3.zoom()
      .extent([[0, 0], [width, height]])
      .scaleExtent([0.1, 8])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Create force simulation
    const simulation = d3.forceSimulation(data.nodes)
      .force('link', d3.forceLink(data.links).id(d => d.id).distance(d => (sizeScale(d.source.value || 1) + sizeScale(d.target.value || 1)) + 30)) // Dynamic distance
      .force('charge', d3.forceManyBody().strength(-150)) // Adjusted strength
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => sizeScale(d.value || 1) + 2)); // Add collision force

    // Create links
    const link = g.append('g')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .selectAll('line')
      .data(data.links)
      .join('line')
      .attr('stroke-width', d => Math.max(1, Math.sqrt(d.value || 1) / 2)); // Adjusted stroke width

    // Create nodes group
    const node = g.append('g')
      .selectAll('.node')
      .data(data.nodes)
      .join('g')
      .attr('class', 'node')
      .call(drag(simulation));

    // Add circles for each node
    node.append('circle')
      .attr('r', d => sizeScale(d.value || 1))
      .attr('fill', d => colorScale(d.type || 'default')) // Use default color if type is missing
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5);

    // Add labels for significant nodes (e.g., high value or creators)
    node.append('text')
      .attr('dx', d => sizeScale(d.value || 1) + 3) // Position label outside the circle
      .attr('dy', '.35em')
      .text(d => (d.type === 'creator' || (d.value || 0) > 10) ? getNodeLabel(d) : '') // Conditional labeling
      .attr('font-size', 9) // Smaller font size
      .attr('fill', '#333')
      .style('pointer-events', 'none')
      .style('text-shadow', '0 1px 0 #fff, 1px 0 0 #fff, 0 -1px 0 #fff, -1px 0 0 #fff'); // Basic text outline

    // Add titles for hovering (improved content)
    node.append('title')
      .text(d => getNodeTooltip(d));

    // Add legend
    createLegend(svg, colorScale, width); // Pass width for positioning

    // Update positions on each tick of the simulation
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node.attr('transform', d => `translate(${d.x}, ${d.y})`);
    });

    // Add search functionality (assuming container is the direct parent)
    addSearchBar(container.parentNode, data, node, simulation, svg, zoom, width, height); // Pass more args

    return {
      svg,
      simulation,
      update: updateVisualization
    };
  }

  // Helper function to get appropriate node label
  function getNodeLabel(d) {
    if (d.type === 'token' && d.symbol) {
      return d.symbol.length > 10 ? shortenAddress(d.symbol) : d.symbol; // Shorten long symbols
    } else if (d.type === 'creator') {
      return shortenAddress(d.id);
    }
    return shortenAddress(d.id);
  }

  // Helper function to get node tooltip content
  function getNodeTooltip(d) {
    let tooltip = `Type: ${d.type || 'Unknown'}\nAddress: ${d.id}`;
    if (d.symbol) tooltip += `\nSymbol: ${d.symbol}`;
    if (d.value) tooltip += `\nValue/Connections: ${d.value}`;
    if (d.created_at) tooltip += `\nCreated: ${new Date(d.created_at).toLocaleDateString()}`;
    if (d.risk_score !== undefined) tooltip += `\nRisk Score: ${d.risk_score}`;
    if (d.token_count !== undefined) tooltip += `\nTokens Created: ${d.token_count}`;
    return tooltip;
  }

  // Helper function to shorten blockchain addresses
  function shortenAddress(address) {
    if (!address || address.length < 10) return address;
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
  }

  // Function to create a legend
  function createLegend(svg, colorScale, width) { // Added width parameter
    const legend = svg.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${width - 150}, 20)`); // Position top-right

    const legendData = Array.from(colorScale.domain());

    legend.selectAll('.legend-item')
      .data(legendData)
      .join('g')
      .attr('class', 'legend-item')
      .attr('transform', (d, i) => `translate(0, ${i * 20})`)
      .call(g => {
        g.append('rect')
          .attr('width', 12)
          .attr('height', 12)
          .attr('fill', d => colorScale(d));

        g.append('text')
          .attr('x', 18) // Adjusted spacing
          .attr('y', 9)
          .attr('font-size', 10) // Smaller legend text
          .attr('alignment-baseline', 'middle')
          .text(d => d.charAt(0).toUpperCase() + d.slice(1));
      });
  }

  // Function to add search functionality
  function addSearchBar(container, data, nodeSelection, simulation, svg, zoom, width, height) { // Added more parameters
    let searchContainer = d3.select(container).select('.search-container');
    if (searchContainer.empty()) { // Create only if it doesn't exist
        searchContainer = d3.select(container)
          .append('div')
          .attr('class', 'search-container')
          .style('position', 'absolute')
          .style('top', '10px')
          .style('left', '10px') // Position top-left
          .style('background', 'rgba(255, 255, 255, 0.8)') // Semi-transparent background
          .style('padding', '5px')
          .style('border', '1px solid #ccc')
          .style('border-radius', '4px')
          .style('z-index', 10); // Ensure it's above the SVG
    }

    let searchInput = searchContainer.select('input');
    if (searchInput.empty()) {
        searchInput = searchContainer.append('input')
          .attr('type', 'text')
          .attr('placeholder', 'Search address or symbol...')
          .style('width', '200px')
          .style('padding', '5px');
    }

    searchInput.on('input', function() {
        const searchTerm = this.value.toLowerCase().trim();
        highlightNodes(searchTerm, nodeSelection, simulation, svg, zoom, width, height); // Call helper
      });
  }

  // Helper function to highlight nodes based on search
  function highlightNodes(searchTerm, nodeSelection, simulation, svg, zoom, width, height) {
      let foundNode = null;

      if (searchTerm === '') {
        // Reset all nodes and links
        nodeSelection.style('opacity', 1);
        nodeSelection.selectAll('circle')
          .attr('stroke', '#fff')
          .attr('stroke-width', 1.5);
        // Reset links (assuming link variable is accessible or passed)
        // link.style('opacity', 0.6); // Need link selection here

        // Reset zoom
        svg.transition().duration(750).call(
          zoom.transform,
          d3.zoomIdentity, // Reset to identity transform
        );

      } else {
        const isAddress = searchTerm.length > 10; // Simple check if it looks like an address

        nodeSelection.style('opacity', 0.1); // Dim all nodes initially

        nodeSelection.filter(d => {
            const idMatch = d.id.toLowerCase().includes(searchTerm);
            const symbolMatch = d.symbol && d.symbol.toLowerCase().includes(searchTerm);
            const matches = idMatch || symbolMatch;
            if (matches && !foundNode) { // Find the first primary match
                foundNode = d;
            }
            return matches;
          })
          .style('opacity', 1) // Highlight matching nodes
          .selectAll('circle')
          .attr('stroke', '#f00') // Highlight stroke
          .attr('stroke-width', 3);

        // Optional: Highlight neighbors (1-hop)
        // ... (requires access to links data)

        // Zoom to the first found node
        if (foundNode) {
            const scale = 2; // Zoom scale factor
            const x = width / 2 - foundNode.x * scale;
            const y = height / 2 - foundNode.y * scale;

            svg.transition().duration(750).call(
              zoom.transform,
              d3.zoomIdentity.translate(x, y).scale(scale)
            );
        }
      }
  }

  // Function to update the visualization with new data
  function updateVisualization(newData) {
    // This function would update the visualization with new data
    // Implementation would depend on specific update requirements
  }

  // Drag functionality for nodes
  function drag(simulation) {
    function dragstarted(event) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    return d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended);
  }

  // Function to load data and create visualization
  function loadTokenNetworkData(dataUrl, containerId) {
    d3.json(dataUrl).then(data => {
      const container = document.getElementById(containerId);
      createTokenCreatorNetwork(data, container);
    }).catch(error => {
      console.error('Error loading token network data:', error);
    });
  }

  // Example usage:
  // loadTokenNetworkData('data/token_creator_network.json', 'visualization-container');