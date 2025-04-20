const notebookData = {
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "title-cell",
        "language": "markdown"
      },
      "source": [
        "# Solana Staking Dashboard",
        "",
        "This dashboard provides insights into Solana staking activities. Analyze trends in staked amounts, rewards, and APY over time. Use the controls to filter by date range and specific validators."
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "imports-cell",
        "language": "javascript"
      },
      "source": [
        "// Import libraries",
        "import * as d3 from \"d3\"",
        "import { Inputs } from \"@observablehq/inputs\"",
        "import { Chart } from \"chart.js\" // Assuming Chart.js for simplicity",
        "import { fetchFromCollector, hasCollector } from \"../utils/collector-connector.js\""
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "data-source-cell",
        "language": "javascript"
      },
      "source": [
        "// Main notebook variables",
        "viewof dataSource = Inputs.radio(",
        "  [\"Sample Data\", \"Fetch from API\"],",
        "  {value: \"Sample Data\", label: \"Data Source\"}",
        ")"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "date-range-cell",
        "language": "javascript"
      },
      "source": [
        "// Date range filter",
        "viewof dateRange = Inputs.range(",
        "  [new Date(\"2023-01-01\"), new Date(\"2023-10-31\")],",
        "  {value: [new Date(\"2023-09-01\"), new Date(\"2023-10-31\")],",
        "   step: 86400000, // one day",
        "   label: \"Date Range\"}",
        ")"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "validator-select-cell",
        "language": "javascript"
      },
      "source": [
        "// Validator selection (example)",
        "viewof selectedValidator = Inputs.select(",
        "  [\"All Validators\", \"ValidatorA\", \"ValidatorB\", \"ValidatorC\"],",
        "  {value: \"All Validators\", label: \"Select Validator\"}",
        ")"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "data-loading-cell",
        "language": "javascript"
      },
      "source": [
        "// Data loading function",
        "stakingData = {",
        "  if (dataSource === \"Sample Data\") {",
        "    return stakingSampleData;",
        "  } else {",
        "    // Use real data from staking collector",
        "    try {",
        "      if (!hasCollector('staking')) {",
        "        throw new Error('Staking collector not available');",
        "      }",
        "      ",
        "      // Show loading indicator",
        "      const loadingMsg = md`**Loading staking data from blockchain...**  \nThis may take a moment as we analyze validator activity.`;",
        "      yield loadingMsg;",
        "      ",
        "      // Get real staking data",
        "      let realData;",
        "      if (selectedValidator !== \"All Validators\") {",
        "        // Fetch data for specific validator",
        "        realData = await fetchFromCollector('staking', 'get_validator_history', selectedValidator);",
        "      } else {",
        "        // Fetch aggregate data for all validators",
        "        realData = await fetchFromCollector('staking', 'get_network_staking_data');",
        "      }",
        "      ",
        "      // Use real data if available",
        "      if (realData && realData.length > 0) {",
        "        return realData;",
        "      }",
        "      ",
        "      // Log info about fallback",
        "      console.log('No staking data found, using sample data');",
        "      return stakingSampleData;",
        "    } catch (error) {",
        "      console.error(\"Error loading staking data:\", error);",
        "      return stakingSampleData.map(item => ({",
        "        ...item,",
        "        _error: error.message,",
        "        _note: 'Sample data due to collector error'",
        "      }));",
        "    }",
        "  }",
        "}"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "filtered-data-cell",
        "language": "javascript"
      },
      "source": [
        "// Filtered data based on selections",
        "filteredStakingData = {",
        "  const startDate = dateRange[0];",
        "  const endDate = dateRange[1];",
        "",
        "  return stakingData.filter(d => {",
        "    const date = new Date(d.date);",
        "    const validatorMatch = selectedValidator === \"All Validators\" || d.validator === selectedValidator;",
        "    return date >= startDate && date <= endDate && validatorMatch;",
        "  });",
        "}"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "summary-stats-cell",
        "language": "javascript"
      },
      "source": [
        "// Summary Statistics",
        "summaryStats = {",
        "  if (!filteredStakingData.length) return \"No data for selected period/validator.\";",
        "",
        "  const totalStaked = d3.sum(filteredStakingData, d => d.staked_amount_sol);",
        "  const totalRewards = d3.sum(filteredStakingData, d => d.rewards_sol);",
        "  const avgApy = d3.mean(filteredStakingData, d => d.apy_percentage);",
        "  const uniqueValidators = new Set(filteredStakingData.map(d => d.validator)).size;",
        "",
        "  return md`",
        "  ## Staking Summary (${selectedValidator})",
        "",
        "  - **Total SOL Staked**: ${totalStaked.toLocaleString(undefined, {maximumFractionDigits: 2})} SOL",
        "  - **Total Rewards Earned**: ${totalRewards.toLocaleString(undefined, {maximumFractionDigits: 4})} SOL",
        "  - **Average APY**: ${avgApy.toFixed(2)}%",
        "  - **Validators Analyzed**: ${selectedValidator === \"All Validators\" ? uniqueValidators : 1}",
        "  `;",
        "}"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "staked-chart-cell",
        "language": "javascript"
      },
      "source": [
        "// Staked Amount Over Time Chart",
        "stakedAmountChart = {",
        "  const ctx = DOM.context2d(800, 400);",
        "",
        "  const timeData = d3.rollup(",
        "    filteredStakingData,",
        "    v => d3.sum(v, d => d.staked_amount_sol),",
        "    d => d3.timeDay(new Date(d.date))",
        "  );",
        "",
        "  const chartData = Array.from(timeData, ([date, value]) => ({ date, value }))",
        "                         .sort((a, b) => a.date - b.date);",
        "",
        "  new Chart(ctx, {",
        "    type: 'line',",
        "    data: {",
        "      labels: chartData.map(d => d.date.toLocaleDateString()),",
        "      datasets: [{",
        "        label: 'Total SOL Staked',",
        "        data: chartData.map(d => d.value),",
        "        borderColor: 'rgb(75, 192, 192)',",
        "        tension: 0.1",
        "      }]",
        "    },",
        "    options: {",
        "      responsive: true,",
        "      plugins: {",
        "        title: { display: true, text: 'Total Staked SOL Over Time' }",
        "      },",
        "      scales: {",
        "        x: { title: { display: true, text: 'Date' } },",
        "        y: { title: { display: true, text: 'SOL Staked' } }",
        "      }",
        "    }",
        "  });",
        "",
        "  return ctx.canvas;",
        "}"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "rewards-chart-cell",
        "language": "javascript"
      },
      "source": [
        "// Rewards Over Time Chart",
        "rewardsChart = {",
        "  const ctx = DOM.context2d(800, 400);",
        "",
        "  const timeData = d3.rollup(",
        "    filteredStakingData,",
        "    v => d3.sum(v, d => d.rewards_sol),",
        "    d => d3.timeDay(new Date(d.date))",
        "  );",
        "",
        "  const chartData = Array.from(timeData, ([date, value]) => ({ date, value }))",
        "                         .sort((a, b) => a.date - b.date);",
        "",
        "  new Chart(ctx, {",
        "    type: 'bar',",
        "    data: {",
        "      labels: chartData.map(d => d.date.toLocaleDateString()),",
        "      datasets: [{",
        "        label: 'Daily Rewards (SOL)',",
        "        data: chartData.map(d => d.value),",
        "        backgroundColor: 'rgba(255, 159, 64, 0.7)'",
        "      }]",
        "    },",
        "    options: {",
        "      responsive: true,",
        "      plugins: {",
        "        title: { display: true, text: 'Daily Staking Rewards (SOL)' }",
        "      },",
        "      scales: {",
        "        x: { title: { display: true, text: 'Date' } },",
        "        y: { title: { display: true, text: 'Rewards (SOL)' } }",
        "      }",
        "    }",
        "  });",
        "",
        "  return ctx.canvas;",
        "}"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "apy-chart-cell",
        "language": "javascript"
      },
      "source": [
        "// APY Distribution (if multiple validators)",
        "apyDistributionChart = {",
        "  if (selectedValidator !== \"All Validators\" || !filteredStakingData.length) {",
        "    return \"APY distribution requires 'All Validators' selection.\";",
        "  }",
        "",
        "  const ctx = DOM.context2d(600, 400);",
        "",
        "  const apyData = filteredStakingData.map(d => d.apy_percentage).filter(apy => !isNaN(apy));",
        "",
        "  // Simple histogram logic (using d3 for binning)",
        "  const bins = d3.bin().thresholds(10)(apyData);",
        "",
        "  new Chart(ctx, {",
        "    type: 'bar',",
        "    data: {",
        "      labels: bins.map(bin => `${bin.x0.toFixed(1)}% - ${bin.x1.toFixed(1)}%`),",
        "      datasets: [{",
        "        label: 'Number of Validator Readings',",
        "        data: bins.map(bin => bin.length),",
        "        backgroundColor: 'rgba(153, 102, 255, 0.7)'",
        "      }]",
        "    },",
        "    options: {",
        "      responsive: true,",
        "      plugins: {",
        "        title: { display: true, text: 'APY Distribution Across Validators' }",
        "      },",
        "      scales: {",
        "        x: { title: { display: true, text: 'APY Range' } },",
        "        y: { title: { display: true, text: 'Frequency' } }",
        "      }",
        "    }",
        "  });",
        "",
        "  return ctx.canvas;",
        "}"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "sample-data-cell",
        "language": "javascript"
      },
      "source": [
        "// Sample Data",
        "stakingSampleData = [",
        "  // Generate some sample data points",
        "  ...d3.timeDays(new Date(\"2023-09-01\"), new Date(\"2023-11-01\")).flatMap(date => {",
        "    const validators = [\"ValidatorA\", \"ValidatorB\", \"ValidatorC\"];",
        "    return validators.map(validator => ({",
        "      date: date.toISOString().split('T')[0],",
        "      validator: validator,",
        "      staked_amount_sol: 10000 + Math.random() * 5000 + (validators.indexOf(validator) * 2000),",
        "      rewards_sol: 1 + Math.random() * 2,",
        "      apy_percentage: 6 + Math.random() * 2 - (validators.indexOf(validator) * 0.5)",
        "    }));",
        "  })",
        "]"
      ]
    }
  ]
}
