// Attack Timeline Visualization using D3.js

function createAttackTimeline(data, container) {
    const width = 960;
    const height = 500;
    const margin = { top: 40, right: 40, bottom: 60, left: 60 }; // Increased bottom margin for axis labels

    // Parse dates
    const parseDate = d3.isoParse; // Assuming ISO 8601 format
    data.forEach(d => {
        d.date = parseDate(d.timestamp || d.date); // Allow 'date' or 'timestamp'
        d.value = +d.value || +d.loss_usd || 1; // Use value or loss_usd, default to 1
    });

    // Filter out entries without valid dates
    data = data.filter(d => d.date instanceof Date && !isNaN(d.date));

    // Sort data by date
    data.sort((a, b) => a.date - b.date);

    const svg = d3.select(container)
        .append('svg')
        .attr('width', '100%')
        .attr('height', '100%')
        .attr('viewBox', [0, 0, width, height])
        .style('display', 'block');

    // Scales
    const xScale = d3.scaleTime()
        .domain(d3.extent(data, d => d.date))
        .range([margin.left, width - margin.right]);

    const yScale = d3.scaleLog() // Use log scale if values vary widely
        .domain([1, d3.max(data, d => d.value) || 1000000]) // Adjust domain based on data range
        .range([height - margin.bottom, margin.top])
        .clamp(true);

    // Color scale for attack types
    const attackTypes = Array.from(new Set(data.map(d => d.type))).sort();
    const colorScale = d3.scaleOrdinal(d3.schemeCategory10)
        .domain(attackTypes);

    // Axes
    const xAxis = d3.axisBottom(xScale).ticks(width / 80).tickSizeOuter(0);
    const yAxis = d3.axisLeft(yScale).ticks(5, ".1s"); // Format for log scale

    svg.append("g")
        .attr("transform", `translate(0,${height - margin.bottom})`)
        .call(xAxis)
        .call(g => g.select(".domain").remove()) // Optional: remove axis line
        .selectAll(".tick line") // Style ticks
        .attr("stroke", "#ccc");

    svg.append("g")
        .attr("transform", `translate(${margin.left},0)`)
        .call(yAxis)
        .call(g => g.select(".domain").remove())
        .selectAll(".tick line")
        .attr("stroke", "#ccc")
        .attr("stroke-dasharray", "2,2"); // Dashed grid lines

    // Axis labels
    svg.append("text")
        .attr("x", width / 2)
        .attr("y", height - margin.bottom / 3)
        .attr("text-anchor", "middle")
        .attr("font-size", 10)
        .attr("fill", "#333")
        .text("Date");

    svg.append("text")
        .attr("transform", "rotate(-90)")
        .attr("x", -(height / 2))
        .attr("y", margin.left / 3)
        .attr("text-anchor", "middle")
        .attr("font-size", 10)
        .attr("fill", "#333")
        .text("Attack Value / Impact (USD - Log Scale)");

    // Tooltip
    const tooltip = d3.select(container)
        .append("div")
        .attr("class", "tooltip")
        .style("opacity", 0)
        .style("position", "absolute")
        .style("background-color", "rgba(255, 255, 255, 0.9)")
        .style("border", "solid 1px #ccc")
        .style("border-radius", "5px")
        .style("padding", "8px")
        .style("font-size", "12px")
        .style("pointer-events", "none");

    // Draw points/circles for each attack
    svg.append("g")
        .selectAll("circle")
        .data(data)
        .join("circle")
        .attr("cx", d => xScale(d.date))
        .attr("cy", d => yScale(d.value))
        .attr("r", 5) // Fixed radius, or scale based on another metric
        .attr("fill", d => colorScale(d.type))
        .attr("stroke", "#fff")
        .attr("stroke-width", 1)
        .attr("opacity", 0.8)
        .on("mouseover", (event, d) => {
            tooltip.transition().duration(100).style("opacity", 0.9);
            tooltip.html(`
                <strong>${d.name || d.type}</strong><br/>
                <strong>Date:</strong> ${d.date.toLocaleDateString()}<br/>
                <strong>Type:</strong> ${d.type}<br/>
                <strong>Loss (USD):</strong> ${d.value.toLocaleString()}<br/>
                ${d.description ? `<hr style='margin: 2px 0;'/>${d.description}` : ''}
            `)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 20) + "px");
            d3.select(event.currentTarget).attr("r", 7).attr("opacity", 1); // Highlight circle
        })
        .on("mouseout", (event, d) => {
            tooltip.transition().duration(300).style("opacity", 0);
            d3.select(event.currentTarget).attr("r", 5).attr("opacity", 0.8); // Reset circle
        });

    // Legend
    const legend = svg.append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top - 30})`); // Position above chart

    legend.selectAll(".legend-item")
        .data(attackTypes)
        .join("g")
        .attr("class", "legend-item")
        .attr("transform", (d, i) => `translate(${i * 120}, 0)`) // Horizontal legend, adjust spacing
        .call(g => {
            g.append("rect")
                .attr("width", 12)
                .attr("height", 12)
                .attr("fill", d => colorScale(d));
            g.append("text")
                .attr("x", 18)
                .attr("y", 9)
                .attr("font-size", 10)
                .attr("alignment-baseline", "middle")
                .text(d);
        });

    // Title
    svg.append("text")
        .attr("x", width / 2)
        .attr("y", margin.top / 2)
        .attr("text-anchor", "middle")
        .attr("font-size", "16px")
        .attr("font-weight", "bold")
        .text("Timeline of Major Solana Security Incidents");

    return svg.node();
}

// Example Usage (using data similar to timeline.json):
// fetch('../reports/security_incidents/timeline.json')
//   .then(response => response.json())
//   .then(data => {
//     createAttackTimeline(data, document.getElementById('timeline-container'));
//   })
//   .catch(error => console.error('Error loading timeline data:', error));
