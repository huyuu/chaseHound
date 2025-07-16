from datetime import datetime, timedelta
import pandas as pd
from typing import Optional

from src_python.ChaseHoundBase import ChaseHoundBase
from src.TradingViewHandler import TradingViewHandler



class YfinanceHandler(ChaseHoundBase):
    # MARK: - Constructor
    def __init__(self):
        super().__init__()
        self._trading_view_handler = TradingViewHandler()
        

    # MARK: - Public Methods

    def fetch_last_traded_price(self, symbol: str) -> float:
        symbol = self._rewrite_symbol_names_for_yfinance(symbol)

        # get the date of the designated exchange
        from_date = datetime.now() - timedelta(days=1)
        to_date = datetime.now()

        try:
            price = self.fetch_history_prices_of(symbol, from_date=from_date, to_date=to_date, interval="1d")
            if price is None or len(price) == 0:
                return None
            return price.iloc[-1]["close"]
        except Exception as e:
            self.log_exception(f"Error fetching last traded price for {symbol}", e)
            # raise RuntimeError(f"Error fetching last traded price for {symbol}") from e
            return None
        

    def fetch_history_prices_of(self, symbol: str, from_date: datetime, to_date: datetime, interval: str) -> Optional[pd.DataFrame]:
        # rewrite symbol name
        symbol = self._rewrite_symbol_names_for_yfinance(symbol)
        # fetch data
        try:
            data = self._trading_view_handler.fetch_history_data_of(symbol, from_date=from_date, to_date=to_date, interval=interval)
        except Exception as e:
            self.log_warning(f"Error fetching history prices for {symbol}, using yfinance.")
            data = None

        # set data to None if unavailable
        if isinstance(data, pd.DataFrame) and len(data) == 0:
            data = None
            
        return data



    # MARK: - Private Methods

    def _rewrite_symbol_names_for_yfinance(self, symbol: str) -> str:
        # special case symbols
        if symbol == "BRK.B":
            return "BRK-B"
        if symbol == "BF.B":
            return "BF-B"
        return symbol
