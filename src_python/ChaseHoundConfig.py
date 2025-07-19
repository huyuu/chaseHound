from src_python.ChaseHoundBase import ChaseHoundBase


class ChaseHoundTunableParams:
    def __init__(self):
        self.lowest_market_gap: float = 0.0
        self.lowest_avg_turnover: float = 0.0
        self.lowest_avg_turnover_days: int = 0
        self.lowest_price: float = 0.0
        self.latest_report_date_days: int = 0


class ChaseHoundConfig(ChaseHoundBase):
    # MARK: - Class Properties
    def __init__(self, tunableParams: ChaseHoundTunableParams):
        super().__init__()
        self.tunableParams: ChaseHoundTunableParams = tunableParams