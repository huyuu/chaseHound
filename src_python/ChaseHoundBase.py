import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(project_root, "submodules", "LLMTrader"))

import logging
import traceback
from datetime import datetime
from pathlib import Path

class ChaseHoundBase:

    # MARK: - Class Properties
    project_root: str = os.path.dirname(os.path.dirname(__file__))

    # MARK: - Constructor
    def __init__(self):
        self.logger = self._setup_logger()
        # Set up exception hook to log unhandled exceptions with full stack trace
        sys.excepthook = self._log_unhandled_exception

    # MARK: - Private Methods
    
    def _setup_logger(self) -> logging.Logger:
        """Set up a logger instance with file and console handlers."""
        logger_name = self.__class__.__name__
        logger = logging.getLogger(logger_name)
        
        # Avoid adding handlers multiple times
        if logger.handlers:
            return logger
            
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = Path(self.project_root) / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        # File handler for all logs
        log_file = log_dir / f"{datetime.now().strftime('%Y%m%d')}_chasehound.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Console handler for info and above
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('%(levelname)s - %(name)s - %(message)s'))
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _log_unhandled_exception(self, exc_type, exc_value, exc_traceback):
        """Log unhandled exceptions with full stack trace."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't log KeyboardInterrupt
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        logger = logging.getLogger(self.__class__.__name__)
        logger.critical(
            "Unhandled exception occurred",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        
    def log_error_with_stack(self, message: str, exception: Exception = None):
        """Log an error message with full call stack trace."""
        if exception:
            self.logger.error(f"{message}: {str(exception)}")
            self.logger.error(f"Exception type: {type(exception).__name__}")
            self.logger.error(f"Full traceback:\n{traceback.format_exc()}")
        else:
            self.logger.error(message)
            self.logger.error(f"Call stack:\n{''.join(traceback.format_stack())}")
            
    def log_exception(self, message: str, exception: Exception):
        """Convenience method to log exceptions with stack trace."""
        self.log_error_with_stack(message, exception)
        
    def log_warning(self, message: str, include_stack: bool = False):
        """Log a warning message with optional call stack trace for non-fatal issues."""
        self.logger.warning(message)
        if include_stack:
            self.logger.warning(f"Call stack:\n{''.join(traceback.format_stack())}")
            
    
    
