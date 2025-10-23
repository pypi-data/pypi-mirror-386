"""
Overcast SDK for Python
Simple incident detection and monitoring for your applications.

Usage:
    from overcast import Overcast
    
    overcast = Overcast(api_key="your_api_key")
    overcast.error("Database connection failed", service="user-service")
"""

from .client import OvercastClient
from .exceptions import OvercastError, OvercastAuthError, OvercastConnectionError

__version__ = "1.0.0"
__all__ = ["OvercastClient", "OvercastError", "OvercastAuthError", "OvercastConnectionError"]

# Convenience alias for cleaner imports
Overcast = OvercastClient
