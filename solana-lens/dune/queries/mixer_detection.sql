-- Dune Analytics Query for Solana Mixer Detection
-- Identifies potential mixer usage patterns based on interactions with known mixer addresses and heuristics.

-- Define known mixer addresses on Solana
WITH known_mixers AS (
    SELECT address, label FROM (VALUES
        ('tor1xzb2Zyy1cUxXmyJfR8aNXuWnwHG8AwgaG7UGD4K', 'Tornado Cash Router'), -- Example, verify address
        ('1MixerZCaShtMCAdLozKTzVdLFf9WZqDehHHQdT1V5Pf', 'SolMixer'), -- Example, verify address
        ('mixBkFZP3Z1hGWaXeYPxvyzh2Wuq2nIUQBNCZHLbwiU', 'Cyclos Privacy Pool') -- Example, verify address
        -- Add more known or suspected mixer addresses
    ) AS t(address, label)
),

-- Time window for analysis
analysis_window AS (
    SELECT interval '90' day AS duration
),

-- Transactions depositing funds INTO known mixers
mixer_deposits AS (
    SELECT
        tf.block_time,
        tf.tx_hash,
        tf.from_address AS depositor_address,
        tf.to_address AS mixer_address,
        km.label AS mixer_label,
        tf.token_symbol,
        tf.amount,
        tf.amount_usd
    FROM solana.token_transfers tf
    JOIN known_mixers km ON tf.to_address = km.address
    CROSS JOIN analysis_window aw
    WHERE tf.block_time >= NOW() - aw.duration
      AND tf.amount_usd > 1 -- Filter out potential dust
),

-- Transactions withdrawing funds FROM known mixers
mixer_withdrawals AS (
    SELECT
        tf.block_time,
        tf.tx_hash,
        tf.from_address AS mixer_address,
        km.label AS mixer_label,
        tf.to_address AS recipient_address,
        tf.token_symbol,
        tf.amount,
        tf.amount_usd
    FROM solana.token_transfers tf
    JOIN known_mixers km ON tf.from_address = km.address
    CROSS JOIN analysis_window aw
    WHERE tf.block_time >= NOW() - aw.duration
      AND tf.amount_usd > 1 -- Filter out potential dust
),

-- Heuristic: Identify addresses depositing and withdrawing within a short time frame
suspicious_cycles AS (
    SELECT
        dep.depositor_address,
        wd.recipient_address,
        dep.mixer_address,
        dep.mixer_label,
        dep.block_time AS deposit_time,
        wd.block_time AS withdrawal_time,
        (wd.block_time - dep.block_time) AS time_diff,
        dep.amount_usd AS deposit_usd,
        wd.amount_usd AS withdrawal_usd
    FROM mixer_deposits dep
    JOIN mixer_withdrawals wd ON dep.mixer_address = wd.mixer_address
                             AND dep.token_symbol = wd.token_symbol -- Match token
                             AND wd.block_time > dep.block_time
                             AND wd.block_time <= dep.block_time + interval '24' hour -- Withdrawal within 24 hours of deposit
    WHERE
        dep.depositor_address != wd.recipient_address -- Different deposit/withdrawal addresses
        -- Optional: Add value similarity check (e.g., withdrawal amount is close to deposit amount)
        -- AND ABS(dep.amount_usd - wd.amount_usd) / NULLIF(dep.amount_usd, 0) < 0.1 -- Within 10% value difference
),

-- Heuristic: Identify deposits of common "round" amounts
round_number_deposits AS (
    SELECT *
    FROM mixer_deposits
    WHERE
        (token_symbol = 'SOL' AND amount IN (0.1, 1, 10, 100, 1000)) OR
        (token_symbol = 'USDC' AND amount IN (10, 100, 1000, 10000, 100000)) OR
        (token_symbol = 'USDT' AND amount IN (10, 100, 1000, 10000, 100000))
)

-- Query 1: Summary of Mixer Activity
SELECT
    mixer_label,
    mixer_address,
    COUNT(DISTINCT tx_hash) AS total_transactions,
    COUNT(DISTINCT depositor_address) AS unique_depositors,
    COUNT(DISTINCT recipient_address) AS unique_recipients,
    SUM(CASE WHEN tf.to_address = mixer_address THEN amount_usd ELSE 0 END) AS total_deposit_usd,
    SUM(CASE WHEN tf.from_address = mixer_address THEN amount_usd ELSE 0 END) AS total_withdrawal_usd
FROM solana.token_transfers tf
JOIN known_mixers km ON tf.to_address = km.address OR tf.from_address = km.address
CROSS JOIN analysis_window aw
WHERE tf.block_time >= NOW() - aw.duration
GROUP BY 1, 2
ORDER BY total_deposit_usd DESC;

-- Query 2: List Suspicious Cycles (Deposit -> Mixer -> Withdrawal)
SELECT
    depositor_address,
    recipient_address,
    mixer_label,
    deposit_time,
    withdrawal_time,
    time_diff,
    deposit_usd,
    withdrawal_usd
FROM suspicious_cycles
ORDER BY deposit_time DESC
LIMIT 500;

-- Query 3: Addresses using Round Number Deposits Frequently
SELECT
    depositor_address,
    COUNT(*) AS round_deposit_count,
    SUM(amount_usd) AS total_round_deposit_usd,
    ARRAY_AGG(DISTINCT mixer_label) AS mixers_used
FROM round_number_deposits
GROUP BY 1
HAVING COUNT(*) >= 3 -- Addresses making 3 or more round number deposits
ORDER BY round_deposit_count DESC
LIMIT 500;