-- Dune Analytics Query for X (Twitter) Related ICO Analysis on Solana
-- Analyzes fundraising, distribution, and fund flows for ICOs promoted on X.

-- Define known ICO tokens potentially promoted via X/Twitter
WITH x_ico_tokens AS (
    SELECT
        mint_address,
        token_symbol,
        token_name,
        twitter_handle, -- Key identifier for this analysis
        launch_date,
        initial_price_usd
    FROM (
        VALUES
            -- Add known token mint addresses, symbols, names, Twitter handles, launch dates, and initial prices
            ('TOKEN_MINT_ADDRESS_1', 'XTOKEN1', 'X Token One', 'x_project_handle_1', '2023-10-01'::date, 0.05),
            ('TOKEN_MINT_ADDRESS_2', 'XTOKEN2', 'X Token Two', 'x_project_handle_2', '2023-09-15'::date, 0.10),
            ('TOKEN_MINT_ADDRESS_3', 'XTOKEN3', 'X Token Three', 'x_project_handle_3', '2023-08-20'::date, 0.01)
            -- ... add more tokens identified through research
    ) AS t(mint_address, token_symbol, token_name, twitter_handle, launch_date, initial_price_usd)
),

-- Identify project wallets associated with these ICOs (requires manual research or heuristics)
ico_project_wallets AS (
    SELECT
        mint_address,
        project_wallet
    FROM (
        VALUES
            ('TOKEN_MINT_ADDRESS_1', 'PROJECT_WALLET_1A'),
            ('TOKEN_MINT_ADDRESS_1', 'PROJECT_WALLET_1B'),
            ('TOKEN_MINT_ADDRESS_2', 'PROJECT_WALLET_2'),
            ('TOKEN_MINT_ADDRESS_3', 'PROJECT_WALLET_3')
            -- ... add more project wallets associated with each token
    ) AS t(mint_address, project_wallet)
),

-- Analyze fundraising transactions (e.g., SOL, USDC, USDT sent to project wallets around launch)
fundraising_txs AS (
    SELECT
        xit.mint_address,
        xit.token_symbol,
        tf.block_time,
        tf.tx_hash,
        tf.from_address AS investor_address,
        tf.to_address AS project_wallet,
        tf.token_symbol AS fundraising_token,
        tf.amount,
        tf.amount_usd
    FROM x_ico_tokens xit
    JOIN solana.token_transfers tf ON tf.to_address IN (SELECT project_wallet FROM ico_project_wallets ipw WHERE ipw.mint_address = xit.mint_address)
    WHERE
        -- Analyze transfers within a window around the launch date (e.g., 7 days before to 30 days after)
        tf.block_time BETWEEN (xit.launch_date - INTERVAL '7' day) AND (xit.launch_date + INTERVAL '30' day)
        AND tf.token_symbol IN ('SOL', 'USDC', 'USDT') -- Common fundraising tokens
),

-- Analyze initial token distribution (holders shortly after launch)
initial_distribution AS (
     SELECT
        xit.mint_address,
        COUNT(DISTINCT tb.holder_address) AS initial_holder_count,
        SUM(tb.balance) AS total_distributed,
        MAX(tb.balance) AS largest_holder_balance
        -- Calculate Gini coefficient or other distribution metrics if needed
    FROM x_ico_tokens xit
    JOIN solana.token_balances tb ON xit.mint_address = tb.mint_address
    WHERE
        -- Snapshot distribution shortly after launch (e.g., within 1-7 days)
        tb.block_time BETWEEN xit.launch_date AND (xit.launch_date + INTERVAL '7' day)
        AND tb.balance > 0
    GROUP BY xit.mint_address
),

-- Analyze fund flows *from* project wallets after fundraising
post_ico_fund_flows AS (
     SELECT
        xit.mint_address,
        xit.token_symbol,
        tf.block_time,
        tf.tx_hash,
        tf.from_address AS project_wallet,
        tf.to_address AS destination_address,
        al.label AS destination_label,
        al.label_type AS destination_type, -- e.g., 'exchange', 'defi', 'team_wallet'
        tf.token_symbol AS flow_token,
        tf.amount,
        tf.amount_usd
    FROM x_ico_tokens xit
    JOIN solana.token_transfers tf ON tf.from_address IN (SELECT project_wallet FROM ico_project_wallets ipw WHERE ipw.mint_address = xit.mint_address)
    LEFT JOIN solana.address_labels al ON tf.to_address = al.address
    WHERE
        -- Analyze flows starting after the main fundraising period
        tf.block_time > (xit.launch_date + INTERVAL '1' day)
        AND tf.block_time <= (xit.launch_date + INTERVAL '90' day) -- Analyze flows for 90 days post-launch
        AND tf.token_symbol IN ('SOL', 'USDC', 'USDT') -- Track movement of raised funds
)

-- Query 1: Summary metrics per ICO
SELECT
    xit.token_symbol,
    xit.token_name,
    xit.twitter_handle,
    xit.launch_date,
    xit.initial_price_usd,
    COALESCE(SUM(ft.amount_usd), 0) AS total_raised_usd,
    COUNT(DISTINCT ft.investor_address) AS unique_investors,
    id.initial_holder_count,
    id.largest_holder_balance / NULLIF(id.total_distributed, 0) * 100 AS largest_holder_percentage
FROM x_ico_tokens xit
LEFT JOIN fundraising_txs ft ON xit.mint_address = ft.mint_address
LEFT JOIN initial_distribution id ON xit.mint_address = id.mint_address
GROUP BY
    xit.token_symbol,
    xit.token_name,
    xit.twitter_handle,
    xit.launch_date,
    xit.initial_price_usd,
    id.initial_holder_count,
    id.total_distributed,
    id.largest_holder_balance
ORDER BY xit.launch_date DESC;

-- Query 2: Aggregated Fund Flow Destinations
SELECT
    piff.destination_type,
    piff.destination_label,
    COUNT(DISTINCT piff.tx_hash) AS transaction_count,
    SUM(piff.amount_usd) AS total_usd_flow,
    COUNT(DISTINCT piff.project_wallet) AS unique_source_project_wallets
FROM post_ico_fund_flows piff
WHERE piff.amount_usd > 100 -- Filter small transfers if needed
GROUP BY 1, 2
ORDER BY total_usd_flow DESC
LIMIT 100;

-- Query 3: Fundraising Timeline (Example for one token)
-- SELECT
--     DATE_TRUNC('day', block_time) AS fundraising_day,
--     SUM(amount_usd) AS daily_raised_usd
-- FROM fundraising_txs
-- WHERE token_symbol = 'XTOKEN1' -- Filter for a specific token
-- GROUP BY 1
-- ORDER BY 1;