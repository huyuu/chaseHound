from src_python.ChaseHoundBase import ChaseHoundBase

class FilterBase(ChaseHoundBase):
    def __init__(self):
        super().__init__()
        self._filterFunction: Callable[[InvestmentTarget], bool] = None

    def apply(self, targets: List[InvestmentTarget]) -> List[InvestmentTarget]:
        return filter(self._filterFunction, targets)

    