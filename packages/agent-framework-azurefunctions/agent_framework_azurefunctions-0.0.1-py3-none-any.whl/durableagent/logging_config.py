"""
Logging configuration for Azure Durable Agent Function App

This module provides proper logging setup for Azure Functions environment.
Azure Functions has its own logging infrastructure, so we need to configure
our loggers to work properly with it.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    logger_name: str = "durableagent"
) -> logging.Logger:
    """
    Configure logging for the durable agent function app.

    This function sets up logging to work properly with Azure Functions Core Tools
    and Azure Functions runtime. It ensures logs are visible in both local development
    and when deployed to Azure.

    Args:
        level: Logging level (default: logging.INFO)
        format_string: Optional custom format string for log messages
        logger_name: Name of the logger to configure (default: "durableagent")

    Returns:
        Configured logger instance

    Usage:
        ```python
        from durableagent.logging_config import setup_logging
        
        # At module level or app initialization
        logger = setup_logging()
        
        # Or with custom settings
        logger = setup_logging(
            level=logging.DEBUG,
            format_string='[%(levelname)s] %(name)s: %(message)s'
        )
        ```
    """
    if format_string is None:
        format_string = '[%(asctime)s] [%(name)s] %(levelname)s: %(message)s'
    
    # Get or create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Create console handler for stdout (Azure Functions uses stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Set encoding to UTF-8 to handle emoji characters on Windows
    if hasattr(console_handler.stream, 'reconfigure'):
        try:
            console_handler.stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            # If reconfigure fails, continue without it
            pass
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    # Ensure logs propagate to root logger (Azure Functions can capture them)
    logger.propagate = True
    
    return logger


def configure_module_loggers(level: int = logging.INFO) -> None:
    """
    Configure loggers for all durableagent modules.

    This ensures consistent logging across all modules in the package.

    Args:
        level: Logging level to set for all modules
    """
    module_names = [
        "durableagent",
        "durableagent.app",
        "durableagent.entities",
        "durableagent.models",
    ]
    
    for module_name in module_names:
        logger = logging.getLogger(module_name)
        logger.setLevel(level)
        
        # Ensure at least one handler exists
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(level)
            formatter = logging.Formatter('[%(name)s] %(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a logger instance with proper configuration.
    
    This is a convenience function for getting loggers in individual modules.
    
    Args:
        name: Logger name (typically __name__ from the calling module)
        level: Logging level (default: logging.INFO)
    
    Returns:
        Configured logger instance
    
    Usage:
        ```python
        from durableagent.logging_config import get_logger

        logger = get_logger(__name__)
        logger.info("This will be visible in Azure Functions logs")
        ```
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # If no handlers exist, add a console handler
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter('[%(name)s] %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


# Initialize logging when module is imported
_root_logger = setup_logging()
