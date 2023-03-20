import json
from uuid import uuid4
import time
from typing import List, Dict, Union
from datetime import date

import requests
import pandas as pd
import boto3
from sqlalchemy import create_engine


def get_order_book_transactions(
        trade_type: List[List[str]]
) -> pd.DataFrame:
    """
    Loop through bids or asks until we find 100K USD worth and record them.
    Do not go too far over $100K, limit to <$1 USD over.

    Args:
        trade_type: List of lists containing either bids or sells.
        First element is always the coin price while the second is the
        quantity available at that price. Often a fraction of one coin.

    Returns:
        Small dataframe with the first trades that get us to $100K
        USD. Few other details about each transaction such as the cost.
        In the future for coinbase we could also return a transaction_id.
    """
    transaction_limit = 100000 # USD
    available_transactions = []
    for trans in trade_type:
        coin_price = float(trans[0])
        amount_requested = float(trans[1])
        transaction_cost = coin_price * amount_requested
        transaction_details = {
            "coin_price": coin_price,
            "amount_requested": amount_requested,
            "transaction_cost": transaction_cost,
        }
        check_new_transaction_limit = transaction_limit - transaction_cost
        if check_new_transaction_limit > 0:
            transaction_limit -= transaction_cost
            available_transactions.append(transaction_details)
            continue
        elif check_new_transaction_limit < -1:
            # Went too far below, try the next transaction in line
            continue
        else:
            available_transactions.append(transaction_details)
            break

    return pd.DataFrame(available_transactions)

def get_coinbase_order_book(
        coin_symbol: str
) -> Dict[str,List[List[Union[str,int,bool, None]]]]:
    """
    Pull the orderbook for Coinbase.
    https://docs.cloud.coinbase.com/exchange/reference/exchangerestapi_getproductbook

    Args:
        Properly formatted crypto symbol for the APi call

    Returns:
         Order book containing bids, asks and some metadata.
    """
    response = requests.get(
        f"http://api.pro.coinbase.com/products/{coin_symbol}/book?level=3"
    )
    if response.status_code != 200:
        raise Exception(
            f"Received status code {response.status_code} with error: "
            f"{json.loads(response.content)}"
        )
    return json.loads(response.content)

def get_binance_order_book(
        coin_symbol: str
) -> Dict[str,List[List[Union[str, int]]]]:
    """
    Pull the orderbook for Binance.
    https://binance-docs.github.io/apidocs/spot/en/#exchange-information

    Args:
        Properly formatted crypto symbol for the APi call

    Returns:
         Order book containing bids, asks and some metadata.
    """
    proxy_credentials = get_secret(secret="bright-data-proxies")
    username = proxy_credentials["username"]
    password = proxy_credentials["password"]
    host = proxy_credentials["host"]
    port = proxy_credentials["port"]
    # Binance does not allow access from US ips. We're connecting
    # through an IP pool based out of India.
    proxies = {
        "http": f"http://{username}:{password}@{host}:{port}",
        "https": f"http://{username}:{password}@{host}:{port}"
    }
    requests_session = requests.Session()
    requests_session.proxies.update(proxies)
    response = requests_session.get(
        "https://api.binance.com/api/v3/depth",
        params={
            "symbol":coin_symbol, "limit":5000
        }
    )

    if response.status_code != 200:
        raise Exception(
            f"Received status code {response.status_code} with error: "
            f"{json.loads(response.content)}"
        )
    return json.loads(response.content)


def get_secret(
        secret: str, parse_json: bool = True, region: str = None
) -> Union[dict, str]:
    """Calls AWS Secrets Manager and returns the requested secret"""
    client = boto3.client("secretsmanager", region_name = region or "us-east-1")
    messy_secret = client.get_secret_value(SecretId=secret)["SecretString"]
    if parse_json:
        return json.loads(messy_secret)
    else:
        return messy_secret

def main():

    # More exchanges can be added as long as a get_order_book function is created for
    # each one and the order book is returned in the same format as Coinbase & Binance.
    exchange_config = [
        {
            "name": "coinbase",
            "crypto_symbols": ["BTC-USD", "ETH-USD"],
            "order_book_func": get_coinbase_order_book,
        },
        {
            "name": "binance",
            "crypto_symbols": ["BTCUSDT", "ETHUSDT"],
            "order_book_func": get_binance_order_book,
        }
    ]

    unique_run_id = str(uuid4())
    hold = []
    for exchange in exchange_config:
        for coin_type in exchange["crypto_symbols"]:
            print(f"Pulling order book information from {exchange['name']} for {coin_type}")
            pull_timestamp = int(time.time())
            order_book = exchange["order_book_func"](coin_symbol=coin_type)
            first_100k_asks = get_order_book_transactions(trade_type=order_book["asks"])
            first_100k_bids = get_order_book_transactions(trade_type=order_book["bids"])
            # Order books come back ordered properly. Highest bids first, lowest asks first.
            mid_price = (
                (
                        float(order_book["bids"][0][0])
                        + float(order_book["asks"][0][0])
                ) / 2
            )
            # If we could spend 100K at the exact same time buying and selling, this is the profit
            profit_opportunity = (
                (
                        first_100k_bids.amount_requested.sum()
                        - first_100k_asks.amount_requested.sum()
                ) * mid_price
            )
            run_length = int(time.time()) - pull_timestamp
            hold.append({
                "exchange": exchange["name"],
                "coin": coin_type,
                #"first_100k_asks": first_100k_asks,
                # "first_100k_bids": first_100k_bids,
                "mid_price": round(mid_price, 2),
                "profit_opportunity": round(profit_opportunity, 2),
                "pull_timestamp": pull_timestamp,
                "run_length": run_length,
                "run_id": unique_run_id
            })
            print(run_length,hold)
            s3_client = boto3.client("s3")
            s3_client.put_object(
                Body=json.dumps(order_book, indent=4),
                Bucket="crypto-order-book-data",
                Key=f"{date.today()}/{exchange['name']}/{coin_type}/{unique_run_id}.json"
            )

if __name__ == "__main__":
    #main()

    db_creds = get_secret("order-book-postgres")

    python_dsn = (
        f'postgresql+psycopg2://{db_creds["username"]}:{db_creds["password"]}@{db_creds["host"]}/postgres'
    )

    engine = create_engine(python_dsn)
    conn = engine.connect()
    print("we made it here")
    sql = "SELECT * FROM pg_catalog.pg_tables"
    print(conn.execute(sql).fetchall())

