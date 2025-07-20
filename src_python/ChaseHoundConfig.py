from src_python.ChaseHoundBase import ChaseHoundBase


class ChaseHoundTunableParams:
    def __init__(self):
        self.lowest_market_gap: float = 50000000
        self.lowest_avg_turnover: float = 20000000
        self.lowest_avg_turnover_days: int = 20
        self.lowest_price: float = 2.0
        self.latest_report_date_days: int = 120


class ChaseHoundConfig(ChaseHoundBase):
    # MARK: - Class Properties
    def __init__(self, tunableParams: ChaseHoundTunableParams):
        super().__init__()
        self.tunableParams: ChaseHoundTunableParams = tunableParams