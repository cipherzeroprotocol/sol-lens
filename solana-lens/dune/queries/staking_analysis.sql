-- Dune Analytics Query for Solana Staking Analysis
-- Analyzes staking deposits, withdrawals, rewards, and validator performance.

-- Define parameters
WITH params AS (
    SELECT
        interval '90' day AS analysis_window -- How far back to look
),

-- Get SOL transfers (potential staking deposits/withdrawals/rewards)
sol_transfers AS (
    SELECT
        block_time,
        tx_hash,
        from_address,
        to_address,
        amount,
        amount_usd
    FROM solana.token_transfers
    CROSS JOIN params
    WHERE token_symbol = 'SOL'
      AND block_time >= NOW() - params.analysis_window
),

-- Identify stake account creations and delegations (more accurate than just transfers)
-- Note: This requires specific decoding of stake program instructions.
-- This is a simplified placeholder; a real query would parse instruction data.
stake_delegations AS (
    SELECT
        block_time,
        tx_hash,
        signers[1] AS staker_address, -- Assuming signer[1] is the staker
        -- Extract delegate_stake instruction details
        json_extract_scalar(instructions[1], '$.parsed.info.stakeAccount') AS stake_account,
        json_extract_scalar(instructions[1], '$.parsed.info.voteAccount') AS validator_vote_account
        -- Need to join with transactions table to get amount if not in instruction
    FROM solana.transactions
    CROSS JOIN params
    WHERE block_time >= NOW() - params.analysis_window
      AND array_contains(instructions.program_id, 'Stake11111111111111111111111111111111111111') -- Solana Stake Program
      AND json_extract_scalar(instructions[1], '$.parsed.type') = 'delegate' -- Filter for delegation instructions
      -- This parsing logic is illustrative and needs refinement based on actual data structure
),

-- Get validator information (including commission, APY if available)
-- Note: APY often requires off-chain calculation or specific data sources.
validator_info AS (
    SELECT
        vote_pubkey AS validator_vote_account,
        node_pubkey AS validator_identity,
        commission,
        activated_stake
        -- Add name, website, APY data if available from tables like solana.validators or external sources
    FROM solana.validators -- Check if this table exists and has the required info
    WHERE epoch = (SELECT MAX(epoch) FROM solana.validators) -- Get latest epoch data
),

-- Approximate staking rewards (often small SOL transfers from known reward sources or stake accounts)
-- This is highly heuristic and less reliable than epoch reward data if available.
potential_rewards AS (
    SELECT
        st.block_time,
        st.tx_hash,
        st.from_address, -- Often a stake account or reward distributor
        st.to_address AS recipient_address,
        st.amount,
        st.amount_usd
    FROM sol_transfers st
    WHERE
        st.amount < 1 -- Rewards are typically small amounts
        AND st.amount > 0
        -- Add filters based on known reward distribution patterns or source addresses if identified
        -- e.g., AND st.from_address IN (SELECT stake_account FROM stake_delegations)
)

-- Query 1: Total Staked SOL Over Time (Approximation using delegations)
-- Note: A better approach uses epoch snapshots of activated stake if available.
SELECT
    DATE_TRUNC('day', block_time) AS day,
    COUNT(DISTINCT tx_hash) AS daily_delegations,
    COUNT(DISTINCT staker_address) AS daily_unique_stakers
    -- SUM(delegated_amount) -- Requires joining to get amount
FROM stake_delegations
GROUP BY 1
ORDER BY 1;

-- Query 2: Top Validators by Delegated Stake (from latest epoch)
SELECT
    vi.validator_vote_account,
    vi.validator_identity,
    vi.commission,
    vi.activated_stake,
    (SELECT COUNT(DISTINCT sd.staker_address)
     FROM stake_delegations sd
     WHERE sd.validator_vote_account = vi.validator_vote_account) AS estimated_delegator_count
FROM validator_info vi
ORDER BY vi.activated_stake DESC
LIMIT 100;

-- Query 3: Estimated Rewards Distribution Over Time
SELECT
    DATE_TRUNC('day', block_time) AS day,
    SUM(amount) AS total_rewards_sol,
    SUM(amount_usd) AS total_rewards_usd,
    COUNT(DISTINCT recipient_address) AS unique_reward_recipients
FROM potential_rewards
GROUP BY 1
ORDER BY 1;

-- Query 4: Staking Activity per Staker (Example for top stakers by delegation count)
WITH staker_activity AS (
    SELECT
        staker_address,
        COUNT(DISTINCT tx_hash) AS delegation_count,
        ARRAY_AGG(DISTINCT validator_vote_account) AS validators_used,
        MIN(block_time) AS first_delegation,
        MAX(block_time) AS last_delegation
    FROM stake_delegations
    GROUP BY 1
    ORDER BY delegation_count DESC
    LIMIT 100
)
SELECT
    sa.staker_address,
    sa.delegation_count,
    sa.validators_used,
    sa.first_delegation,
    sa.last_delegation,
    COALESCE(SUM(pr.amount), 0) AS estimated_total_rewards_sol
FROM staker_activity sa
LEFT JOIN potential_rewards pr ON sa.staker_address = pr.recipient_address
GROUP BY 1, 2, 3, 4, 5
ORDER BY sa.delegation_count DESC;
