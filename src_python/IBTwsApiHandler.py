from ibapi import wrapper
from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.utils import getTimeStrFromMillis, longMaxString
from ibapi.utils import iswrapper

# types
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

from src.IBTwsAPIHandler import IBTwsAPIHandler as LLMTraderIBTwsAPIHandler
from ChaseHoundBase import ChaseHoundBase

import threading
from time import sleep
import queue
from concurrent.futures import Future
from tqdm import tqdm
import time


class IBTwsApiHandler_ConcurrentGetPrice(LLMTraderIBTwsAPIHandler, ChaseHoundBase):
    def __init__(self):
        super().__init__()
        ChaseHoundBase.__init__(self)
        # EClient.__init__(self, self)
        # internal structures for managing market data request queue
        self._max_concurrent_requests = 1
        self._working_queue: 'queue.Queue[tuple[str, str, Future]]' = queue.Queue(maxsize=self._max_concurrent_requests)
        self._results_dict: dict[int, tuple[str, Future]] = {}
        self._results_dict_lock = threading.Lock()

        # background worker thread to process waiting queue continuously
        self._queue_worker_stop_event = threading.Event()
        self._queue_worker_thread = threading.Thread(target=self._queue_worker, daemon=True)
        self._queue_worker_thread.start()

    def async_run(self) -> bool:
        didSucceed = self._connect_to_server()
        if not didSucceed:
            return False
        tws_thread = threading.Thread(target=self.run, daemon=True)
        tws_thread.start()
        sleep(3)
        return True
    
    def shutdown(self):
        """Optional: cleanly stop the queue worker when shutting down the API handler."""
        self._queue_worker_stop_event.set()
        if self._queue_worker_thread.is_alive():
            self._queue_worker_thread.join(timeout=1)
    
    def error(self, reqId, errorCode, errorString, advancedOrderReject, not_important):
        print(f"Error: reqid: {reqId}, ", end="")
        super().error(reqId, errorCode, errorString, advancedOrderReject, not_important)
        # if the market data request is not completed, set the future to None
        if reqId in self._results_dict:
            symbol, future = self._results_dict.get(reqId)
            if future is None or not future.done():
                future.set_result(None)
                self._working_queue.task_done()
    # MARK: - Private Helper Methods
    
    

    # MARK: - Fetch Market Data

    def async_fetch_last_trade_price_for_symbols(self, symbols: list[str], primaryExchanges: list[str]) -> list[Future]:
        """Create futures for a batch of symbols and start processing, returning immediately.

        The caller receives a list of concurrent.futures.Future objects.  Each future will be
        completed with the fetched price when it becomes available.  This function does NOT
        block; it simply schedules the requests respecting IBKR's 100-concurrent limit.
        """
        assert len(symbols) == len(primaryExchanges), "symbols and primaryExchanges must have same length"

        start_time = time.time()
        reset_timeout = 60 # seconds
        for symbol, primary_exchange in zip(symbols, primaryExchanges):
            # wait until working queue has capacity
            while self._working_queue.full():
                now = time.time()
                total_seconds = now - start_time
                if total_seconds > reset_timeout:
                    print(f"Resetting working queue and results dictionary due to timeout after {total_seconds} seconds")
                    self._reset_working_queue_and_results_dict()
                    assert self._working_queue.empty(), "working queue is still not empty after reset"
                else:
                    sleep(0.05)
            # add to working queue
            self._working_queue.put((symbol, primary_exchange))
            start_time = time.time() # reset the start time

        self._working_queue.join()

        results_dict_with_symbol_as_key = {symbol: value for _, (symbol, value) in self._results_dict.items()}
        results_list = [results_dict_with_symbol_as_key[symbol] for symbol in symbols].copy()

        # reset self._results_dict
        with self._results_dict_lock:
            self._results_dict.clear()

        # sort results by original symbols order
        return results_list


    def __async_fetch_last_trade_price_for_symbol(self, symbol: str, primaryExchange: str, future: Future=None) -> Future:
        """
        Never call this method directly since self._results_dict needs to be reset.
        """
        if future is None:
            future = Future()
        # build contract
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        contract.primaryExchange = primaryExchange
        # self.reqMarketDataType(3)  # Request delayed data

        req_id = self.getNextValidId()
        with self._results_dict_lock:
            self._results_dict[req_id] = (symbol, future)
        # request live data; caller can adjust data type outside if desired
        self.reqMktData(req_id, contract, "", False, False, [])


    def tickPrice(self, reqId: int, tickType: int, price: float, attrib: TickAttrib):
        if int(tickType) != 4: # skip other than last close price tick types
            return
        # print(f"Tick price: {reqId} - {tickType} - {price} - {attrib}")
        # resolve corresponding future if present
        with self._results_dict_lock:
            symbol, future = self._results_dict.get(reqId, (None, None))
            assert future is not None and symbol is not None, f"Future or symbol is None for reqId: {reqId}"
            # skip all the reset process if the future is already done
            if future.done():
                return
            future.set_result(float(price))
            # cancel market data subscription to free slot
            self.cancelMktData(reqId)
            print(f"Last trade price for {symbol} is {price} by {reqId}")
            self._working_queue.task_done()
        # No direct queue processing here; the dedicated worker thread will pick up next items
    
    def _reset_working_queue_and_results_dict(self):
        # since the workingQueue has been stucked for a while, we need to loop over the results_dict and set all the futures to be None,
        # and then clear the results_dict and workingQueue
        with self._results_dict_lock:
            for reqId, (_, future) in self._results_dict.items():
                if future is not None and not future.done():
                    future.set_result(None)
                    self.cancelMktData(reqId)
        
        # Clear the working queue by draining all items
        with self._working_queue.mutex:
            self._working_queue.queue.clear()             # Clear all enqueued items
            self._working_queue.all_tasks_done.notify_all()  # Unblock threads waiting on .join()
            self._working_queue.unfinished_tasks = 0      # Reset task counter manually (⚠️ internal)

    def _queue_worker(self):
        """Background loop that dispatches waiting requests while respecting limits."""
        while not self._queue_worker_stop_event.is_set():
            # attempt to move queued requests into working set
            self._process_working_queue()
            # short sleep to prevent busy-wait; tweak as needed for latency/CPU trade-off
            sleep(0.05)

    def _process_working_queue(self):
        """Send as many queued requests as possible up to the concurrency limit."""
        while not self._working_queue.empty():
            symbol, primary_exchange = self._working_queue.get()
            self.__async_fetch_last_trade_price_for_symbol(symbol, primary_exchange)