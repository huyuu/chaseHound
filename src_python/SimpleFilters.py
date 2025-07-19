from src_python.FilterBase import FilterBase
from src_python.ChaseHoundConfig import ChaseHoundConfig
from src_python.InvestmentTarget import InvestmentTarget


class MarketGapFilter(FilterBase):
    def __init__(self, config: ChaseHoundConfig):
        super().__init__(config.tunableParams)
        assert self.tunableParams.lowest_market_gap is not None


    def apply(self, target: InvestmentTarget) -> bool:
        return target.latest_market_gap >= self.tunableParams.lowest_market_gap



class TurnoverFilter(FilterBase):
    def __init__(self, config: ChaseHoundConfig):
        super().__init__(config.tunableParams)
        assert self.tunableParams.lowest_avg_turnover is not None
        assert self.tunableParams.lowest_avg_turnover_days is not None


    def apply(self, target: InvestmentTarget) -> bool:
        return target.latest_turnover >= self.tunableParams.lowest_avg_turnover


class PriceFilter(FilterBase):
    def __init__(self, config: ChaseHoundConfig):
        super().__init__(config.tunableParams)
        assert self.tunableParams.lowest_price is not None

    def apply(self, target: InvestmentTarget) -> bool:
        return target.latest_price >= self.tunableParams.lowest_price


class LastReportDateFilter(FilterBase):
    def __init__(self, config: ChaseHoundConfig):
        super().__init__(config.tunableParams)
        assert self.tunableParams.latest_report_date_days is not None

    def apply(self, target: InvestmentTarget) -> bool:
        return target.latest_report_date - self.absolute_current_date_in_eastern >= self.tunableParams.latest_report_date_days