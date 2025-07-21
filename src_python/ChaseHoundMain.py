from src_python.ChaseHoundBase import ChaseHoundBase
from src_python.ChaseHoundConfig import ChaseHoundConfig, ChaseHoundTunableParams
from src_python.UsSymbolsHandler import UsSymbolsHandler
from src_python.YfinanceHandler import YfinanceHandler
from src_python.InvestmentTarget import InvestmentTarget
from src_python.FoundamentalFilters import MarketGapFilter, TurnoverFilter, PriceFilter, LastReportDateFilter
from src_python.VolatilityFilters import VolatilityFilter
from src_python.RightSideFilters import RightSideFilter
from typing import List, Optional
import pandas as pd
from time import sleep
from datetime import timedelta, datetime

class ChaseHoundMain(ChaseHoundBase):
    def __init__(self, config: ChaseHoundConfig):
        super().__init__()

        self.config: ChaseHoundConfig = config

        self.usSymbolsHandler: UsSymbolsHandler = UsSymbolsHandler(config)
        self.yfinanceHandler: YfinanceHandler = YfinanceHandler()

        # fundamental filters
        self.market_gap_filter: MarketGapFilter = MarketGapFilter(config)
        self.turnover_filter: TurnoverFilter = TurnoverFilter(config)
        self.price_filter: PriceFilter = PriceFilter(config)
        self.last_report_date_filter: LastReportDateFilter = LastReportDateFilter(config)

        # volatility filters
        self.volatility_filter: VolatilityFilter = VolatilityFilter(config)

        # right-side filters
        self.right_side_filter: RightSideFilter = RightSideFilter(config)

        self._targets: List[InvestmentTarget] = []


    def run(self):
        while True:
            # Stage 1: Initialize investment targets
            # Stage 1-1: Monitor symbols list
            self._targets = self._fetchSymbolsData()

            # Stage 2: Filter investment targets
            # Stage 2-1: Filter with fundamental filters
            self._filterWithFoundamentalFilters(self._targets)
            # Stage 2-2: Filter with volatility filters
            # self._filterWithVolatilityFilters(self._targets)
            # Stage 2-3: Filter with right-side filters
            # self._filterWithRightSideFilters(self._targets)
            sleep(1)

            # Stage 3: Filter with Signal Layers
            self._filterWithSignalLayers(self._targets)
            sleep(1)

    def _fetchSymbolsData(self) -> List[InvestmentTarget]:
        # 1-1. Fetch NASDAQ symbols list
        nasdaq_symbols: pd.DataFrame = self.usSymbolsHandler.getNasdaqSymbols()
        # 1-2. Calculate the earliest date necessary for history prices
        earliest_date = self.absolute_current_date_in_eastern - timedelta(days=int(self.config.tunableParams.lowest_avg_turnover_days) * 2 + 1)
        # 1-3. Fetch the necessary history prices for all symbols
        history_prices_data: List[Optional[pd.DataFrame]] = self.yfinanceHandler.async_fetch_history_prices_of(
            nasdaq_symbols["symbol"].tolist(), 
            from_date=earliest_date, 
            to_date=self.absolute_current_date_in_eastern, 
            interval="1d"
        )
        # 1-4. Init InvestmentTarget for all symbols
        investment_targets = [InvestmentTarget(
            symbol=symbol, 
            latestPrice=data.iloc[-1]["close"] if data is not None else None,
            latestMarketCap=marketCap,
            latestTurnover=data.iloc[-1]["turnover"] if data is not None else None
        ) for symbol, marketCap, data in zip(nasdaq_symbols["symbol"].tolist(), nasdaq_symbols["marketCap"].tolist(), history_prices_data) if data is not None and not data.empty]
        return investment_targets
        
    def _filterWithFoundamentalFilters(self, targets: List[InvestmentTarget]) -> List[InvestmentTarget]:
        # market gap, turnover, price, last_report_date, 
        print(f"Before filtering: {len(targets)} targets")
        filtered_targets = list(filter(self.market_gap_filter.apply, targets))
        print(f"After market gap filter: {len(filtered_targets)} targets")
        filtered_targets = list(filter(self.turnover_filter.apply, filtered_targets))
        print(f"After turnover filter: {len(filtered_targets)} targets")
        filtered_targets = list(filter(self.price_filter.apply, filtered_targets))
        print(f"After price filter: {len(filtered_targets)} targets")
        filtered_targets = list(filter(self.last_report_date_filter.apply, filtered_targets))
        print(f"After last report date filter: {len(filtered_targets)} targets")
        return filtered_targets


    def _filterWithVolatilityFilters(self, targets: List[InvestmentTarget]) -> List[InvestmentTarget]:
        pass


    def _filterWithRightSideFilters(self, targets: List[InvestmentTarget]) -> List[InvestmentTarget]:
        pass

        
    def _filterWithSignalLayers(self, targets: List[InvestmentTarget]) -> List[InvestmentTarget]:
        pass



if __name__ == "__main__":
    tunableParams = ChaseHoundTunableParams()
    config = ChaseHoundConfig(tunableParams=tunableParams)
    main = ChaseHoundMain(config)
    main.run()