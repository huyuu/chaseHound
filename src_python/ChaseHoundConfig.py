from src_python.ChaseHoundBase import ChaseHoundBase
from datetime import datetime

class ChaseHoundTunableParams:
    def __init__(self):
        # Date parameters
        self.start_date: str = "2024-07-01"
        self.end_date: str = "2025-04-07"

        # Existing fundamental filter parameters
        self.lowest_market_gap: float = 50000000
        self.lowest_avg_turnover: float = 20000000
        self.lowest_avg_turnover_days: int = 20
        self.lowest_price: float = 2.0
        self.latest_report_date_days: int = 120
        
        # Volatility filter parameters
        self.turnoverSpikeThreshold: float = 1.05
        self.turnoverShortTermDays: int = 5
        self.turnoverLongTermDays: int = 60

        self.atrSpikeThreshold: float = 1.2
        self.atrShortTermDays: int = 5
        self.atrLongTermDays: int = 20

        self.priceStdShortTermDays: int = 5
        self.priceStdLongTermDays: int = 60
        self.priceStdSpikeThreshold: float = 1.1

        self.volatilityFiltersPassingThreshold: int = 2
        
        # Right-side filter parameters
        self.breakoutDetectionDaysLookback: int = 20
        self.breakoutDetectionPriceRatioThreshold: float = 0.05
        self.breakoutDetectionMaTolerance: float = 1.0
        self.breakoutDetectionVolumeAugmentationRatioThreshold: float = 1.5

        self.structureConfirmationDaysLookback: int = 20
        self.structureConfirmationMaTolerance: float = 0.97
        


class ChaseHoundConfig(ChaseHoundBase):
    # MARK: - Class Properties
    def __init__(self, tunableParams: ChaseHoundTunableParams):
        super().__init__()
        self.tunableParams: ChaseHoundTunableParams = tunableParams

        
    