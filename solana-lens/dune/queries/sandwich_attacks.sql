-- Dune Analytics Query for Solana Sandwich Attack Detection
-- Identifies potential sandwich attacks by looking for front-run/back-run patterns around victim trades.

-- Define parameters
WITH params AS (
    SELECT
        interval '7' day AS analysis_window, -- How far back to look
        interval '10' second AS max_time_diff, -- Max time between front-run/victim and victim/back-run
        0.01 AS min_profit_usd, -- Minimum profit in USD to consider it an attack
        ARRAY['Raydium', 'Orca', 'Jupiter Aggregator', 'Serum'] AS target_dex -- DEXs to analyze
),

-- Get all DEX swaps within the analysis window
dex_swaps AS (
    SELECT
        block_time,
        block_slot,
        tx_hash,
        dex_program,
        trader_address,
        input_mint,
        output_mint,
        input_amount,
        output_amount,
        input_amount_usd,
        output_amount_usd
    FROM solana.dex_trades
    CROSS JOIN params
    WHERE block_time >= NOW() - params.analysis_window
      AND dex_program = ANY(params.target_dex)
      AND input_amount_usd > 10 -- Filter out very small trades
),

-- Identify potential sandwich patterns
-- Look for triplets: Attacker Buy -> Victim Swap -> Attacker Sell
-- Matching token pair, DEX, and occurring close together in time/blocks
potential_sandwiches AS (
    SELECT
        -- Front-run (Attacker Buy)
        a_buy.block_time AS front_run_time,
        a_buy.block_slot AS front_run_slot,
        a_buy.tx_hash AS front_run_tx,
        a_buy.trader_address AS attacker_address,
        a_buy.dex_program,
        a_buy.input_mint AS attacker_buy_input_mint,   -- e.g., USDC
        a_buy.output_mint AS attacker_buy_output_mint, -- e.g., SOL (Token being bought)
        a_buy.input_amount_usd AS front_run_usd,

        -- Victim Swap (Victim Buys or Sells the same token)
        victim.block_time AS victim_time,
        victim.block_slot AS victim_slot,
        victim.tx_hash AS victim_tx,
        victim.trader_address AS victim_address,
        victim.input_amount_usd AS victim_input_usd,
        victim.output_amount_usd AS victim_output_usd,

        -- Back-run (Attacker Sell)
        a_sell.block_time AS back_run_time,
        a_sell.block_slot AS back_run_slot,
        a_sell.tx_hash AS back_run_tx,
        a_sell.output_amount_usd AS back_run_usd,

        -- Profit Calculation
        (a_sell.output_amount_usd - a_buy.input_amount_usd) AS profit_usd,

        -- Time differences
        (victim.block_time - a_buy.block_time) AS diff_front_victim,
        (a_sell.block_time - victim.block_time) AS diff_victim_back

    FROM dex_swaps a_buy
    JOIN dex_swaps victim ON a_buy.dex_program = victim.dex_program -- Same DEX
        AND a_buy.trader_address != victim.trader_address -- Different trader
        AND (
            -- Case 1: Victim buys the token the attacker front-ran
            (a_buy.output_mint = victim.output_mint AND a_buy.input_mint = victim.input_mint) OR
            -- Case 2: Victim sells the token the attacker front-ran
            (a_buy.output_mint = victim.input_mint AND a_buy.input_mint = victim.output_mint)
        )
        AND victim.block_slot >= a_buy.block_slot -- Victim tx is at or after attacker buy
        AND victim.block_time >= a_buy.block_time
        AND victim.block_time <= a_buy.block_time + (SELECT max_time_diff FROM params) -- Victim tx close after attacker buy
    JOIN dex_swaps a_sell ON victim.dex_program = a_sell.dex_program -- Same DEX
        AND a_buy.trader_address = a_sell.trader_address -- Same attacker
        AND a_buy.output_mint = a_sell.input_mint -- Attacker sells the token they bought
        AND a_buy.input_mint = a_sell.output_mint -- Attacker gets back the original token
        AND a_sell.block_slot >= victim.block_slot -- Attacker sell is at or after victim tx
        AND a_sell.block_time >= victim.block_time
        AND a_sell.block_time <= victim.block_time + (SELECT max_time_diff FROM params) -- Attacker sell close after victim tx
    CROSS JOIN params
    WHERE (a_sell.output_amount_usd - a_buy.input_amount_usd) > params.min_profit_usd -- Filter by minimum profit
)

-- Query 1: List identified sandwich attacks
SELECT
    front_run_time,
    victim_time,
    back_run_time,
    attacker_address,
    victim_address,
    dex_program,
    attacker_buy_output_mint AS sandwiched_token_mint, -- The token whose price was manipulated
    front_run_usd,
    victim_input_usd,
    victim_output_usd,
    back_run_usd,
    profit_usd,
    front_run_tx,
    victim_tx,
    back_run_tx,
    diff_front_victim,
    diff_victim_back
FROM potential_sandwiches
ORDER BY front_run_time DESC
LIMIT 1000;

-- Query 2: Summary statistics by Attacker
SELECT
    attacker_address,
    COUNT(*) AS attack_count,
    SUM(profit_usd) AS total_profit_usd,
    AVG(profit_usd) AS avg_profit_usd,
    ARRAY_AGG(DISTINCT dex_program) AS dexs_used,
    MIN(front_run_time) AS first_attack_time,
    MAX(back_run_time) AS last_attack_time
FROM potential_sandwiches
GROUP BY 1
ORDER BY total_profit_usd DESC
LIMIT 100;

-- Query 3: Summary statistics by DEX
SELECT
    dex_program,
    COUNT(*) AS attack_count,
    SUM(profit_usd) AS total_profit_usd,
    AVG(profit_usd) AS avg_profit_usd,
    COUNT(DISTINCT attacker_address) AS unique_attackers,
    COUNT(DISTINCT victim_address) AS unique_victims
FROM potential_sandwiches
GROUP BY 1
ORDER BY attack_count DESC;

-- Query 4: Summary statistics by Token Pair (approximated)
SELECT
    attacker_buy_input_mint AS token_a, -- e.g., USDC
    attacker_buy_output_mint AS token_b, -- e.g., SOL
    COUNT(*) AS attack_count,
    SUM(profit_usd) AS total_profit_usd
FROM potential_sandwiches
GROUP BY 1, 2
ORDER BY attack_count DESC
LIMIT 50;
