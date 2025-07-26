from src_python.ChaseHoundBase import ChaseHoundBase
from src_python.ChaseHoundConfig import ChaseHoundConfig, ChaseHoundTunableParams
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

class PostAnalysis(ChaseHoundBase):
    def __init__(self, config: ChaseHoundConfig):
        super().__init__()
        self.config = config

    def plotDistribution(self):
        tempFolderPath = os.path.join(self.config.project_root, "temp")

        timelineDf = pd.DataFrame(columns=["date", "performanceMean", "performanceStd"])
        for fileName in os.listdir(tempFolderPath):
            if not fileName.endswith(".csv"):
                continue
            filePath = os.path.join(tempFolderPath, fileName)
            try:
                dfOfOneDay = pd.read_csv(filePath)
            except Exception as e:
                print(f"Error reading file {filePath}: {e}")
                continue

            if "currentDayPriceChangePercentage" not in dfOfOneDay.columns:
                continue

            if len(dfOfOneDay) == 0:
                continue
            
            # plot the distribution of currentDayPriceChangePercentage
            date = fileName.split(".")[0].split("_")[-1]
            date = datetime.strptime(date, "%Y%m%d")
            performanceMean = dfOfOneDay["currentDayPriceChangePercentage"].mean()
            performanceStd = dfOfOneDay["currentDayPriceChangePercentage"].std()

            if len(timelineDf) == 0:
                timelineDf = pd.DataFrame({"date": [date], "performanceMean": [performanceMean], "performanceStd": [performanceStd]})
            else:
                timelineDf = pd.concat([timelineDf, pd.DataFrame({"date": [date], "performanceMean": [performanceMean], "performanceStd": [performanceStd]})], ignore_index=True)

        # plot x-dates, y-performance distributions with fill between +-2 std
        plt.figure(figsize=(10, 5))
        plt.plot(timelineDf["date"], timelineDf["performanceMean"], label="Performance Mean")
        plt.fill_between(timelineDf["date"], timelineDf["performanceMean"] - 2 * timelineDf["performanceStd"], timelineDf["performanceMean"] + 2 * timelineDf["performanceStd"], alpha=0.2)
        plt.legend()
        plt.show()
            
if __name__ == "__main__":
    config = ChaseHoundConfig(ChaseHoundTunableParams())
    postAnalysis = PostAnalysis(config)
    postAnalysis.plotDistribution()