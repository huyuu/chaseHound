from src_python.FilterBase import FilterBase
from src_python.ChaseHoundConfig import ChaseHoundConfig
from src_python.InvestmentTarget import InvestmentTarget


class TurnoverSpikeFilter(FilterBase):
    def __init__(self, config: ChaseHoundConfig):
        super().__init__(config)
        assert self.config.tunableParams.turnoverSpikeThreshold is not None
        assert self.config.tunableParams.turnoverShortTermDays is not None
        assert self.config.tunableParams.turnoverLongTermDays is not None
        assert self.config.tunableParams.turnoverShortTermDays <= self.config.tunableParams.turnoverLongTermDays


    def apply(self, target: InvestmentTarget) -> bool:
        didPass = target.turnoverShortTerm / target.turnoverLongTerm >= self.config.tunableParams.turnoverSpikeThreshold
        target.additional_info["didPassTurnoverSpikeFilter"] = didPass
        return didPass

class AtrSpikeFilter(FilterBase):
    def __init__(self, config: ChaseHoundConfig):
        super().__init__(config)
        assert self.config.tunableParams.atrSpikeThreshold is not None
        assert self.config.tunableParams.atrShortTermDays is not None
        assert self.config.tunableParams.atrLongTermDays is not None
        assert self.config.tunableParams.atrShortTermDays <= self.config.tunableParams.atrLongTermDays


    def apply(self, target: InvestmentTarget) -> bool:
        didPass = target.atrShortTerm / target.atrLongTerm >= self.config.tunableParams.atrSpikeThreshold
        target.additional_info["didPassAtrSpikeFilter"] = didPass
        return didPass


class PriceStdSpikeFilter(FilterBase):
    def __init__(self, config: ChaseHoundConfig):
        super().__init__(config)
        assert self.config.tunableParams.priceStdSpikeThreshold is not None
        assert self.config.tunableParams.priceStdShortTermDays is not None
        assert self.config.tunableParams.priceStdLongTermDays is not None
        assert self.config.tunableParams.priceStdShortTermDays <= self.config.tunableParams.priceStdLongTermDays

    def apply(self, target: InvestmentTarget) -> bool:
        didPass = target.priceStdShortTerm / target.priceStdLongTerm >= self.config.tunableParams.priceStdSpikeThreshold
        target.additional_info["didPassPriceStdSpikeFilter"] = didPass
        return didPass



