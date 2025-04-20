# SolanaLens: Multi-Bounty Research & Visualization Hub

SolanaLens is a collection of focused research reports and interactive visualizations that analyze different aspects of Solana security, including token patterns, MEV attacks, dusting attacks, and more.

## 📋 Table of Contents
1. [Installation](#installation)
2. [How to Use SolanaLens](#how-to-use-solanalens)
3. [Using Real Data](#using-real-data)
4. [Research Reports](#research-reports)
5. [Visualizations](#visualizations)
6. [Project Structure](#project-structure)
7. [Core Components](#core-components)
8. [Target Bounties](#target-bounties)
9. [Contributing](#contributing)
10. [License](#license)

## Installation

### Prerequisites
- Node.js v14.x or later
- Git
- A web browser supporting ES6

### Setup Instructions
1. Clone the repository:
```bash
git clone https://github.com/cipherzeroprotocol/sol-lens.git
cd sol-lens
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

4. Open your browser and navigate to `http://localhost:3000`

## How to Use SolanaLens

SolanaLens offers multiple ways to explore Solana security data:

### 1. Interactive Notebooks

SolanaLens provides several Observable-based notebooks for interactive data exploration:

1. **Launch a Notebook**:
   - Navigate to `http://localhost:3000/visualizations`
   - Select a notebook (e.g., "Token Network Analysis", "Sandwich Attacks")

2. **Choose Data Source**:
   - **Sample Data**: Quick exploration with pre-loaded examples
   - **Upload File**: Analyze your own JSON data
   - **Fetch from API**: Connect to live blockchain data

3. **Interact with Visualizations**:
   - Use sliders and filters to refine analysis
   - Hover over data points for details
   - Drag nodes in network graphs to explore connections

4. **Export Results**:
   - Use the Export button to download data as JSON/CSV
   - Save visualizations as PNG (where supported)

### 2. Research Reports

1. **Access Reports**:
   - Navigate to `http://localhost:3000/reports`
   - Select a report category

2. **Navigate Report Content**:
   - Use the table of contents for quick navigation
   - Interactive elements will be highlighted
   - Click on charts for expanded views

3. **Data References**:
   - Each report includes links to source data
   - SQL queries are available in the `/reports/{category}/queries` folders

### 3. Command Line Tools

Advanced users can run data collectors directly:

```bash
# Analyze dusting attacks for the past 30 days
node scripts/cli.js analyze-dusting --days 30

# Detect sandwich attacks on a specific DEX
node scripts/cli.js detect-sandwich --dex jupiter --days 14

# Analyze token creator patterns
node scripts/cli.js analyze-tokens --limit 200
```

## Using Real Data

SolanaLens supports both sample data (for demo purposes) and real blockchain data for evaluations:

### Providing API Keys

To use real blockchain data, initialize with your API keys:

```javascript
// Initialize with your API keys
SolanaLens.init({
  apiKeys: {
    helius: 'your-helius-api-key',
    range: 'your-range-api-key'
  }
});
```

### In Notebooks

All notebooks offer three data modes:
1. **Sample Data**: Pre-loaded sample data for quick testing
2. **Upload File**: Upload your own JSON data for analysis
3. **Fetch from API**: Uses real blockchain data from the collectors

For hackathon judging, select "Fetch from API" option in the notebooks for real-time blockchain analysis.

### API Key Security

Your API keys are:
- Stored only in browser localStorage (client-side)
- Never transmitted to any server
- Cleared when using the "Clear API Keys" button
- Used only for direct API calls to data providers

## Research Reports

SolanaLens includes four comprehensive research reports:

1. **X (Twitter) ICO Analysis**: Examines fundraising patterns and fund flows of ICOs promoted on X (Twitter)
   - Token distribution analysis
   - Post-ICO fund movement tracking
   - Case studies of suspicious projects

2. **Money Laundering Routes**: Maps common money laundering paths on Solana
   - Cross-chain bridge hopping techniques
   - Mixer and layering patterns
   - Detection methodologies

3. **Security Incidents History**: Timeline and analysis of major Solana security events
   - Root cause analysis of major exploits
   - Impact assessment and lessons learned
   - Technical vulnerability explanations

4. **Web2 Security Vulnerabilities**: Analysis of off-chain security issues affecting Solana projects
   - Frontend vulnerability examples
   - API security gaps
   - Infrastructure weak points

## Visualizations

SolanaLens provides interactive visualizations for:

1. **Token Network Analysis**: Examine connections between token creators to identify suspicious patterns
   - Network graph of related tokens
   - Risk scoring based on on-chain activity
   - Scam token pattern detection

2. **Sandwich Attack Visualization**: Explore MEV front-running and back-running attacks
   - Timeline of identified attacks
   - Analysis by DEX and token pair
   - Profit extraction patterns

3. **Dusting Attack Analysis**: Investigate address poisoning and tracking attempts
   - Campaign identification and tracking
   - Target wallet category analysis
   - Temporal patterns in dusting activities

4. **Staking Dashboard**: Monitor validator activities and staking patterns
   - Performance metrics
   - Distribution analysis
   - Historical trends

## Project Structure

```
solana-lens/
├── reports/                    # Research reports
│   ├── x_ico_analysis/         # X ICO report assets
│   ├── money_laundering/       # Money laundering report
│   ├── security_incidents/     # Security history report
│   └── web2_security/          # Web2 security report
├── visualizations/             # Interactive visualizations
│   ├── notebooks/              # Observable notebooks
│   │   ├── token_network.js    # Token creator network
│   │   ├── sandwich_attacks.js # MEV visualization
│   │   ├── dusting_analysis.js # Dusting attack visualization
│   │   └── staking_dashboard.js # Staking visualization
│   ├── d3/                     # D3.js visualizations
│   └── utils/                  # Shared utilities
├── scripts/                    # Data collection scripts
│   ├── collectors/             # Data collectors
│   │   ├── bridge-collector.js # Bridge analysis collector
│   │   ├── dusting-collector.js # Dusting attack collector
│   │   └── sandwich-collector.js # Sandwich attack collector
│   ├── api/                    # API clients
│   │   ├── helius-client.js    # Helius API interface
│   │   └── range-client.js     # Range API interface
│   ├── utils/                  # Shared utilities
│   └── cli.js                  # Command line interface
└── index.js                    # Main entry point
```

## Core Components

1. **Research Reports** - In-depth markdown/PDF reports on key security topics
2. **SQL Query Collection** - Dune Analytics queries that analyze on-chain data
3. **Interactive Visualizations** - Simple d3.js and Observable notebooks
4. **Data Collection Scripts** - Blockchain data collectors that feed the visualizations

## Target Bounties

This approach can win multiple bounties with minimal technical overhead:

### Research Track Bounties
- **Arkham X ICOs ($16,250)** - Research report on Twitter ICO fundraising and fund flows
- **Range War Games ($15,000)** - Analysis of money laundering routes and methods
- **Helius History of Security Incidents ($5,000)** - Timeline and analysis of major incidents
- **Guvenkaya Web2 Security ($5,000)** - Article on web2 security issues in Solana projects

### Visualization Track Bounties
- **RugCheck Onchain Analysis ($7,000)** - Network visualizations of token creator patterns
- **Helius Malicious MEV ($5,000)** - Dashboard showing sandwich attack patterns
- **Helius Account Dusting ($5,000)** - Visualization of dusting and poisoning attacks
- **Dune Data Article ($3,000)** - SQL queries analyzing Solana on-chain activity
- **Nebula Node Staking ($3,000)** - Staking visualization dashboard
- **Ded Monkes Visualization ($3,000)** - Ecosystem mapping visualization

## Contributing

We welcome contributions to SolanaLens! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

*SolanaLens - Shedding light on Solana security patterns*
