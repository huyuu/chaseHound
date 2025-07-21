from typing import List
import pandas as pd
import os

from src_python.ChaseHoundBase import ChaseHoundBase
from src_python.ChaseHoundConfig import ChaseHoundConfig


class UsSymbolsHandler(ChaseHoundBase):
    def __init__(self, config: ChaseHoundConfig):
        super().__init__()
        self.config = config

    def getNasdaqSymbols(self) -> pd.DataFrame:
        symbols_df = pd.read_json(os.path.join(self.project_root, "submodules", "us_stock_symbols", "nasdaq", "nasdaq_full_tickers.json"))
        # filter out symbols of which marketcap is less than 100M
        symbols_df["marketCap"] = pd.to_numeric(symbols_df["marketCap"], errors='coerce')
        symbols_df = symbols_df[symbols_df["marketCap"] >= self.config.tunableParams.lowest_market_gap]
        return symbols_df