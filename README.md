To activate an isolated virtual env & install dependencies run `. ./setup.sh`.
To run the script itself `python pull_recent_order_books.py`

**My process**
- Read over requirements multiple times
- Conducted some preliminary research (detailed below)
- Selected two marketplaces and explored the data returned by their order book APIs
- Diagramed overall architecture including dataflow and final table structures
- Provisioned AWS account for this project (dedicated EC2, SSM, Postgres)
- Wrote the code (`pull_recent_order_books.py`)
- Deployed the code (simple CI/CD GH workflow)
- Schedule code to run once per hour as a cron job (simple solution for now)
- Monitor output for a bit to ensure it's working properly
  - Performance did change once running on an EC2, required me to utilize proxies to ensure data could be pulled from Binance within the US.
  
**Background research**

- Coinbase has lower fees for larger transactions (0.35% between 10K and 50K vs .50% at <10K).
- Bids and asks already sorted in a very helpful order. Highest bids first, lowest asks first.
- Using level 3 orderbook, need to be aware that Coinbase warns to not abuse. Should swap to use level 2 if transaction_id granularity isn’t required.
- Could use level 1 orderbook for mid price instead of calculating ourselves.
- No need for a heavy streaming solution yet quite yet. Postgres can work fine if we model the data properly
by separating out facts and dimensions while also indexing the tables efficiently. Views on top of these tables to assist analytics will also be essential.


**Future opportunities**
- Add function / script to pull from raw order data and fully repopulate `optimal_transactions` table in the event we wish to change the $100K USD threshold.
- Enhanced monitoring, catch response codes from APIs and log failures to Kibana / Grafana / (other soluton)
- Unit tests
- Structure raw order book data better prior to writing.
- Documentation for all the fields. Does Core Scientific use a data catalog?

**Assumptions made**

- While we are persisting the raw order book data, it isn't to be consumed on a frequent basis and thus S3 in a fairly unstructured format is sufficient for a POC. The tables & views derived during each poll are what is useful for analysis
- When there are spending thresholds outlined for this project such as $100,000 or $50,000, we either always stay a little under or a little over.


![Order Book Diagrams drawio](https://user-images.githubusercontent.com/128027142/226431737-bc287fd3-842f-419d-83fd-a3ae49839c12.svg)
