from typing import List
import pandas as pd
import os
from datetime import datetime, timedelta
import pandas_market_calendars as mcal

from src_python.ChaseHoundBase import ChaseHoundBase
from src_python.ChaseHoundConfig import ChaseHoundConfig


class UsSymbolsHandler(ChaseHoundBase):
    def __init__(self, config: ChaseHoundConfig):
        super().__init__()
        self.config = config
        self.market_open_dates = self._getNasdaqMarketOpenDate()

    def getNasdaqSymbols(self) -> pd.DataFrame:
        symbols_df = pd.read_json(os.path.join(self.project_root, "submodules", "us_stock_symbols", "nasdaq", "nasdaq_full_tickers.json"))
        # filter out symbols of which marketcap is less than 100M
        symbols_df["marketCap"] = pd.to_numeric(symbols_df["marketCap"], errors='coerce')
        symbols_df = symbols_df[symbols_df["marketCap"] >= self.config.tunableParams.lowest_market_cap]
        return symbols_df

    def getNextMarketOpenDate(self, currentDate: datetime) -> datetime:
        next_day = currentDate + timedelta(days=1)
        # Iterate over the market open dates
        next_market_open_date = self.market_open_dates.loc[self.market_open_dates["date"] == next_day, "next_market_open_date"]
        if len(next_market_open_date) == 0:
            return None
        return next_market_open_date.iloc[0].to_pydatetime()

    def getPreviousMarketOpenDate(self, currentDate: datetime) -> datetime:
        # Find all market open dates that are before the current date
        previous_dates = self.market_open_dates[self.market_open_dates["date"] < currentDate]
        
        # Filter to only actual market open dates (where market_open is not null)
        actual_market_dates = previous_dates[previous_dates["market_open"].notna()]
        
        if len(actual_market_dates) == 0:
            return None
            
        # Get the most recent market open date
        most_recent_date = actual_market_dates["date"].max()
        return most_recent_date.to_pydatetime()

    def doesDateReferToCloseLoopSimulation(self, date: datetime) -> bool:
        # if date < today 00:00:00, it is in close-loop-simulation mode
        if date <= self.absolute_current_date_in_eastern:
            return True
        # if date is after market close time, it is in close-loop-simulation mode
        if date > self._getMarketCloseTimeOf(self.absolute_current_datetime_in_eastern):
            return True
        # if date is before market close time, it is in prediction mode
        return False

    def doesDateReferToPrediction(self, date: datetime) -> bool:
        return not self.doesDateReferToCloseLoopSimulation(date)


    def _getNasdaqMarketOpenDate(self) -> pd.DataFrame:
        # Get the NASDAQ calendar
        nyse = mcal.get_calendar('NASDAQ')

        # Define the date range for which you want to fetch market open dates
        start_date = datetime.strptime(self.config.tunableParams.start_date, "%Y-%m-%d")
        start_date = start_date - timedelta(days=7)
        end_date = datetime.strptime(self.config.tunableParams.end_date, "%Y-%m-%d")
        end_date = end_date + timedelta(days=7)

        # Get the schedule for the specified date range
        schedule = nyse.schedule(start_date=start_date, end_date=end_date)

        # Reset the index to make the datetime index a column and reset index to int
        schedule.reset_index(inplace=True, drop=False, names=["date"])
        schedule.loc[:, "next_market_open_date"] = schedule.loc[:, "date"]
        # schedule.loc[:, "market_open_date"] = schedule.loc[:, "date"]
        # schedule.set_index("date", inplace=True, drop=True)

        # create a new dateframe with all the dates from start_date to end_date
        all_dates = pd.date_range(start=start_date, end=end_date)
        all_dates_df = pd.DataFrame({"date": all_dates})

        # merge the schedule and all_dates_df on the date column
        schedule = pd.merge(all_dates_df, schedule, on="date", how="left")

        # fill the next_market_open_date column with the next market open date
        schedule.loc[:, "next_market_open_date"] = schedule.loc[:, "next_market_open_date"].bfill()

        schedule.reset_index(inplace=True, drop=True)
        return schedule

    def _getMarketCloseTimeOf(self, date: datetime) -> datetime:
        only_date = datetime(date.year, date.month, date.day)
        market_close_time = self.market_open_dates.loc[self.market_open_dates["date"] == only_date, "market_close"]
        if len(market_close_time) == 0:
            return None
        market_close_time = market_close_time.iloc[-1].to_pydatetime()
        return market_close_time
