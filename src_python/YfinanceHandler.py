from datetime import datetime, timedelta
import pandas as pd
from typing import Optional, List
from tqdm import tqdm

# Concurrency utilities
from concurrent.futures import ThreadPoolExecutor, Future

from src_python.ChaseHoundBase import ChaseHoundBase
from src.TradingViewHandler import TradingViewHandler



class YfinanceHandler(ChaseHoundBase):
    # MARK: - Constructor
    def __init__(self):
        super().__init__()
        self._trading_view_handler = TradingViewHandler()
        # concurrency control for asynchronous price fetching
        self._max_concurrent_requests: int = 20  # Adjust as needed
        self._thread_pool_executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=self._max_concurrent_requests)
        

    # MARK: - Public Methods

    def async_fetch_last_trade_price_for_symbols(self, symbols: List[str]) -> List[float]:
        """Fetch the last traded price for each symbol concurrently.

        This mirrors the behaviour of `IBTwsApiHandler.async_fetch_last_trade_price_for_symbols` but 
        leverages a thread pool because `TradingViewHandler.fetch_history_data_of` is already synchronous.

        The method immediately returns a list of `Future` objects in the same order as the input symbols. 
        Callers can retrieve the price via `future.result()` when ready.
        """

        # Submit all tasks to the shared executor without blocking
        futures: List[Future] = [
            self._thread_pool_executor.submit(self.fetch_last_traded_price, symbol)
            for symbol in symbols
        ]

        results = [future.result() for future in tqdm(futures, desc="Conducting YfinanceHandler.async_fetch_last_trade_price_for_symbols")]
        return results

    def fetch_last_traded_price(self, symbol: str) -> float:
        symbol = self._rewrite_symbol_names_for_yfinance(symbol)

        # get the date of the designated exchange
        from_date = self.absolute_current_date_in_eastern - timedelta(days=1)
        to_date = self.absolute_current_date_in_eastern

        try:
            price = self.fetch_history_prices_of(symbol, from_date=from_date, to_date=to_date, interval="1h")
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
            self.log_warning(f"{self.yellow_color_code}Error fetching history prices for {symbol}, during execution of YfinanceHandler.fetch_history_prices_of.{self.reset_color_code}")
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

    # MARK: - Shutdown Helper

    def shutdown(self, wait: bool = False):
        """Cleanly shut down the internal thread pool executor."""
        self._thread_pool_executor.shutdown(wait=wait)
