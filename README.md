To activate an isolated virtual env & install dependencies run `. ./setup.sh`


**Background research**

- Coinbase has lower fees for larger transactions (0.35% between 10K and 50K vs .50% at <10K).

- Bids and Asks come from the API already sorted in a very helpful order. Highest bids first, lowest asks first.
- Using level 3 orderbook, need to be aware that Coinbase warns to not abuse. Should swap to use level 2 if transaction_id granularity isn’t required.
- Could use level 1 orderbook for mid price instead of calculating ourselves.
- No need for a heavy streaming solution. Postgres works fine. If we maintain the cadence of one pull per 60 seconds, the larger table `optimal_transactions` will have ~31 million rows after 3 years.

**Future opportunities**
- Add function / script to pull from raw order data and fully repopulate `optimal_transactions` table in the event we wish to change the $100K USD threshold.
- In the future if we expect to be using the raw order book data, we could start structuring it more nicely prior to writing it.
