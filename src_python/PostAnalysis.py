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
        sp500AvgDf = pd.DataFrame(columns=["date", "performanceMean", "performanceStd"])
        # DataFrame to keep track of the hit-rate (ratio of predictions that hit the top-N performers)
        hitRateDf = pd.DataFrame(columns=["date", "hitRate"])
        for fileName in os.listdir(tempFolderPath):
            if not fileName.endswith(".csv"):
                continue
            if not fileName.split(".")[0].endswith("results"):
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
            date = fileName.split(".")[0].split("_")[0]
            date = datetime.strptime(date, "%Y%m%d")
            performanceMean = dfOfOneDay["currentDayPriceChangePercentage"].mean()
            performanceStd = dfOfOneDay["currentDayPriceChangePercentage"].std()

            if len(timelineDf) == 0:
                timelineDf = pd.DataFrame({"date": [date], "performanceMean": [performanceMean], "performanceStd": [performanceStd]})
            else:
                timelineDf = pd.concat([timelineDf, pd.DataFrame({"date": [date], "performanceMean": [performanceMean], "performanceStd": [performanceStd]})], ignore_index=True)

            # ------------------------------------------------------------------
            # Compute the hit-rate using the existing didInBestNTargets column
            # ------------------------------------------------------------------
            if "isInBestNTargets" in dfOfOneDay.columns:
                try:
                    hitRate = dfOfOneDay["isInBestNTargets"].mean()

                    if len(hitRateDf) == 0:
                        hitRateDf = pd.DataFrame({"date": [date], "hitRate": [hitRate]})
                    else:
                        hitRateDf = pd.concat([hitRateDf, pd.DataFrame({"date": [date], "hitRate": [hitRate]})], ignore_index=True)
                except Exception as e:
                    print(f"Error computing hit rate for {date}: {e}")
            else:
                print(f"Warning: isInBestNTargets column not found in {fileName}")


        for fileName in os.listdir(tempFolderPath):
            if not fileName.endswith(".csv"):
                continue
            if not fileName.split(".")[0].endswith("sp500Avg"):
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
            date = fileName.split(".")[0].split("_")[0]
            date = datetime.strptime(date, "%Y%m%d")
            performanceMean = dfOfOneDay["currentDayPriceChangePercentage"].mean()
            performanceStd = dfOfOneDay["currentDayPriceChangePercentage"].std()

            if len(sp500AvgDf) == 0:
                sp500AvgDf = pd.DataFrame({"date": [date], "performanceMean": [performanceMean], "performanceStd": [performanceStd]})
            else:
                sp500AvgDf = pd.concat([sp500AvgDf, pd.DataFrame({"date": [date], "performanceMean": [performanceMean], "performanceStd": [performanceStd]})], ignore_index=True)

        # ----------------------------------------------------------------------
        # Visualisation: main axis for performance; secondary axis for hit-rate
        # ----------------------------------------------------------------------
        fig, ax1 = plt.subplots(figsize=(10, 5))

        # Performance curves (left axis)
        ax1.plot(timelineDf["date"], timelineDf["performanceMean"], label="Performance Mean (Left Axis)", color="C0")
        ax1.plot(sp500AvgDf["date"], sp500AvgDf["performanceMean"], label="SP500 Avg (Left Axis)", color="C1")
        ax1.fill_between(
            timelineDf["date"],
            timelineDf["performanceMean"] - 2 * timelineDf["performanceStd"],
            timelineDf["performanceMean"] + 2 * timelineDf["performanceStd"],
            alpha=0.2,
        )
        ax1.axhline(y=0, color="black", linestyle="--", linewidth=0.5)
        ax1.set_ylim(-0.2, 0.5)
        ax1.set_xlabel("Date")
        ax1.set_ylabel("Performance Mean")

        # Hit-rate curve (right axis, different unit scale)
        ax2 = ax1.twinx()
        if len(hitRateDf) > 0:
            ax2.plot(hitRateDf["date"], hitRateDf["hitRate"], color="C2", label="Hit Rate (Right Axis)", alpha=0.75)
            ax2.set_ylabel("Hit Rate")
            ax2.set_ylim(0, 1)

        # Merge legends from both axes
        lines_1, labels_1 = ax1.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="best")

        fig.suptitle("Performance Distribution & Hit Rate")
        fig.savefig(os.path.join(self.config.project_root, "temp", "performanceDistribution.png"), dpi=300)
            
if __name__ == "__main__":
    config = ChaseHoundConfig(ChaseHoundTunableParams())
    postAnalysis = PostAnalysis(config)
    postAnalysis.plotDistribution()