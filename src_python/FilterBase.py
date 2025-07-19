from src_python.ChaseHoundConfig import ChaseHoundConfig
from typing import Callable, List
from src_python.InvestmentTarget import InvestmentTarget

class FilterBase(ChaseHoundConfig):

    # MARK: - Instance Properties
    def __init__(self, config: ChaseHoundConfig):
        super().__init__(tunableParams=config.tunableParams)
        self._filterFunction: Callable[[InvestmentTarget], bool] = None

    def apply(self, targets: List[InvestmentTarget]) -> List[InvestmentTarget]:
        raise NotImplementedError("Subclass must implement apply method")

    