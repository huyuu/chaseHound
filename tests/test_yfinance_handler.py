import unittest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from typing import List

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "src_python"))

from YfinanceHandler import YfinanceHandler


class TestYfinanceHandler(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.handler = YfinanceHandler()
        # Mock the TradingViewHandler to avoid external dependencies
        self.handler._trading_view_handler = Mock()
        
    def tearDown(self):
        """Clean up after each test method."""
        self.handler.shutdown(wait=True)
        
    def test_fetch_last_traded_price_success(self):
        """Test successful fetching of last traded price for a single symbol."""
        # Mock the history data
        mock_data = pd.DataFrame({
            'close': [150.0, 155.0, 152.0],
            'open': [148.0, 151.0, 154.0],
            'high': [156.0, 158.0, 155.0],
            'low': [147.0, 150.0, 151.0]
        })
        
        with patch.object(self.handler, 'fetch_history_prices_of', return_value=mock_data):
            price = self.handler.fetch_last_traded_price("AAPL")
            self.assertEqual(price, 152.0)
            
    def test_fetch_last_traded_price_no_data(self):
        """Test fetching last traded price when no data is available."""
        with patch.object(self.handler, 'fetch_history_prices_of', return_value=None):
            price = self.handler.fetch_last_traded_price("INVALID")
            self.assertIsNone(price)
            
    def test_fetch_last_traded_price_empty_data(self):
        """Test fetching last traded price when empty data is returned."""
        empty_data = pd.DataFrame()
        with patch.object(self.handler, 'fetch_history_prices_of', return_value=empty_data):
            price = self.handler.fetch_last_traded_price("AAPL")
            self.assertIsNone(price)
            
    def test_fetch_last_traded_price_exception(self):
        """Test handling of exceptions during price fetching."""
        with patch.object(self.handler, 'fetch_history_prices_of', side_effect=Exception("Network error")):
            with patch.object(self.handler, 'log_exception'):
                price = self.handler.fetch_last_traded_price("AAPL")
                self.assertIsNone(price)
                
    def test_async_fetch_last_trade_price_for_symbols(self):
        """Test asynchronous fetching of last traded prices for multiple symbols."""
        symbols = ["AAPL", "GOOGL", "MSFT"]
        expected_prices = [150.0, 2800.0, 300.0]
        
        # Mock the fetch_last_traded_price method to return different prices for each symbol
        def mock_fetch_price(symbol):
            price_map = {"AAPL": 150.0, "GOOGL": 2800.0, "MSFT": 300.0}
            return price_map.get(symbol, None)
            
        with patch.object(self.handler, 'fetch_last_traded_price', side_effect=mock_fetch_price):
            prices = self.handler.async_fetch_last_trade_price_for_symbols(symbols)
            self.assertEqual(prices, expected_prices)
            
    def test_async_fetch_last_trade_price_for_symbols_with_none_values(self):
        """Test asynchronous fetching when some symbols return None."""
        symbols = ["AAPL", "INVALID", "MSFT"]
        expected_prices = [150.0, None, 300.0]
        
        def mock_fetch_price(symbol):
            price_map = {"AAPL": 150.0, "INVALID": None, "MSFT": 300.0}
            return price_map.get(symbol, None)
            
        with patch.object(self.handler, 'fetch_last_traded_price', side_effect=mock_fetch_price):
            prices = self.handler.async_fetch_last_trade_price_for_symbols(symbols)
            self.assertEqual(prices, expected_prices)
            
    def test_fetch_history_prices_of_success(self):
        """Test successful fetching of historical price data."""
        mock_data = pd.DataFrame({
            'close': [150.0, 155.0, 152.0],
            'open': [148.0, 151.0, 154.0],
            'high': [156.0, 158.0, 155.0],
            'low': [147.0, 150.0, 151.0]
        })
        
        self.handler._trading_view_handler.fetch_history_data_of.return_value = mock_data
        
        from_date = datetime.now() - timedelta(days=7)
        to_date = datetime.now()
        
        result = self.handler.fetch_history_prices_of("AAPL", from_date, to_date, "1h")
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3)
        self.handler._trading_view_handler.fetch_history_data_of.assert_called_once()
        
    def test_fetch_history_prices_of_empty_data(self):
        """Test fetching historical prices when empty data is returned."""
        empty_data = pd.DataFrame()
        self.handler._trading_view_handler.fetch_history_data_of.return_value = empty_data
        
        from_date = datetime.now() - timedelta(days=7)
        to_date = datetime.now()
        
        result = self.handler.fetch_history_prices_of("AAPL", from_date, to_date, "1h")
        
        self.assertIsNone(result)
        
    def test_fetch_history_prices_of_exception(self):
        """Test handling of exceptions during historical price fetching."""
        self.handler._trading_view_handler.fetch_history_data_of.side_effect = Exception("API error")
        
        from_date = datetime.now() - timedelta(days=7)
        to_date = datetime.now()
        
        with patch.object(self.handler, 'log_warning'):
            result = self.handler.fetch_history_prices_of("AAPL", from_date, to_date, "1h")
            self.assertIsNone(result)
            
    def test_rewrite_symbol_names_for_yfinance(self):
        """Test symbol name rewriting for yfinance compatibility."""
        # Test BRK.B -> BRK-B conversion
        self.assertEqual(self.handler._rewrite_symbol_names_for_yfinance("BRK.B"), "BRK-B")
        
        # Test BF.B -> BF-B conversion
        self.assertEqual(self.handler._rewrite_symbol_names_for_yfinance("BF.B"), "BF-B")
        
        # Test normal symbol remains unchanged
        self.assertEqual(self.handler._rewrite_symbol_names_for_yfinance("AAPL"), "AAPL")
        
        # Test another normal symbol
        self.assertEqual(self.handler._rewrite_symbol_names_for_yfinance("GOOGL"), "GOOGL")
        
    def test_integration_with_real_data(self):
        """Integration test with a known symbol (this requires network access)."""
        # Skip this test in CI/CD environments or when network is unavailable
        # This test is commented out to avoid dependencies on external services
        # Uncomment and run manually to test real integration
        
        # handler = YfinanceHandler()
        # try:
        #     price = handler.fetch_last_traded_price("AAPL")
        #     self.assertIsNotNone(price)
        #     self.assertIsInstance(price, (int, float))
        #     self.assertGreater(price, 0)
        # except Exception as e:
        #     self.skipTest(f"Integration test skipped due to network/API issue: {e}")
        # finally:
        #     handler.shutdown()
        
        pass
        
    def test_performance_comparison(self):
        """Test that demonstrates the performance difference between sync and async methods."""
        # This test replicates the performance comparison from the original experiment
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        
        # Mock fetch_last_traded_price to simulate processing time
        def mock_fetch_price(symbol):
            import time
            time.sleep(0.01)  # Simulate small delay
            return 100.0 + len(symbol)  # Return a mock price
            
        with patch.object(self.handler, 'fetch_last_traded_price', side_effect=mock_fetch_price):
            import time
            
            # Test async method
            start_time = time.time()
            async_prices = self.handler.async_fetch_last_trade_price_for_symbols(symbols)
            async_time = time.time() - start_time
            
            # Test sync method (sequential)
            start_time = time.time()
            sync_prices = []
            for symbol in symbols:
                sync_prices.append(self.handler.fetch_last_traded_price(symbol))
            sync_time = time.time() - start_time
            
            # Assert that async is faster (allowing for some overhead)
            self.assertLess(async_time, sync_time * 0.8)
            
            # Assert that results are the same
            self.assertEqual(async_prices, sync_prices)
            
    def test_shutdown_method(self):
        """Test the shutdown method properly cleans up resources."""
        # Create a new handler for this test
        handler = YfinanceHandler()
        
        # Mock the thread pool executor
        handler._thread_pool_executor = Mock()
        
        # Test shutdown with wait=False (default)
        handler.shutdown()
        handler._thread_pool_executor.shutdown.assert_called_once_with(wait=False)
        
        # Test shutdown with wait=True
        handler._thread_pool_executor.reset_mock()
        handler.shutdown(wait=True)
        handler._thread_pool_executor.shutdown.assert_called_once_with(wait=True)


if __name__ == '__main__':
    unittest.main() 