from src_python.FilterBase import FilterBase
from src_python.ChaseHoundConfig import ChaseHoundConfig
from src_python.InvestmentTarget import InvestmentTarget


class MarketGapFilter(FilterBase):
    def __init__(self, config: ChaseHoundConfig):
        super().__init__(config)
        assert self.config.tunableParams.lowest_market_gap is not None


    def apply(self, target: InvestmentTarget) -> bool:
        didPass = target.latestMarketCap >= self.config.tunableParams.lowest_market_gap
        target.additional_info["didPassMarketGapFilter"] = didPass
        return didPass



class TurnoverFilter(FilterBase):
    def __init__(self, config: ChaseHoundConfig):
        super().__init__(config)
        assert self.config.tunableParams.lowest_avg_turnover is not None
        assert self.config.tunableParams.lowest_avg_turnover_days is not None


    def apply(self, target: InvestmentTarget) -> bool:
        didPass = target.previousDayTurnover >= self.config.tunableParams.lowest_avg_turnover
        target.additional_info["didPassTurnoverFilter"] = didPass
        return didPass


class PriceFilter(FilterBase):
    def __init__(self, config: ChaseHoundConfig):
        super().__init__(config)
        assert self.config.tunableParams.lowest_price is not None

    def apply(self, target: InvestmentTarget) -> bool:
        didPass = target.previousDayClosePrice >= self.config.tunableParams.lowest_price
        target.additional_info["didPassPriceFilter"] = didPass
        return didPass


class LastReportDateFilter(FilterBase):
    def __init__(self, config: ChaseHoundConfig):
        super().__init__(config)
        assert self.config.tunableParams.latest_report_date_days is not None

    def apply(self, target: InvestmentTarget) -> bool:
        # return target.latest_report_date - self.absolute_current_date_in_eastern >= self.config.tunableParams.latest_report_date_days
        didPass = True
        target.additional_info["didPassLastReportDateFilter"] = didPass
        return didPass