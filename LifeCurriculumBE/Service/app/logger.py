"""
Logging configuration for LifeCurriculum service
Provides centralized logging with EST timestamps and file information
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import pytz


class ESTFormatter(logging.Formatter):
    """Custom formatter that converts timestamps to EST"""
    
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(fmt, datefmt)
        self.est_tz = pytz.timezone('US/Eastern')
    
    def formatTime(self, record, datefmt=None):
        """Override formatTime to use EST timezone"""
        dt = datetime.fromtimestamp(record.created, tz=self.est_tz)
        if datefmt:
            return dt.strftime(datefmt)
        else:
            return dt.strftime('%Y-%m-%d %H:%M:%S %Z')


class LifeCurriculumLogger:
    """Central logger configuration for the LifeCurriculum service"""
    
    _loggers = {}
    _configured = False
    
    @classmethod
    def setup_logging(cls, log_level: str = "INFO", log_file: Optional[str] = None):
        """
        Setup the base logging configuration
        
        Args:
            log_level: The logging level (DEBUG, INFO, WARN, ERROR)
            log_file: Optional file path to write logs to
        """
        if cls._configured:
            return
            
        # Convert string log level to logging constant
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Create custom formatter with EST timezone and file information
        formatter = ESTFormatter(
            fmt='%(asctime)s | %(levelname)-5s | %(filename)s:%(lineno)d | %(funcName)s() | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S %Z'
        )
        
        # Setup console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)
        root_logger.addHandler(console_handler)
        
        # Setup file handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        # Disable propagation for third-party loggers to reduce noise
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("fastapi").setLevel(logging.WARNING)
        
        cls._configured = True
    
    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        """
        Get a logger instance for a specific module
        
        Args:
            name: Name of the logger (typically __name__ of the calling module)
            
        Returns:
            logging.Logger: Configured logger instance
        """
        if not cls._configured:
            cls.setup_logging()
        
        if name is None:
            return logging.getLogger()
        
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        
        return cls._loggers[name]
    
    @classmethod
    def set_level(cls, level: str):
        """
        Change the logging level for all loggers
        
        Args:
            level: New logging level (DEBUG, INFO, WARN, ERROR)
        """
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        
        # Update root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)
        
        # Update all handlers
        for handler in root_logger.handlers:
            handler.setLevel(numeric_level)
        
        # Update all cached loggers
        for logger in cls._loggers.values():
            logger.setLevel(numeric_level)


# Convenience functions for easy import and use
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance
    
    Args:
        name: Name of the logger (typically __name__ of the calling module)
        
    Returns:
        logging.Logger: Configured logger instance
    
    Example:
        from app.logger import get_logger
        
        logger = get_logger(__name__)
        logger.info("This is an info message")
        logger.warning("This is a warning message")
        logger.error("This is an error message")
        logger.debug("This is a debug message")
    """
    return LifeCurriculumLogger.get_logger(name)


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """
    Setup the base logging configuration
    
    Args:
        log_level: The logging level (DEBUG, INFO, WARN, ERROR)
        log_file: Optional file path to write logs to
    """
    LifeCurriculumLogger.setup_logging(log_level, log_file)


def set_log_level(level: str):
    """
    Change the logging level
    
    Args:
        level: New logging level (DEBUG, INFO, WARN, ERROR)
    """
    LifeCurriculumLogger.set_level(level)
