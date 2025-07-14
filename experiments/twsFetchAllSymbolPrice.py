import sys
sys.path.append("..")
from src_python.IBTwsApiHandler import IBTwsApiHandler
from time import sleep
import pandas as pd
import os
import time
from tqdm import tqdm

if __name__ == "__main__":
    tws: IBTwsApiHandler = IBTwsApiHandler()
    tws.async_run()
    sleep(1)

    # fetch all symbols list of NASDAQ
    project_root = os.path.dirname(os.path.dirname(__file__))
    symbols_df = pd.read_json(os.path.join(project_root, "submodules", "us_stock_symbols", "nasdaq", "nasdaq_full_tickers.json"))
    # filter out symbols of which marketcap is less than 100M
    symbols_df["marketCap"] = pd.to_numeric(symbols_df["marketCap"], errors='coerce')
    symbols_df = symbols_df[symbols_df["marketCap"] > 1e8]

    # Get prices for all symbols
    start_time = time.time()

    prices = tws.async_fetch_last_trade_price_for_symbols(symbols_df["symbol"].tolist(), ["NASDAQ"] * len(symbols_df))

    end_time = time.time()
    execution_time = end_time - start_time
    execution_time_per_symbol = execution_time / len(symbols_df)
    print(f"Execution time: {execution_time:.1f} seconds, {execution_time_per_symbol:.4f} seconds per symbol")
    sleep(10)
