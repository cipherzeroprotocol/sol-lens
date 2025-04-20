# SolanaLens Shared Data Directory

This directory serves as the bridge between data collection scripts and visualization components in the SolanaLens project.

## Directory Structure

```
data/
├── viz/                   # Data formatted specifically for visualizations
│   ├── network/           # Network graph data for D3 visualizations
│   ├── security/          # Security analysis data (poisoning, sandwich attacks)
│   ├── mixer/             # Mixer service analysis data
│   └── defi/              # DeFi-related analysis data
├── raw/                   # Raw data collected from APIs
└── processed/             # Intermediate processed data
```

## Data Flow

1. Python scripts in `scripts/` collect and analyze data
2. Data is exported to this directory using `DataExporter` class
3. JavaScript visualizations load data using `data-loader.js`

## File Naming Conventions

- `*_latest.json` - Most recent version of a dataset, always overwritten
- `*_YYYYMMDD_HHMMSS.json` - Timestamped version for historical reference

## Data Types

### Network Graph Data

Format expected by D3 force-directed graph visualizations:

```json
{
  "nodes": [
    {"id": "node1", "type": "account", "value": 10, ...},
    ...
  ],
  "links": [
    {"source": "node1", "target": "node2", "value": 1, ...},
    ...
  ],
  "metadata": {
    "name": "graph_name",
    "description": "...",
    "generated_at": "ISO timestamp"
  }
}
```

### Time-Series Data

Format for charts and timelines:

```json
{
  "dataset_name": "dataset_name",
  "dataset_type": "timeline",
  "generated_at": "ISO timestamp",
  "data": [
    {"timestamp": "ISO date", "value": 123, ...},
    ...
  ]
}
```

## Usage Notes

- When adding new data types, update both the Python `DataExporter` class and the JavaScript `data-loader.js` utility
- Keep both timestamped and latest versions of datasets for tracking changes over time
