# update submodules
import shutil
import subprocess
import os
import stat
if os.path.exists("submodules"):
    def _handle_remove_readonly(func, path, exc_info):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            raise
    shutil.rmtree("submodules", onerror=_handle_remove_readonly)
os.makedirs("submodules", exist_ok=True)
subprocess.run(["git", "clone", "--single-branch", "--branch", "main_lightweight", "--depth", "1", "https://github.com/huyuu/LLMTrader.git", "submodules/LLMTrader"])
subprocess.run(["git", "clone", "--depth", "1", "https://github.com/rreichel3/US-Stock-Symbols.git", "submodules/us_stock_symbols"])


from src_python.ChaseHoundBase import ChaseHoundBase
from src_python.ChaseHoundConfig import ChaseHoundConfig, ChaseHoundTunableParams
from src_python.UsSymbolsHandler import UsSymbolsHandler
from src_python.YfinanceHandler import YfinanceHandler
from src_python.InvestmentTarget import InvestmentTarget
from src_python.FoundamentalFilters import MarketGapFilter, TurnoverFilter, PriceFilter, LastReportDateFilter
from src_python.VolatilityFilters import TurnoverSpikeFilter, AtrSpikeFilter, PriceStdSpikeFilter
from src_python.RightSideFilters import BreakOutDetectionFilter, StructureConfirmationFilter
from src_python.PostAnalysis import PostAnalysis
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

        # post analysis
        self.postAnalysis: PostAnalysis = PostAnalysis(config)

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


    def run(self, verbose: bool = False):
        self._preprocessing()

        virtual_date = self.end_date
        while virtual_date >= self.start_date:
            # Stage 1: Initialize investment targets
            # Stage 1-1: Monitor symbols list
            self._targets: List[InvestmentTarget] = self._fetchSymbolsData(virtual_date=virtual_date)
            self._targets = self._preprocessAfterFetchingSymbolsData(self._targets)
            original_targets: List[InvestmentTarget] = self._targets.copy()

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

            # fill in the performance for the filtered targets
            all_targets = self._fillRecordedPerformance(original_targets, virtual_date)

            # calculate the most n targets which have the highest currentDayPriceChangePercentage
            best_n_targets = self._calculateMostNTargets(all_targets, n=self.config.tunableParams.bestTargetsN)

            # pass the best n targets through the filters and find out in which filter they dropped
            best_n_targets_dropped_out_at = self._findTheFilterWhereItDroppedOut(best_n_targets)

            # stage 5: find and store sp500 avg. Sp500 could be retrieved by ^SPX symbol in yf
            sp500_target = self._findAndStoreSp500Avg(virtual_date)

            # Stage 6: Print and store the results
            self._printAndStoreResults([sp500_target], virtual_date, profix="sp500Avg")
            best_n_targets_df = self._printAndStoreResultsForBestNTargets(best_n_targets, virtual_date, best_n_targets_dropped_out_at, profix="bestTargetsOfTheDay")
            self._printAndStoreResultsForMainTargets(self._targets, virtual_date, best_n_targets_df, profix="results")

            self._postAnalysis(virtual_date)

            virtual_date = self.usSymbolsHandler.getPreviousMarketOpenDate(virtual_date)

        self.yfinanceHandler.shutdown()

    def _preprocessing(self):
        # set up temp folder
        if os.path.exists(ChaseHoundBase.temp_folder):
            shutil.rmtree(ChaseHoundBase.temp_folder)
        os.makedirs(ChaseHoundBase.temp_folder, exist_ok=True)

        nasdaq_symbols: pd.DataFrame = self.usSymbolsHandler.getNasdaqSymbols()
        retrieve_end_date = self.end_date + timedelta(days=min(7, (self.absolute_current_date_in_eastern - self.start_date).days))
        # secure cache
        self.yfinanceHandler.loadFromRamOrAsyncFetchHistoryPricesOf(
            nasdaq_symbols["symbol"].tolist() + ["^SPX"], 
            self.start_date - timedelta(days=7), 
            retrieve_end_date, 
            "1d"
        )

    def _fetchSymbolsData(self, virtual_date: datetime) -> List[InvestmentTarget]:
        # 1-1. Fetch NASDAQ symbols list
        nasdaq_symbols: pd.DataFrame = self.usSymbolsHandler.getNasdaqSymbols()

        # 1-2. Calculate the earliest date necessary for history prices
        earliest_date = virtual_date - timedelta(
            days=int(self.config.tunableParams.lowest_avg_turnover_days) * 3
        )

        # 1-3. Fetch the necessary history prices for all symbols
        history_prices_data: List[Optional[pd.DataFrame]] = self.yfinanceHandler.loadFromRamOrAsyncFetchHistoryPricesOf(
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
                previousDayClosePrice=data_enhanced.iloc[-1]["close"],
                previousDayVolume=data_enhanced.iloc[-1]["volume"],
                latestMarketCap=marketCap,
                previousDayTurnover=data_enhanced.iloc[-1]["turnover"],
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
        candles_at_date: List[Optional[pd.DataFrame]] = self.yfinanceHandler.loadFromRamOrAsyncFetchHistoryPricesOf(
            [target.symbol for target in targets],
            from_date=self.usSymbolsHandler.getPreviousMarketOpenDate(virtual_date),
            to_date=virtual_date,
            interval="1d",
        )

        for target, candle in zip(targets, candles_at_date):
            if candle is None or candle.empty:
                continue
            target.additional_info["currentDayOpenPrice"] = candle.iloc[-1]["open"]
            target.additional_info["currentDayHighPrice"] = candle.iloc[-1]["high"]
            target.additional_info["currentDayLowPrice"] = candle.iloc[-1]["low"]
            target.additional_info["currentDayClosePrice"] = candle.iloc[-1]["close"]
            target.additional_info["currentDayPriceChange"] = target.additional_info["currentDayClosePrice"] - target.previousDayClosePrice
            target.additional_info["currentDayPriceChangePercentage"] = target.additional_info["currentDayPriceChange"] / target.previousDayClosePrice
            target.additional_info["openingGapInPercentage"] = target.additional_info["currentDayOpenPrice"] - target.previousDayClosePrice / target.previousDayClosePrice

        return targets


    def _printAndStoreResults(self, targets: List[InvestmentTarget], virtual_date: datetime, profix: str = "") -> pd.DataFrame:
        # store targets to csv
        result_df = pd.DataFrame()
        for target in targets:
            result_df = pd.concat([result_df, target.to_series().to_frame().T], ignore_index=True, axis=0)
        if len(result_df) == 0:
            return result_df
        # sort by currentDayPriceChangePercentage
        result_df = result_df.sort_values(by="currentDayPriceChangePercentage", ascending=False)
        # add turnover ranking for the existing symbols
        # result_df["turnoverRanking"] = result_df["previousDayTurnover"].rank(method="first", ascending=False)
        path = os.path.join(self.project_root, "temp", f"{virtual_date.strftime('%Y%m%d')}_{profix}.csv")
        
        result_df.to_csv(path, index=False)
        return result_df

    def _printAndStoreResultsForMainTargets(self, targets: List[InvestmentTarget], virtual_date: datetime, best_n_targets: pd.DataFrame, profix: str = "") -> pd.DataFrame:
        # store targets to csv
        result_df = pd.DataFrame()
        for target in targets:
            result_df = pd.concat([result_df, target.to_series().to_frame().T], ignore_index=True, axis=0)
        if len(result_df) == 0:
            return result_df
        # sort by currentDayPriceChangePercentage
        result_df = result_df.sort_values(by="currentDayPriceChangePercentage", ascending=False)
        # add turnover ranking for the existing symbols
        # result_df["turnoverRanking"] = result_df["previousDayTurnover"].rank(method="first", ascending=False)
        # add isInBestNTargets
        result_df["isInBestNTargets"] = result_df["symbol"].isin(best_n_targets["symbol"].tolist()).astype(bool)

        path = os.path.join(self.project_root, "temp", f"{virtual_date.strftime('%Y%m%d')}_{profix}.csv")
        result_df.to_csv(path, index=False)
        return result_df

    def _printAndStoreResultsForBestNTargets(self, targets: List[InvestmentTarget], virtual_date: datetime, dropped_out_at: List[str], profix: str = "") -> pd.DataFrame:
        # store targets to csv
        result_df = pd.DataFrame()
        for target in targets:
            result_df = pd.concat([result_df, target.to_series().to_frame().T], ignore_index=True, axis=0)
        if len(result_df) == 0:
            return result_df
        # sort by currentDayPriceChangePercentage
        result_df = result_df.sort_values(by="currentDayPriceChangePercentage", ascending=False)
        # add turnover ranking for the existing symbols
        # result_df["turnoverRanking"] = result_df["previousDayTurnover"].rank(method="first", ascending=False)
        # add droppedOutAtFilter
        result_df["droppedOutAtFilter"] = dropped_out_at
        path = os.path.join(self.project_root, "temp", f"{virtual_date.strftime('%Y%m%d')}_{profix}.csv")
        result_df.to_csv(path, index=False)
        return result_df

    def _postAnalysis(self, virtual_date: datetime):
        self.postAnalysis.plotDistribution()

    def _findAndStoreSp500Avg(self, virtual_date: datetime):
        """Fetch ^SPX data, compute basic volatility metrics, store a CSV snapshot and
        return an ``InvestmentTarget`` that represents the S&P 500 average for the
        given *virtual_date*.

        The method mirrors (on a single symbol) the logic used in
        ``_fetchSymbolsData`` / ``_fillRecordedPerformance`` so that the returned
        target can be handled identically by the rest of the pipeline.
        """

        symbol = "^SPX"

        # ------------------------------------------------------------------
        # 1. Retrieve the necessary historical candles for ^SPX
        # ------------------------------------------------------------------
        earliest_date = virtual_date - timedelta(
            days=int(self.config.tunableParams.lowest_avg_turnover_days) * 3
        )

        history_prices_list = self.yfinanceHandler.loadFromRamOrAsyncFetchHistoryPricesOf(
            [symbol],
            from_date=earliest_date,
            to_date=virtual_date - timedelta(days=1),  # only up to the prev. day
            interval="1d",
        )
        data = history_prices_list[0] if history_prices_list else None
        if data is None or data.empty:
            print(f"No data found for {symbol} at {virtual_date}")
            # When data is unavailable, return a minimal placeholder to avoid
            # breaking the caller.  Down-stream code will simply skip empty
            # targets.
            return InvestmentTarget(
                symbol=symbol,
                previousDayClosePrice=float("nan"),
                previousDayVolume=float("nan"),
                latestMarketCap=float("nan"),
                previousDayTurnover=float("nan"),
                candles=pd.DataFrame(),
            )

        # ------------------------------------------------------------------
        # 2. Enhance dataframe and compute metrics (turnover / ATR / price std)
        # ------------------------------------------------------------------
        data_enhanced = self._enhance_candle_dataframe(data)

        turnoverShortTerm = data_enhanced["turnover"].tail(
            self.config.tunableParams.turnoverShortTermDays
        ).mean()
        turnoverLongTerm = data_enhanced["turnover"].tail(
            self.config.tunableParams.turnoverLongTermDays
        ).mean()

        atr_series = self._calculate_true_range(data_enhanced)
        atrShortTerm = atr_series.tail(self.config.tunableParams.atrShortTermDays).mean()
        atrLongTerm = atr_series.tail(self.config.tunableParams.atrLongTermDays).mean()

        priceStdShortTerm = data_enhanced["close"].tail(
            self.config.tunableParams.priceStdShortTermDays
        ).std()
        priceStdLongTerm = data_enhanced["close"].tail(
            self.config.tunableParams.priceStdLongTermDays
        ).std()

        # Previous-day snapshot (last row of the enhanced dataframe)
        prev_candle = data_enhanced.iloc[-1]

        sp500_target = InvestmentTarget(
            symbol=symbol,
            previousDayClosePrice=prev_candle["close"],
            previousDayVolume=prev_candle["volume"],
            latestMarketCap=float("nan"),  # not applicable for an index
            previousDayTurnover=prev_candle["turnover"],
            candles=data_enhanced,
            turnoverShortTerm=turnoverShortTerm,
            turnoverLongTerm=turnoverLongTerm,
            atrShortTerm=atrShortTerm,
            atrLongTerm=atrLongTerm,
            priceStdShortTerm=priceStdShortTerm,
            priceStdLongTerm=priceStdLongTerm,
        )

        # ------------------------------------------------------------------
        # 3. Fill same-day performance metrics and store to CSV
        # ------------------------------------------------------------------
        sp500_target = self._fillRecordedPerformance([sp500_target], virtual_date)[0]

        return sp500_target


    def _calculateMostNTargets(self, targets: List[InvestmentTarget], n: int) -> List[InvestmentTarget]:
        return sorted(targets, key=lambda x: x.additional_info["currentDayPriceChangePercentage"], reverse=True)[:n]


    def _findTheFilterWhereItDroppedOut(self, targets: List[InvestmentTarget]) -> List[str]:
        """Determine at which filter stage each *target* was discarded.

        The function sequentially re-applies all filters (fundamental →
        volatility → right-side).  For every *target*, the first filter that
        rejects it is recorded and returned.  If a target passes all filters,
        the string ``"passed_all_filters"`` is returned instead.

        Side-effect: the result is also stored in
        ``target.additional_info["droppedOutAtFilter"]`` so that the
        information gets exported alongside other metrics when the target is
        converted to a ``pd.Series``.
        """

        dropped_out_list: List[str] = []

        # ------------------------------------------------------------------
        # Re-use the existing *batch* filter helpers to locate the stage where
        # each target has been eliminated.  We compare the target lists after
        # every stage to identify the first filter group that discarded it.
        # ------------------------------------------------------------------

        # 1. Initialise the reason map with the optimistic outcome
        reason_map = {t.symbol: "passedAllFilters" for t in targets}

        # 2. Fundamental filters ------------------------------------------------
        after_foundamental = self._filterWithFoundamentalFilters(targets)
        for t in targets:
            if t not in after_foundamental:
                reason_map[t.symbol] = "foundamentalFilters"

        # 3. Volatility filters -------------------------------------------------
        after_volatility = self._filterWithVolatilityFilters(after_foundamental)
        for t in after_foundamental:
            if t not in after_volatility and reason_map[t.symbol] == "passedAllFilters":
                reason_map[t.symbol] = "volatilityFilters"

        # 4. Right-side filters --------------------------------------------------
        after_right_side = self._filterWithRightSideFilters(after_volatility)
        for t in after_volatility:
            if t not in after_right_side and reason_map[t.symbol] == "passedAllFilters":
                reason_map[t.symbol] = "rightSideFilters"

        # 5. Signal layers (currently a pass-through, but kept for completeness)
        after_signal_layers = self._filterWithSignalLayers(after_right_side)
        for t in after_right_side:
            if t not in after_signal_layers and reason_map[t.symbol] == "passedAllFilters":
                reason_map[t.symbol] = "signalLayers"

        # 6. Persist result on each target and build output list
        for t in targets:
            t.additional_info["droppedOutAtFilter"] = reason_map[t.symbol]
            dropped_out_list.append(reason_map[t.symbol])

        return dropped_out_list

    def _preprocessAfterFetchingSymbolsData(self, targets: List[InvestmentTarget]) -> List[InvestmentTarget]:
        # calculate previousDayTurnover ranking, among the given targets
        
        
        # Return early if there are no targets to process
        if not targets:
            return targets

        # ------------------------------------------------------------------
        # Compute ranking based on ``previousDayTurnover``.
        # The highest turnover receives rank 1, the next highest rank 2, etc.
        # ------------------------------------------------------------------

        # Sort targets by turnover in *descending* order (highest first)
        sorted_by_turnover = sorted(
            targets,
            key=lambda t: (t.previousDayTurnover if t.previousDayTurnover is not None else -float("inf")),
            reverse=True,
        )

        # Assign rank — note that we preserve stability ("first" method)
        for rank, target in enumerate(sorted_by_turnover, start=1):
            # Store in ``additional_info`` so that it gets exported by ``to_series``
            target.additional_info["previousDayTurnoverRanking"] = rank

        # Nothing else to modify – the caller expects the *same* list back
        return targets


if __name__ == "__main__":
    tunableParams = ChaseHoundTunableParams()
    config = ChaseHoundConfig(tunableParams=tunableParams)
    main = ChaseHoundMain(config)
    main.run()