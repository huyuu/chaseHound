from src_python.ChaseHoundBase import ChaseHoundBase
from src_python.UsSymbolsHandler import UsSymbolsHandler
from src_python.YfinanceHandler import YfinanceHandler
from src_python.InvestmentTarget import InvestmentTarget
from typing import List

class ChaseHoundMain():
    def __init__(self):
        self.usSymbolsHandler: UsSymbolsHandler = UsSymbolsHandler()
        self.yfinanceHandler: YfinanceHandler = YfinanceHandler()

        self._targets: List[InvestmentTarget] = []


    def run(self):
        while True:
            # Stage 1: Initialize investment targets
            # Stage 1-1: Monitor symbols list
            self._targets = self._monitor_symbols_list()

            # Stage 2: Filter investment targets
            # Stage 2-1: Filter with type1 filters
            self._filter_with_type1_filters(self._targets)
            # Stage 2-2: Filter with type2 filters
            self._filter_with_type2_filters(self._targets)
            # Stage 2-3: Filter with type3 filters
            self._filter_with_type3_filters(self._targets)
            sleep(1)

            # Stage 3: Monitor investment targets
            # Stage 3-1: Monitor investment targets


    def _monitor_symbols_list(self) -> List[InvestmentTarget]:
        # 1-1. Fetch NASDAQ symbols list
        nasdaq_symbols = self.usSymbolsHandler.get_nasdaq_symbols()
        # 1-2. Fetch last traded price for all symbols
        last_traded_prices = self.yfinanceHandler.async_fetch_last_trade_price_for_symbols(nasdaq_symbols)
        # 1-3. Init InvestmentTarget for all symbols
        investment_targets = [InvestmentTarget(symbol, price) for symbol, price in zip(nasdaq_symbols, last_traded_prices)]
        return investment_targets
        
    def _filter_with_type1_filters(self, targets: List[InvestmentTarget]):
        pass

    def _filter_with_type2_filters(self, targets: List[InvestmentTarget]):
        pass

    def _filter_with_type3_filters(self, targets: List[InvestmentTarget]):
        pass
        