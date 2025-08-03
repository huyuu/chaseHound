import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(project_root, "submodules", "LLMTrader"))

import logging
import traceback
from datetime import datetime
from pathlib import Path
import pytz

class ChaseHoundBase:

    # MARK: - Class Properties
    project_root: str = os.path.dirname(os.path.dirname(__file__))
    temp_folder: str = os.path.join(project_root, "temp")
    # set absolute current time and date in eastern timezone
    eastern = pytz.timezone('America/New_York')  # GMT-5 timezone
    absolute_current_datetime_in_eastern_cls = datetime.now(eastern).replace(tzinfo=None)
    absolute_current_date_in_eastern_cls = datetime(
        year=absolute_current_datetime_in_eastern_cls.year, 
        month=absolute_current_datetime_in_eastern_cls.month, 
        day=absolute_current_datetime_in_eastern_cls.day
    )
    # set absolute current time and date in UTC timezone
    absolute_current_datetime_in_utc_cls = datetime.now(pytz.utc).replace(tzinfo=None)
    absolute_current_date_in_utc_cls = datetime(
        year=absolute_current_datetime_in_utc_cls.year, 
        month=absolute_current_datetime_in_utc_cls.month, 
        day=absolute_current_datetime_in_utc_cls.day
    )
    # set absolute current time and date in JPT timezone
    absolute_current_datetime_in_jpt_cls = datetime.now(pytz.timezone('Asia/Tokyo')).replace(tzinfo=None)
    absolute_current_date_in_jpt_cls = datetime(
        year=absolute_current_datetime_in_jpt_cls.year, 
        month=absolute_current_datetime_in_jpt_cls.month, 
        day=absolute_current_datetime_in_jpt_cls.day
    )
    # set common properties
    green_color_code = "\033[92m"
    red_color_code = "\033[91m"
    yellow_color_code = "\033[93m"
    reset_color_code = "\033[0m"

    @property
    def absolute_current_datetime_in_eastern(self):
        return ChaseHoundBase.absolute_current_datetime_in_eastern_cls

    @property
    def absolute_current_date_in_eastern(self):
        return ChaseHoundBase.absolute_current_date_in_eastern_cls

    @property
    def absolute_current_datetime_in_utc(self):
        return ChaseHoundBase.absolute_current_datetime_in_utc_cls

    @property
    def absolute_current_datetime_in_utc(self):
        return ChaseHoundBase.absolute_current_datetime_in_utc_cls
    
    @property
    def absolute_current_date_in_jpt(self):
        return ChaseHoundBase.absolute_current_date_in_jpt_cls

    @property
    def latest_absolute_current_time_in_eastern(self):
        return datetime.now(ChaseHoundBase.eastern).replace(tzinfo=None)

    @property
    def latest_absolute_current_time_in_utc(self):
        return datetime.now(pytz.utc).replace(tzinfo=None)

    @property
    def latest_absolute_current_time_in_jpt(self):
        return datetime.now(pytz.timezone('Asia/Tokyo')).replace(tzinfo=None)

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
            
    
    
