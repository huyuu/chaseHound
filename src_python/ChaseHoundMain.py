from src_python.ChaseHoundBase import ChaseHoundBase
from src_python.ChaseHoundConfig import ChaseHoundConfig, ChaseHoundTunableParams
from src_python.UsSymbolsHandler import UsSymbolsHandler
from src_python.YfinanceHandler import YfinanceHandler
from src_python.InvestmentTarget import InvestmentTarget
from src_python.FoundamentalFilters import MarketGapFilter, TurnoverFilter, PriceFilter, LastReportDateFilter
from src_python.VolatilityFilters import TurnoverSpikeFilter, AtrSpikeFilter, PriceStdSpikeFilter
from src_python.RightSideFilters import BreakOutDetectionFilter, StructureConfirmationFilter
from typing import List, Optional
import pandas as pd
from time import sleep
from datetime import timedelta, datetime
import os

class ChaseHoundMain(ChaseHoundBase):
    def __init__(self, config: ChaseHoundConfig):
        super().__init__()

        self.config: ChaseHoundConfig = config

        self.usSymbolsHandler: UsSymbolsHandler = UsSymbolsHandler(config)
        self.yfinanceHandler: YfinanceHandler = YfinanceHandler()

        # fundamental filters
        self.market_gap_filter: MarketGapFilter = MarketGapFilter(config)
        self.turnover_filter: TurnoverFilter = TurnoverFilter(config)
        self.price_filter: PriceFilter = PriceFilter(config)
        self.last_report_date_filter: LastReportDateFilter = LastReportDateFilter(config)

        # volatility filters
        self.turnover_spike_filter: TurnoverSpikeFilter = TurnoverSpikeFilter(config)
        self.atr_spike_filter: AtrSpikeFilter = AtrSpikeFilter(config)
        self.price_std_spike_filter: PriceStdSpikeFilter = PriceStdSpikeFilter(config)

        # right-side filters
        self.breakout_detection_filter: BreakOutDetectionFilter = BreakOutDetectionFilter(config)
        self.structure_confirmation_filter: StructureConfirmationFilter = StructureConfirmationFilter(config)

        self._targets: List[InvestmentTarget] = []

        # preprocessing
        if isinstance(self.config.tunableParams.start_date, str):
            self.start_date = datetime.strptime(self.config.tunableParams.start_date, "%Y-%m-%d")
        else:
            self.start_date = self.config.tunableParams.start_date
        if isinstance(self.config.tunableParams.end_date, str):
            self.end_date = datetime.strptime(self.config.tunableParams.end_date, "%Y-%m-%d")
        else:
            self.end_date = self.config.tunableParams.end_date


    def run(self):
        for virtual_date in pd.date_range(start=self.start_date, end=self.end_date, freq="D"):
            # Stage 1: Initialize investment targets
            # Stage 1-1: Monitor symbols list
            self._targets = self._fetchSymbolsData(virtual_date=virtual_date)

            # Stage 2: Filter investment targets
            # Stage 2-1: Filter with fundamental filters
            self._targets = self._filterWithFoundamentalFilters(self._targets)
            # Stage 2-2: Filter with volatility filters
            self._targets = self._filterWithVolatilityFilters(self._targets)
            # Stage 2-3: Filter with right-side filters
            self._targets = self._filterWithRightSideFilters(self._targets)

            # Stage 3: Filter with Signal Layers
            self._targets = self._filterWithSignalLayers(self._targets)

            # stage 4: fill the recorded performance (if in close-loop-simulation mode)
            self._targets = self._fillRecordedPerformance(self._targets, virtual_date)


            # Stage 4: Print and store the results
            self._printAndStoreResults(self._targets, virtual_date)

        self.yfinanceHandler.shutdown()

    def _fetchSymbolsData(self, virtual_date: datetime) -> List[InvestmentTarget]:
        # 1-1. Fetch NASDAQ symbols list
        nasdaq_symbols: pd.DataFrame = self.usSymbolsHandler.getNasdaqSymbols()

        # 1-2. Calculate the earliest date necessary for history prices
        earliest_date = virtual_date - timedelta(
            days=int(self.config.tunableParams.lowest_avg_turnover_days) * 3
        )

        # 1-3. Fetch the necessary history prices for all symbols
        history_prices_data: List[Optional[pd.DataFrame]] = self.yfinanceHandler.async_fetch_history_prices_of(
            nasdaq_symbols["symbol"].tolist(),
            from_date=earliest_date,
            to_date=virtual_date - timedelta(days=1),
            interval="1d",
        )

        # 1-4. Build InvestmentTarget instances & compute metrics
        investment_targets: List[InvestmentTarget] = []
        for symbol, marketCap, data in zip(
            nasdaq_symbols["symbol"].tolist(),
            nasdaq_symbols["marketCap"].tolist(),
            history_prices_data,
        ):
            if data is None or data.empty:
                continue

            # Add derived columns required by RightSide filters
            data_enhanced = self._enhance_candle_dataframe(data)

            # Calculate volatility-related metrics
            # Turnover metrics
            turnoverShortTerm = turnoverLongTerm = atrShortTerm = atrLongTerm = priceStdShortTerm = priceStdLongTerm = None
            assert all(
                hasattr(self.config.tunableParams, attr)
                for attr in [
                    "turnoverShortTermDays",
                    "turnoverLongTermDays",
                    "turnoverSpikeThreshold",
                ]
            )

            turnoverShortTerm = data_enhanced["turnover"].tail(self.config.tunableParams.turnoverShortTermDays).mean()
            turnoverLongTerm = data_enhanced["turnover"].tail(self.config.tunableParams.turnoverLongTermDays).mean()

            # ATR metrics
            assert all(
                hasattr(self.config.tunableParams, attr)
                for attr in ["atrShortTermDays", "atrLongTermDays", "atrSpikeThreshold"]
            )
            atrShortTerm = self._calculate_true_range(data_enhanced).tail(self.config.tunableParams.atrShortTermDays).mean()
            atrLongTerm = self._calculate_true_range(data_enhanced).tail(self.config.tunableParams.atrLongTermDays).mean()

            # Price Std metrics
            assert all(
                hasattr(self.config.tunableParams, attr)
                for attr in [
                    "priceStdShortTermDays",
                    "priceStdLongTermDays",
                    "priceStdSpikeThreshold",
                ]
            )
            priceStdShortTerm = data_enhanced["close"].tail(self.config.tunableParams.priceStdShortTermDays).std()
            priceStdLongTerm = data_enhanced["close"].tail(self.config.tunableParams.priceStdLongTermDays).std()

            target = InvestmentTarget(
                symbol=symbol,
                latestPrice=data_enhanced.iloc[-1]["close"],
                latestMarketCap=marketCap,
                latestTurnover=data_enhanced.iloc[-1]["turnover"],
                candles=data_enhanced,
                turnoverShortTerm=turnoverShortTerm,
                turnoverLongTerm=turnoverLongTerm,
                atrShortTerm=atrShortTerm,
                atrLongTerm=atrLongTerm,
                priceStdShortTerm=priceStdShortTerm,
                priceStdLongTerm=priceStdLongTerm,
            )

            investment_targets.append(target)

        return investment_targets

    # ------------------------------------------------------------------
    # Private helper methods
    # ------------------------------------------------------------------

    def _enhance_candle_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ajoute les colonnes nécessaires pour les filtres Right-Side."""
        df = df.copy()
        if "volumeAvg20d" not in df.columns:
            df["volumeAvg20d"] = df["volume"].rolling(window=20).mean()
        if "ma_20" not in df.columns:
            df["ma_20"] = df["close"].rolling(window=20).mean()
        return df

    @staticmethod
    def _calculate_true_range(df: pd.DataFrame) -> pd.Series:
        prev_close = df["close"].shift(1)
        tr = pd.concat(
            [
                df["high"] - df["low"],
                (df["high"] - prev_close).abs(),
                (df["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        return tr

        
    def _filterWithFoundamentalFilters(self, targets: List[InvestmentTarget]) -> List[InvestmentTarget]:
        # market gap, turnover, price, last_report_date, 
        print(f"Before filtering: {len(targets)} targets")
        filtered_targets = list(filter(self.market_gap_filter.apply, targets))
        print(f"After market gap filter: {len(filtered_targets)} targets")
        filtered_targets = list(filter(self.turnover_filter.apply, filtered_targets))
        print(f"After turnover filter: {len(filtered_targets)} targets")
        filtered_targets = list(filter(self.price_filter.apply, filtered_targets))
        print(f"After price filter: {len(filtered_targets)} targets")
        filtered_targets = list(filter(self.last_report_date_filter.apply, filtered_targets))
        print(f"After last report date filter: {len(filtered_targets)} targets")
        return filtered_targets


    def _filterWithVolatilityFilters(self, targets: List[InvestmentTarget]) -> List[InvestmentTarget]:
        assert self.config.tunableParams.volatilityFiltersPassingThreshold is not None
        print(f"Before volatility filters: {len(targets)} targets")
        result_targets = []
        for target in targets:
            turnoverSpikeDetected = self.turnover_spike_filter.apply(target)
            atrSpikeDetected = self.atr_spike_filter.apply(target)
            priceStdSpikeDetected = self.price_std_spike_filter.apply(target)
            if sum([turnoverSpikeDetected, atrSpikeDetected, priceStdSpikeDetected]) >= self.config.tunableParams.volatilityFiltersPassingThreshold:
                result_targets.append(target)
        print(f"After volatility filters: {len(result_targets)} targets")
        return result_targets


    def _filterWithRightSideFilters(self, targets: List[InvestmentTarget]) -> List[InvestmentTarget]:
        print(f"Before right-side filters: {len(targets)} targets")
        filtered_targets = list(filter(self.breakout_detection_filter.apply, targets))
        print(f"After breakout detection filter: {len(filtered_targets)} targets")
        filtered_targets = list(filter(self.structure_confirmation_filter.apply, filtered_targets))
        print(f"After structure confirmation filter: {len(filtered_targets)} targets")
        return filtered_targets

        
    def _filterWithSignalLayers(self, targets: List[InvestmentTarget]) -> List[InvestmentTarget]:
        print(f"Before signal layers: {len(targets)} targets")
        return targets

    def _fillRecordedPerformance(self, targets: List[InvestmentTarget], virtual_date: datetime) -> List[InvestmentTarget]:
        # skip this step if in close-loop-simulation mode
        if self.usSymbolsHandler.doesDateReferToPrediction(virtual_date):
            return targets

        # fill the recorded performance
        candles_at_date: List[Optional[pd.DataFrame]] = self.yfinanceHandler.async_fetch_history_prices_of(
            [target.symbol for target in targets],
            from_date=self.usSymbolsHandler.getPreviousMarketOpenDate(virtual_date),
            to_date=virtual_date,
            interval="1d",
        )

        for target, candle in zip(targets, candles_at_date):
            target.additional_info["currentDayOpenPrice"] = candle.iloc[-1]["open"]
            target.additional_info["currentDayClosePrice"] = candle.iloc[-1]["close"]
            target.additional_info["currentDayPriceChange"] = target.additional_info["currentDayClosePrice"] - target.latestPrice
            target.additional_info["currentDayPriceChangePercentage"] = target.additional_info["currentDayPriceChange"] / target.latestPrice

        return targets


    def _printAndStoreResults(self, targets: List[InvestmentTarget], virtual_date: datetime):
        # store targets to csv
        result_df = pd.DataFrame()
        for target in targets:
            result_df = pd.concat([result_df, target.to_series().to_frame().T], ignore_index=True, axis=0)
        path = os.path.join(self.project_root, "temp", f"results_{virtual_date.strftime('%Y%m%d')}.csv")
        result_df.to_csv(path, index=False)



if __name__ == "__main__":
    tunableParams = ChaseHoundTunableParams()
    config = ChaseHoundConfig(tunableParams=tunableParams)
    main = ChaseHoundMain(config)
    main.run()