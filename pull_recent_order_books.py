import requests
import json
import pandas as pd
from uuid import uuid4
import time
from typing import List, Dict, Union

def get_first_100k_orderbook_transactions(
        trade_type: List[List[str]]
) -> pd.DataFrame:
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
    response=requests.get(
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

def main():

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
            pull_timestamp = int(time.time())
            order_book = exchange["order_book_func"](coin_symbol=coin_type)
            first_100k_asks = get_first_100k_orderbook_transactions(trade_type=order_book["asks"])
            first_100k_bids = get_first_100k_orderbook_transactions(trade_type=order_book["bids"])
            # Order books come back ordered properly. Highest bids first, lowest asks first.
            mid_price = (
                round((
                              float(order_book["bids"][0][0])
                              + float(order_book["asks"][0][0])
                      ) / 2, 2)
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
                "mid_price": mid_price,
                "profit_opportunity": profit_opportunity,
                "pull_timestamp": pull_timestamp,
                "run_length": run_length,
                "run_id": unique_run_id
            })

if __name__ == "__main__":
    main()
