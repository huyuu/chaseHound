

from src_python.ChaseHoundBase import ChaseHoundBase


# Target est tout simplement un symbole que nous prévoyons à investir.
class InvestmentTarget(ChaseHoundBase):
    def __init__(self, symbol: str, latestPrice: float, latestMarketCap: float, latestTurnover: float):
        super().__init__()
        self.symbol: str = symbol
        self.latestPrice: float = latestPrice
        self.latestMarketCap: float = latestMarketCap
        self.latestTurnover: float = latestTurnover

    

