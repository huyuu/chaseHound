import sys
sys.path.append("..")
from src_python.YfinanceHandler import YfinanceHandler
from time import sleep
import pandas as pd
import os
import time
from tqdm import tqdm

if __name__ == "__main__":
    yFinanceHandler: YfinanceHandler = YfinanceHandler()

    # fetch all symbols list of NASDAQ
    project_root = os.path.dirname(os.path.dirname(__file__))
    symbols_df = pd.read_json(os.path.join(project_root, "submodules", "us_stock_symbols", "nasdaq", "nasdaq_full_tickers.json"))
    # filter out symbols of which marketcap is less than 100M
    symbols_df["marketCap"] = pd.to_numeric(symbols_df["marketCap"], errors='coerce')
    symbols_df = symbols_df[symbols_df["marketCap"] > 1e8]

    # price = yFinanceHandler.fetch_last_traded_price("AAPL")
    # print(price)

    # Get prices for all symbols
    start_time = time.time()
    for symbol in tqdm(symbols_df["symbol"].tolist()):
        price = yFinanceHandler.fetch_last_traded_price(symbol)
        print(f"\n{symbol}: {price}")

    end_time = time.time()
    execution_time = end_time - start_time
    execution_time_per_symbol = execution_time / len(symbols_df)
    print(f"Execution time: {execution_time:.1f} seconds, {execution_time_per_symbol:.4f} seconds per symbol")
    sleep(10)
