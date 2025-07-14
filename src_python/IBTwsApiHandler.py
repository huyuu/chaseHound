import sys
sys.path.append("..")


from ibapi.common import * # @UnusedWildImport
from ibapi.order_condition import * # @UnusedWildImport
from ibapi.contract import * # @UnusedWildImport
from ibapi.order import * # @UnusedWildImport
from ibapi.order_cancel import * # @UnusedWildImport
from ibapi.order_state import * # @UnusedWildImport
from ibapi.execution import Execution
from ibapi.execution import ExecutionFilter
from ibapi.commission_and_fees_report import CommissionAndFeesReport
from ibapi.ticktype import * # @UnusedWildImport
from ibapi.tag_value import TagValue

from ibapi.account_summary_tags import *

from submodules.LLMTrader.src.IBTwsAPIHandler import IBTwsAPIHandler as LLMTraderIBTwsAPIHandler

class IBTwsApiHandler(LLMTraderIBTwsAPIHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # MARK: - Fetch Market Data

    def async_fetch_last_trade_price_for_symbol(self, symbol: str, primaryExchange: str) -> float:
        """
        Fetch the last trade price for a symbol.
        """
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        contract.primaryExchange = primaryExchange

        request_id = self.getNextValidId()
        self._init_async_flags_and_results(func_name=f"lastTradedPrice_{request_id}")
        # self.reqMarketDataType(3)  # Request delayed data
        self.reqMarketDataType(1)  # Request live data
        # response handler: self.tickPrice(...)
        # https://ibkrcampus.com/campus/ibkr-api-page/twsapi-doc/#available-tick-types
        self.reqMktData(request_id, contract, "", False, False, [])
        last_traded_price = self._await_get_future_return(func_name=f"lastTradedPrice_{request_id}")

    def tickPrice(self, reqId: int, tickType: int, price: float, attrib: TickAttrib):
        """
        Handle the tickPrice event.
        """
        if reqId == self.request_id:
            self.last_traded_price = price
    
    
