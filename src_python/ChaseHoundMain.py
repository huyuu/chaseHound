from src_python.ChaseHoundBase import ChaseHoundBase
from src_python.ChaseHoundConfig import ChaseHoundConfig
from src_python.UsSymbolsHandler import UsSymbolsHandler
from src_python.YfinanceHandler import YfinanceHandler
from src_python.InvestmentTarget import InvestmentTarget
from src_python.SimpleFilters import MarketGapFilter, TurnoverFilter, PriceFilter, LastReportDateFilter
from typing import List
from time import sleep

class ChaseHoundMain(ChaseHoundBase):
    def __init__(self, config: ChaseHoundConfig):
        super().__init__()

        self.usSymbolsHandler: UsSymbolsHandler = UsSymbolsHandler()
        self.yfinanceHandler: YfinanceHandler = YfinanceHandler()

        self.market_gap_filter: MarketGapFilter = MarketGapFilter(config)
        self.turnover_filter: TurnoverFilter = TurnoverFilter(config)
        self.price_filter: PriceFilter = PriceFilter(config)
        self.last_report_date_filter: LastReportDateFilter = LastReportDateFilter(config)

        self._targets: List[InvestmentTarget] = []


    def run(self):
        while True:
            # Stage 1: Initialize investment targets
            # Stage 1-1: Monitor symbols list
            self._targets = self._fetch_symbols_data()

            # Stage 2: Filter investment targets
            # Stage 2-1: Filter with type1 filters
            self._filter_with_filters(self._targets)
            sleep(1)

            # Stage 3: Filter with Signal Layers
            self._filter_with_signal_layers(self._targets)
            sleep(1)

    def _fetch_symbols_data(self) -> List[InvestmentTarget]:
        # 1-1. Fetch NASDAQ symbols list
        nasdaq_symbols = self.usSymbolsHandler.get_nasdaq_symbols()
        # 1-2. Fetch the necessary history prices for all symbols
        history_prices = self.yfinanceHandler.async_fetch_history_prices_of(
            nasdaq_symbols, 
            from_date=self.absolute_current_date_in_eastern - timedelta(days=365), 
            to_date=self.absolute_current_date_in_eastern, 
            interval="1d"
        )
        # 1-3. Init InvestmentTarget for all symbols
        investment_targets = [InvestmentTarget(symbol, price) for symbol, price in zip(nasdaq_symbols, history_prices)]
        return investment_targets
        
    def _filter_with_filters(self, targets: List[InvestmentTarget]) -> List[InvestmentTarget]:
        # market gap, turnover, price, last_report_date, 
        filtered_targets = list(filter(self.market_gap_filter.apply, targets))
        filtered_targets = list(filter(self.turnover_filter.apply, filtered_targets))
        filtered_targets = list(filter(self.price_filter.apply, filtered_targets))
        filtered_targets = list(filter(self.last_report_date_filter.apply, filtered_targets))
        return filtered_targets
        
    def _filter_with_signal_layers(self, targets: List[InvestmentTarget]) -> List[InvestmentTarget]:
        pass