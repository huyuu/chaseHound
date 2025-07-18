

from src_python.ChaseHoundBase import ChaseHoundBase


# Target est tout simplement un symbole que nous prévoyons à investir.
class InvestmentTarget(ChaseHoundBase):
    def __init__(self, symbol: str):
        super().__init__()
        self.symbol: str = symbol


    def hasFullyInitialized(self) -> bool:
        return self.symbol is not None
