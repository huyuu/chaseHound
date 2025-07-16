#!/usr/bin/env python3

"""
Example script demonstrating the logging system in ChaseHoundBase.
This shows how all classes inherit logging capabilities and how errors are automatically logged with full call stacks.
"""

import sys
import os
# Add src_python to the path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src_python'))

from ChaseHoundBase import ChaseHoundBase
from YfinanceHandler import YfinanceHandler

class ExampleClass(ChaseHoundBase):
    def __init__(self):
        super().__init__()
        
    def method_that_logs_info(self):
        self.logger.info("This is an info message")
        self.logger.warning("This is a warning message")
        
    def method_that_logs_warnings(self):
        """Demonstrates the new log_warning method."""
        self.logger.info("Demonstrating warning logging methods")
        
        # Basic warning without stack trace
        self.log_warning("This is a non-fatal warning without stack trace")
        
        # Warning with stack trace for more detailed debugging
        self.log_warning("This is a non-fatal warning with stack trace", include_stack=True)
        
        # Example of a realistic warning scenario
        deprecated_value = "old_format"
        if deprecated_value == "old_format":
            self.log_warning("Using deprecated format, consider updating to new format")
        
    def method_that_causes_error(self):
        """This method will cause an error to demonstrate stack trace logging."""
        self.logger.info("About to cause an error for demonstration")
        try:
            # This will cause a division by zero error
            result = 1 / 0
        except Exception as e:
            # Using the new logging method that captures full call stack
            self.log_exception("Demonstration error occurred", e)
            # Re-raise if needed
            raise

    def method_with_nested_calls(self):
        """Demonstrates how call stacks work with nested method calls."""
        self.logger.info("Starting nested call demonstration")
        self._nested_method_level_1()
        
    def _nested_method_level_1(self):
        self.logger.info("In nested method level 1")
        self._nested_method_level_2()
        
    def _nested_method_level_2(self):
        self.logger.info("In nested method level 2")
        try:
            # This will cause an error deep in the call stack
            undefined_variable.some_method()
        except Exception as e:
            self.log_exception("Error in deeply nested method", e)
            raise

if __name__ == "__main__":
    print("=== ChaseHound Logging System Demo ===")
    
    # Create an instance of our example class
    example = ExampleClass()
    
    # Demonstrate basic logging
    print("\n1. Basic logging messages:")
    example.method_that_logs_info()
    
    # Demonstrate warning logging
    print("\n2. Warning logging with optional stack traces:")
    example.method_that_logs_warnings()
    
    # Demonstrate error logging with stack trace
    print("\n3. Error logging with stack trace:")
    try:
        example.method_that_causes_error()
    except Exception:
        print("Error was logged with full stack trace")
    
    # Demonstrate nested call stack logging
    print("\n4. Nested call stack logging:")
    try:
        example.method_with_nested_calls()
    except Exception:
        print("Nested error was logged with full call stack")
    
    # Demonstrate with YfinanceHandler
    print("\n5. YfinanceHandler logging example:")
    handler = YfinanceHandler()
    try:
        # This will likely fail since we don't have the actual TradingViewHandler
        handler.fetch_last_traded_price("AAPL")
    except Exception:
        print("YfinanceHandler error was logged with full stack trace")
    
    print("\n=== Demo Complete ===")
    print("Check the 'logs' directory for detailed log files.") 