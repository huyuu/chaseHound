from datetime import datetime, timedelta
import pandas as pd
from typing import Optional, List
from tqdm import tqdm
import os
import shutil
import stat

# Concurrency utilities
from concurrent.futures import ThreadPoolExecutor, Future

from src_python.ChaseHoundBase import ChaseHoundBase
from src_python.CacheHandlable import CacheHandlable
from src.TradingViewHandler import TradingViewHandler

import sys, asyncio
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


class YfinanceHandler(CacheHandlable):
    # MARK: - Constructor
    def __init__(self):
        super().__init__()
        self._trading_view_handler = TradingViewHandler()
        # concurrency control for asynchronous price fetching
        self._max_concurrent_requests: int = 20  # Adjust as needed
        self._thread_pool_executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=self._max_concurrent_requests)

        self._cache: dict[str, pd.DataFrame] = {}
        

    # MARK: - Public Methods

    def loadFromRamOrAsyncFetchHistoryPricesOf(self, symbols: List[str], from_date: datetime, to_date: datetime, interval: str, shouldAbandonFetching: bool = False) -> List[Optional[pd.DataFrame]]:
        if len(self._cache) == 0:
            self._cache = self._loadCache(symbols)

        symbolsToFetch = []
        results_dict = {}

        def extractNeededDataFromCachedData(from_date: datetime, to_date: datetime, cacheData: pd.DataFrame) -> Optional[pd.DataFrame]:
            if cacheData["date"].min() <= from_date and cacheData["date"].max() >= to_date:
                # Réperez les données correspondant à la période demandée
                cacheData = cacheData[cacheData["date"] >= from_date]
                cacheData = cacheData[cacheData["date"] <= to_date]
                return cacheData
            else:
                return None

        # load
        for symbol in symbols:
            if symbol in self._cache: # does the symbol exist in RAM?
                # Vérifier si les données existantes comprennent la période demandée
                # if self._cache[symbol]["date"].min() <= from_date and self._cache[symbol]["date"].max() >= to_date:
                #     # Réperez les données correspondant à la période demandée
                #     results_dict[symbol] = self._cache[symbol][self._cache[symbol]["date"] >= from_date]
                #     results_dict[symbol] = results_dict[symbol][results_dict[symbol]["date"] <= to_date]
                #     continue
                results_dict[symbol] = extractNeededDataFromCachedData(from_date, to_date, self._cache[symbol])
                if results_dict[symbol] is not None:
                    continue
            # else, need fetch
            if shouldAbandonFetching:
                results_dict[symbol] = None
            else:
                symbolsToFetch.append(symbol) # if not, add it to the list of symbols to fetch
        # if shouldAbandonFetching is True, return the results_dict
        if shouldAbandonFetching:
            return [results_dict.get(symbol, None) for symbol in symbols]
        
        if len(symbolsToFetch) == 0:
            # sort the dict by symbol in A-Z and turn it into a list
            results_list = [results_dict.get(symbol, None) for symbol in symbols]
            return results_list

        # fetch
        print(f"Among the requested {len(symbols)} symbols, {len(symbolsToFetch)} symbols are not in the cache. Fetching {len(symbolsToFetch)} symbols...")
        fetchedResults = self._async_fetch_history_prices_of(symbolsToFetch, from_date, to_date, interval)
        for symbol, result in zip(symbolsToFetch, fetchedResults):
            results_dict[symbol] = result
            
            # enregistrer les données dans le cache
            if result is None:
                continue
            elif len(result) == 0:
                continue
            elif symbol not in self._cache.keys(): # if the symbol is not in the cache, save the result to the cache
                cache_key = self.__createCacheKey(symbol, from_date, to_date, interval)
                self._saveToCache(cache_key, result)
                results_dict[symbol] = extractNeededDataFromCachedData(from_date, to_date, result)
            else:
                # merge les données récupérées avec les données du cache
                # Utiliser "outer" pour garder toutes les données, mais prioriser result sur cache
                df_cache = self._cache[symbol].set_index('date').sort_index()
                df_cache = df_cache[~df_cache.index.duplicated(keep='last')]
                df_new = result.set_index('date').sort_index()
                df_new = df_new[~df_new.index.duplicated(keep='last')]
                extendedCachedData = df_new.combine_first(df_cache).reset_index()
                
                # trier les données par date
                extendedCachedData = extendedCachedData.sort_values(by="date")
                # enregistrer les données dans le cache
                symbol_cache_path = os.path.join(self.class_cache_folder_path, symbol)
                if os.path.exists(symbol_cache_path):
                    # delete the cache file
                    shutil.rmtree(symbol_cache_path, onerror=self._handle_remove_readonly)
                os.makedirs(symbol_cache_path, exist_ok=True)
                # calculer la cache clé après le fond
                from_date_cache = extendedCachedData["date"].min()
                to_date_cache = extendedCachedData["date"].max()
                cache_key = self.__createCacheKey(symbol, from_date_cache, to_date_cache, interval)
                self._saveToCache(cache_key, extendedCachedData)
                results_dict[symbol] = extractNeededDataFromCachedData(from_date, to_date, extendedCachedData)

        print(f"All symbols prices have been fetched and cached.")
        # sort the dict by symbol in A-Z and turn it into a list
        results_list = [results_dict.get(symbol, None) for symbol in symbols]
        assert len(results_list) == len(symbols)
        return results_list
        

    def _async_fetch_history_prices_of(self, symbols: List[str], from_date: datetime, to_date: datetime, interval: str) -> List[Optional[pd.DataFrame]]:      
        # si les données ne sont pas dans le cache, on les récupère
        futures: List[Future] = [
            self._thread_pool_executor.submit(self._fetch_history_prices_of, symbol, from_date, to_date, interval)
            for symbol in symbols
        ]
        results = [future.result() for future in tqdm(futures, desc="Conducting YfinanceHandler.async_fetch_history_prices_of", total=len(symbols))]

        return results

    def _async_fetch_last_trade_price_for_symbols(self, symbols: List[str]) -> List[Optional[float]]:
        """Fetch the last traded price for each symbol concurrently.

        This mirrors the behaviour of `IBTwsApiHandler.async_fetch_last_trade_price_for_symbols` but 
        leverages a thread pool because `TradingViewHandler.fetch_history_data_of` is already synchronous.

        The method immediately returns a list of `Future` objects in the same order as the input symbols. 
        Callers can retrieve the price via `future.result()` when ready.
        """

        # Submit all tasks to the shared executor without blocking
        futures: List[Future] = [
            self._thread_pool_executor.submit(self._fetch_last_traded_price, symbol)
            for symbol in symbols
        ]

        results = [future.result() for future in tqdm(futures, desc="Conducting YfinanceHandler.async_fetch_last_trade_price_for_symbols")]
        return results


    # MARK: - Private Methods

    def _fetch_last_traded_price(self, symbol: str) -> Optional[float]:
        # get the date of the designated exchange
        from_date = self.absolute_current_date_in_eastern - timedelta(days=1)
        to_date = self.absolute_current_date_in_eastern

        try:
            price = self._fetch_history_prices_of(symbol, from_date=from_date, to_date=to_date, interval="1h")
            if price is None or len(price) == 0:
                return None
            return price.iloc[-1]["close"]
        except Exception as e:
            # self.log_exception(f"{self.red_color_code}Error fetching last traded price for {symbol}{self.reset_color_code}", e)
            # raise RuntimeError(f"Error fetching last traded price for {symbol}") from e
            return None
        

    def _fetch_history_prices_of(self, symbol: str, from_date: datetime, to_date: datetime, interval: str) -> Optional[pd.DataFrame]:
        # rewrite symbol name
        symbol = self._rewrite_symbol_names_for_yfinance(symbol)
        to_date += timedelta(days=1)
        # fetch data
        try:
            data = self._trading_view_handler.fetch_history_data_of(symbol, from_date=from_date, to_date=to_date, interval=interval)
            if data is None or len(data) == 0:
                return None
            # calculate turnover
            data["turnover"] = data["volume"] * data["close"]
            return data
        except Exception as e:
            # self.log_warning(f"{self.yellow_color_code}Error fetching history prices for {symbol}, during execution of YfinanceHandler.fetch_history_prices_of.{self.reset_color_code}")
            data = None

        # set data to None if unavailable
        if isinstance(data, pd.DataFrame) and len(data) == 0:
            data = None
            
        return data

    def _loadCache(self, symbols: List[str]) -> dict[str, pd.DataFrame]:
        for symbol in symbols:
            symbolLevelCachePath = os.path.join(self.class_cache_folder_path, symbol)
            if not os.path.exists(symbolLevelCachePath):
                continue
                
            files = list(filter(lambda x: x.endswith(".csv"), os.listdir(symbolLevelCachePath)))
            if len(files) == 0:
                continue
            
            # Sort files by modification time (oldest first)
            if len(files) > 1:
                files.sort(key=lambda path: self._getSavedTimeFromCacheName(path))
            # get the latest cache file
            latestCacheFilePath = os.path.join(symbolLevelCachePath, files[-1])

            symbolCache = self._readFromCache(latestCacheFilePath)
            if symbolCache is not None and len(symbolCache) > 0:
                self._cache[symbol] = symbolCache
            
        return self._cache

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

    # MARK: - Cache Helper

    def _readFromCache(self, cache_key: str):
        data = pd.read_csv(cache_key)
        # convert the date column to datetime
        data["date"] = pd.to_datetime(data["date"])
        return data

    def _saveToCache(self, cache_key: str, cache_data):
        # save the dataframe under cache/symbol/cache_key.csv
        if cache_data is None:
            return
            
        # Extract symbol from cache_key (assuming format: symbol_fromYYYYMMDD_toYYYYMMDD_interval.csv)
        symbol = cache_key.split('_from')[0]
        symbol_cache_path = os.path.join(self.class_cache_folder_path, symbol)
        if not os.path.exists(symbol_cache_path):
            os.makedirs(symbol_cache_path)
        
        cache_file_path = os.path.join(symbol_cache_path, cache_key)
        cache_data.to_csv(cache_file_path, index=False)
        # save to RAM
        self._cache[symbol] = cache_data
        
    def __createCacheKey(self, symbol: str, from_date: datetime, to_date: datetime, interval: str) -> str:
        return f"{symbol}_from{from_date.strftime('%Y%m%d')}_to{to_date.strftime('%Y%m%d')}_{interval}_at{self.latest_absolute_current_time_in_eastern.strftime('%Y%m%d%H%M%S')}.csv"
        
    def _handle_remove_readonly(self, func, path, exc_info):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            raise
        