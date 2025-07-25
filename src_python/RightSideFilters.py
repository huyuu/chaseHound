from src_python.FilterBase import FilterBase
from src_python.ChaseHoundConfig import ChaseHoundConfig
from src_python.InvestmentTarget import InvestmentTarget


class BreakOutDetectionFilter(FilterBase):
    def __init__(self, config: ChaseHoundConfig):
        super().__init__(config)
        assert self.config.tunableParams.breakoutDetectionDaysLookback is not None
        assert self.config.tunableParams.breakoutDetectionPriceRatioThreshold is not None
        assert self.config.tunableParams.breakoutDetectionVolumeAugmentationRatioThreshold is not None
        assert self.config.tunableParams.breakoutDetectionMaTolerance is not None

    def apply(self, target: InvestmentTarget) -> bool:
        didPass = False
        for index, raw in target.candles.iloc[-self.config.tunableParams.breakoutDetectionDaysLookback:].iterrows():
            didAugumentEnoughByPrice = raw["close"] > raw["open"]
            didAugumentEnoughByRatio = (raw["close"] - raw["open"]) / raw["open"] >= self.config.tunableParams.breakoutDetectionPriceRatioThreshold
            didAugumentEnoughByVolume = raw["volume"] > raw["volumeAvg20d"] * self.config.tunableParams.breakoutDetectionVolumeAugmentationRatioThreshold
            if didAugumentEnoughByPrice or didAugumentEnoughByRatio or didAugumentEnoughByVolume:
                didPass = True
                break
        target.additional_info["didPassBreakoutDetectionFilter"] = didPass
        return didPass


class StructureConfirmationFilter(FilterBase):
    def __init__(self, config: ChaseHoundConfig):
        super().__init__(config)
        assert self.config.tunableParams.structureConfirmationMaTolerance is not None
        
        
    def apply(self, target: InvestmentTarget) -> bool:
        didPass = True
        for index, raw in target.candles.iloc[-self.config.tunableParams.structureConfirmationDaysLookback:].iterrows():
            if raw["close"] < raw["ma_20"] * self.config.tunableParams.structureConfirmationMaTolerance:
                didPass = False
                break
        target.additional_info["didPassStructureConfirmationFilter"] = didPass
        return didPass

