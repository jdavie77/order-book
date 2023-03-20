CREATE TABLE postgres.public.transactions_summary (
      coin_transaction_id varchar primary key,
      exchange varchar,
      coin varchar,
      transaction_limit bigint,
      mid_price float,
      profit_opportunity float,
      pull_timestamp bigint,
      run_length bigint,
      run_id varchar
);

CREATE TABLE postgres.public.optimal_transactions (
      coin_price float,
      amount_requested float,
      transaction_cost float,
      transaction_type varchar,
      pull_timestamp bigint,
      coin_transaction_id varchar
);
CREATE INDEX pull_timestamp ON postgres.public.optimal_transactions(pull_timestamp) WITH (deduplicate_items = off);


-- Views for answering questions related to analysis
CREATE OR REPLACE VIEW postgres.public.recent_transactions AS
WITH last_two_days_transactions AS (
    SELECT * FROM postgres.public.optimal_transactions
    WHERE pull_timestamp >
          EXTRACT(EPOCH FROM NOW()) - (EXTRACT(EPOCH FROM NOW()) - (60 * 60 * 24 * 2)) -- Two days back from now
)
SELECT all_transactions.*
     ,exchange
     ,coin
     ,mid_price
     ,CASE WHEN coin ilike '%btc%' THEN 'bitcoin'
           WHEN coin ilike '%eth%' then 'ethereum'
    END crypto_currency
     ,run_id
FROM last_two_days_transactions all_transactions
         LEFT JOIN postgres.public.transactions_summary USING (coin_transaction_id);


CREATE OR REPLACE VIEW best_way_to_buy_or_sell_50k AS

WITH keep_most_recent_data AS (
    SELECT transaction_type,exchange,coin,transaction_cost
         ,amount_requested,coin_price,coin_transaction_id,crypto_currency
         ,pull_timestamp
         ,RANK() OVER (
             PARTITION BY EXCHANGE,COIN,transaction_type
             ORDER BY pull_timestamp DESC) most_recent_data
    FROM postgres.public.recent_transactions
)
   , calculate_rolling_costs AS (
    SELECT *
         ,SUM(CASE WHEN transaction_type = 'ask' THEN transaction_cost END) OVER (
        PARTITION BY coin_transaction_id,transaction_type ORDER BY coin_price
        ) rolling_asking_cost

         ,SUM(CASE WHEN transaction_type = 'bid' THEN transaction_cost END) OVER (
        PARTITION BY coin_transaction_id,transaction_type ORDER BY coin_price DESC
        ) rolling_bidding_cost
    FROM keep_most_recent_data
    WHERE most_recent_data = 1
), find_cost_per_coin_per_exchange AS (
    SELECT transaction_type
         ,exchange
         ,crypto_currency
         , sum(amount_requested) amount_requested
         , sum(transaction_cost) total_cost
         , sum(transaction_cost) / sum(amount_requested) cost_per_coin
    FROM calculate_rolling_costs
    where transaction_type = 'bid'
      and rolling_bidding_cost <= 55000
    GROUP BY 1,2,3
    UNION ALL
    SELECT transaction_type
         ,exchange
         ,crypto_currency
         ,sum(amount_requested) amount_requested
         ,sum(transaction_cost) total_cost
         , sum(transaction_cost) / sum(amount_requested) cost_per_coin
    FROM calculate_rolling_costs
    where transaction_type = 'ask'
      and rolling_asking_cost <= 55000
    GROUP BY 1,2,3
), label_best_exchange AS (
    SELECT *
         ,ROW_NUMBER() OVER (
        PARTITION BY transaction_type,crypto_currency
        ORDER BY cost_per_coin DESC) best_value
    FROM find_cost_per_coin_per_exchange
)
SELECT * FROM label_best_exchange where best_value = 1;