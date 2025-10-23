"""
Azure Durable Agent Function App

This package provides integration between Microsoft Agent Framework and Azure Durable Functions,
enabling durable, stateful AI agents deployed as Azure Function Apps.
"""

# Configure logging before importing other modules
from .logging_config import setup_logging, configure_module_loggers

# Setup logging for the package
setup_logging()
configure_module_loggers()

from .app import AgentFunctionApp
from .orchestration import DurableAIAgent, get_agent

__all__ = [
    "AgentFunctionApp",
    "DurableAIAgent",
    "get_agent",
]
__version__ = "0.1.0"
