

from src_python.ChaseHoundBase import ChaseHoundBase


# Target est tout simplement un symbole que nous prévoyons à investir.
# Cette classe a été étendue pour calculer et stocker toutes les métriques
# nécessaires aux différents filtres (fondamentaux, volatilité, right-side).

from typing import Optional
import pandas as pd


class InvestmentTarget(ChaseHoundBase):

    def __init__(
        self,
        symbol: str,
        latestPrice: float,
        latestMarketCap: float,
        latestTurnover: float,
        candles: pd.DataFrame,
        turnoverShortTerm: float = None,
        turnoverLongTerm: float = None,
        atrShortTerm: float = None,
        atrLongTerm: float = None,
        priceStdShortTerm: float = None,
        priceStdLongTerm: float = None,
    ):
        """Classe simple pour représenter un titre potentiel d'investissement.

        Aucun calcul complexe n'est effectué ici afin de maintenir la classe
        lisible. Tous les indicateurs dérivés sont calculés ailleurs et ajoutés
        dynamiquement aux instances.
        """

        super().__init__()

        self.symbol: str = symbol
        self.latestPrice: float = latestPrice
        self.latestMarketCap: float = latestMarketCap
        self.endTurnover: float = latestTurnover

        # Historique complet de prix/volume (désormais requis)
        self.candles: pd.DataFrame = candles

        # Les attributs suivants sont maintenant requis à l'initialisation
        self.turnoverShortTerm: float = turnoverShortTerm
        self.turnoverLongTerm: float = turnoverLongTerm
        self.atrShortTerm: float = atrShortTerm
        self.atrLongTerm: float = atrLongTerm
        self.priceStdShortTerm: float = priceStdShortTerm
        self.priceStdLongTerm: float = priceStdLongTerm

        self.additional_info: dict = {}

    # ------------------------------------------------------------------
    # Public helper methods
    # ------------------------------------------------------------------

    def to_series(self) -> pd.Series:
        """Return a *flat* ``pd.Series`` representation of the target.

        The resulting series is convenient for building a summary
        ``pd.DataFrame`` via ``pd.concat``.  It contains:

        1. Basic symbol and latest market information (price, turnover …).
        2. OHLCV fields of the latest candle (open/high/low/close/volume).
        3. Recently-computed volatility metrics (turnover/ATR/std-dev).
        4. Every boolean attribute whose name starts with ``is`` – this
           convention is used for filter flags such as
           ``isBreakoutDetectionFilterPassed``.  The method therefore adapts
           automatically when new filters add flags to the instance.
        """

        # Basic attributes
        data = {
            "symbol": self.symbol,
            "latestPrice": self.latestPrice,
            "latestMarketCap": self.latestMarketCap,
            "latestTurnover": self.endTurnover,
            "turnoverShortTerm": self.turnoverShortTerm,
            "turnoverLongTerm": self.turnoverLongTerm,
            "atrShortTerm": self.atrShortTerm,
            "atrLongTerm": self.atrLongTerm,
            "priceStdShortTerm": self.priceStdShortTerm,
            "priceStdLongTerm": self.priceStdLongTerm,
        }

        # Latest OHLCV information if available
        if isinstance(self.candles, pd.DataFrame) and not self.candles.empty:
            last = self.candles.iloc[-1]
            for col in ["open", "high", "low", "close", "volume"]:
                # Some data sources use capitalised column names – be lenient
                if col in last:
                    data[col] = last[col]
                elif col.capitalize() in last:
                    data[col] = last[col.capitalize()]
                else:
                    data[col] = None
        else:
            # Preserve column structure even if data is missing
            for col in ["open", "high", "low", "close", "volume"]:
                data[col] = None

        # Add filter results from additional_info dictionary
        if hasattr(self, 'additional_info') and isinstance(self.additional_info, dict):
            for filter_name, filter_result in self.additional_info.items():
                data[filter_name] = filter_result

        return pd.Series(data)

    

