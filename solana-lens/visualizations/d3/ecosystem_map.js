// Solana Ecosystem Map Visualization using D3.js

function createEcosystemMap(data, container) {
    const width = 960;
    const height = 700;
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };

    const svg = d3.select(container)
        .append('svg')
        .attr('width', '100%')
        .attr('height', '100%')
        .attr('viewBox', [0, 0, width, height])
        .style('display', 'block');

    const g = svg.append('g');

    // Color scale for categories (e.g., DeFi, NFT, Infrastructure)
    const colorScale = d3.scaleOrdinal(d3.schemeCategory10)
        .domain(Array.from(new Set(data.nodes.map(d => d.category))));

    // Size scale (e.g., based on TVL, users, or market cap)
    const sizeScale = d3.scaleSqrt()
        .domain([0, d3.max(data.nodes, d => d.value || 1)])
        .range([5, 35]);

    // Tooltip div
    const tooltip = d3.select(container)
        .append("div")
        .attr("class", "tooltip")
        .style("opacity", 0)
        .style("position", "absolute")
        .style("background-color", "white")
        .style("border", "solid")
        .style("border-width", "1px")
        .style("border-radius", "5px")
        .style("padding", "10px")
        .style("pointer-events", "none"); // Important

    // Simulation for layout (could use force, pack, treemap, etc.)
    // Using force simulation for network-like structure
    const simulation = d3.forceSimulation(data.nodes)
        .force("link", d3.forceLink(data.links).id(d => d.id).strength(0.05)) // Weak links for loose clustering
        .force("charge", d3.forceManyBody().strength(-50))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collision", d3.forceCollide().radius(d => sizeScale(d.value || 1) + 5))
        .force("x", d3.forceX(width / 2).strength(0.02)) // Pull towards center X
        .force("y", d3.forceY(height / 2).strength(0.02)); // Pull towards center Y

    // Create links (optional, if showing connections)
    const link = g.append("g")
        .attr("stroke", "#ccc")
        .attr("stroke-opacity", 0.5)
        .selectAll("line")
        .data(data.links)
        .join("line")
        .attr("stroke-width", 1);

    // Create nodes
    const node = g.append("g")
        .selectAll(".node")
        .data(data.nodes)
        .join("g")
        .attr("class", "node")
        .call(drag(simulation))
        .on("mouseover", (event, d) => {
            tooltip.transition().duration(200).style("opacity", .9);
            tooltip.html(`<strong>${d.name}</strong><br/>Category: ${d.category}<br/>Value: ${d.value || 'N/A'}`)
                .style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 28) + "px");
            // Highlight node and neighbors (optional)
            node.style('opacity', n => (n === d || data.links.some(l => (l.source === d && l.target === n) || (l.target === d && l.source === n))) ? 1 : 0.3);
            link.style('stroke-opacity', l => (l.source === d || l.target === d) ? 1 : 0.1);
        })
        .on("mouseout", () => {
            tooltip.transition().duration(500).style("opacity", 0);
            // Reset highlight
            node.style('opacity', 1);
            link.style('stroke-opacity', 0.5);
        });

    // Add circles or images for nodes
    node.append("circle")
        .attr("r", d => sizeScale(d.value || 1))
        .attr("fill", d => colorScale(d.category))
        .attr("stroke", "#fff")
        .attr("stroke-width", 1.5);

    // Add labels (optional, maybe only for larger nodes)
    node.append("text")
        .attr("dy", ".35em")
        .attr("text-anchor", "middle")
        .text(d => (sizeScale(d.value || 1) > 15) ? d.name : "") // Label larger nodes
        .attr("font-size", 9)
        .attr("fill", "#333")
        .style("pointer-events", "none");

    // Legend
    createEcosystemLegend(svg, colorScale, width);

    // Simulation ticks
    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        node.attr("transform", d => `translate(${d.x}, ${d.y})`);
    });

    // Drag function
    function drag(simulation) {
        // ... (standard d3 drag functions - start, dragged, end) ...
        function dragstarted(event) { if (!event.active) simulation.alphaTarget(0.3).restart(); event.subject.fx = event.subject.x; event.subject.fy = event.subject.y; }
        function dragged(event) { event.subject.fx = event.x; event.subject.fy = event.y; }
        function dragended(event) { if (!event.active) simulation.alphaTarget(0); event.subject.fx = null; event.subject.fy = null; }
        return d3.drag().on("start", dragstarted).on("drag", dragged).on("end", dragended);
    }

    return svg.node();
}

function createEcosystemLegend(svg, colorScale, width) {
    const legend = svg.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${width - 150}, 20)`);

    const legendData = colorScale.domain().sort(); // Sort categories alphabetically

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
          .attr('x', 18)
          .attr('y', 9)
          .attr('font-size', 10)
          .attr('alignment-baseline', 'middle')
          .text(d);
      });
}

// Example Usage:
// const ecosystemData = {
//     nodes: [
//         { id: "jupiter", name: "Jupiter", category: "DeFi", value: 100 },
//         { id: "raydium", name: "Raydium", category: "DeFi", value: 80 },
//         { id: "tensor", name: "Tensor", category: "NFT", value: 60 },
//         { id: "helius", name: "Helius", category: "Infrastructure", value: 50 },
//         // ... more nodes
//     ],
//     links: [
//         { source: "jupiter", target: "raydium" }, // Example link
//         // ... more links representing interactions or dependencies
//     ]
// };
// createEcosystemMap(ecosystemData, document.getElementById('ecosystem-container'));
