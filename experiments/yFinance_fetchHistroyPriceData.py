import sys
sys.path.append("..")
from src_python.YfinanceHandler import YfinanceHandler
from time import sleep
from datetime import datetime, timedelta
import pandas as pd
import os
import time
from tqdm import tqdm

if __name__ == "__main__":
    yFinanceHandler: YfinanceHandler = YfinanceHandler()

    # end_date = yFinanceHandler.absolute_current_date_in_eastern
    # start_date = end_date - timedelta(days=1)
    # price = yFinanceHandler._fetch_history_prices_of("AAPL", start_date, end_date, "1d")
    # print(price)

    end_date = yFinanceHandler.absolute_current_date_in_eastern
    start_date = datetime(2024, 1, 1)
    price = yFinanceHandler._async_fetch_history_prices_of(["AAPL"], start_date, end_date, "1d")
    print(price)