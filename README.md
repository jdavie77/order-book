To activate an isolated virtual env & install dependencies run `. ./setup.sh`


**Background research**

- Coinbase has lower fees for larger transactions (0.35% between 10K and 50K vs .50% at <10K).

- Bids and Asks come from the API already sorted in order we’d be most interested in using the data. Highest bids first, lowest asks first.
- Using level 3 orderbook, need to be aware that Coinbase warns to not abuse. Should swap to use level 2 if transaction_id granularity isn’t required.
- Could use level 1 orderbook for mid price instead of calculating ourselves.
- No need for a heavy streaming solution. Postgres works fine.
- In the future if we expect to be using the raw order book data, we could start structuring it more nicely prior to writing it.
