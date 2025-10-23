"""
Overcast Client
Core SDK functionality for sending logs to Overcast incident detection.
"""

import json
import traceback
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

from .exceptions import OvercastError, OvercastAuthError, OvercastConnectionError, OvercastValidationError


class OvercastClient:
    """
    Overcast SDK Client
    
    Simple client for sending logs to Overcast for automated incident detection.
    Supports automatic stack trace extraction and structured logging.
    
    Example:
        overcast = OvercastClient(api_key="your_key")
        overcast.error("Database timeout occurred")
        
        # With metadata
        overcast.error("Payment failed", service="billing", user_id=12345)
        
        # Automatic exception capture
        try:
            risky_operation()
        except Exception as e:
            overcast.exception("Operation failed", exception=e)
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.overcast.com",
        service: Optional[str] = None,
        timeout: int = 30,
        debug: bool = False
    ):
        """
        Initialize Overcast client.
        
        Args:
            api_key: Your Overcast API key
            base_url: Overcast API base URL (defaults to production)
            service: Default service name for all logs (can be overridden per log)
            timeout: Request timeout in seconds
            debug: Enable debug logging
        """
        if not api_key or not api_key.strip():
            raise OvercastValidationError("API key is required")
            
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip('/')
        self.default_service = service
        self.timeout = timeout
        self.debug = debug
        self._session = requests.Session()
        
        # Set default headers
        self._session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': f'overcast-python-sdk/1.0.0'
        })

    def _log(self, level: str, message: str, **kwargs) -> bool:
        """
        Internal method to send log to Overcast.
        
        Args:
            level: Log level (ERROR, WARNING, INFO, DEBUG)
            message: Log message
            **kwargs: Additional metadata (service, user_id, etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Extract service name
            service = kwargs.pop('service', None) or self.default_service
            
            # Handle exception parameter for automatic stack trace
            exception = kwargs.pop('exception', None)
            if exception and isinstance(exception, BaseException):
                # Extract stack trace
                tb_str = ''.join(traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                ))
                message = f"{message}\n\nStack trace:\n{tb_str}"
                kwargs['exception_type'] = type(exception).__name__
                kwargs['exception_message'] = str(exception)

            # Build log entry
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": level.upper(),
                "message": message,
                "service": service,
                "raw_log": message,
                "metadata": {
                    "sdk": "python",
                    "sdk_version": "1.0.0",
                    **kwargs
                }
            }
            
            # Build request payload
            payload = {
                "api_key": self.api_key,
                "source_type": "python_sdk",
                "source_description": f"Python SDK - {service or 'application'}",
                "logs": [log_entry]
            }
            
            if self.debug:
                print(f"[Overcast SDK] Sending log: {level} - {message[:100]}...")
                
            # Send to Overcast
            response = self._session.post(
                f"{self.base_url}/api/v1/ingest/logs",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 401:
                raise OvercastAuthError("Invalid API key - check your Overcast API key")
            elif response.status_code == 422:
                raise OvercastValidationError(f"Request validation failed: {response.text}")
            elif not response.ok:
                raise OvercastConnectionError(f"HTTP {response.status_code}: {response.text}")
                
            if self.debug:
                result = response.json()
                print(f"[Overcast SDK] Success: {result.get('incidents_detected', 0)} incidents detected")
                
            return True
            
        except (ConnectionError, Timeout) as e:
            if self.debug:
                print(f"[Overcast SDK] Connection error: {e}")
            raise OvercastConnectionError(f"Failed to connect to Overcast: {e}")
        except RequestException as e:
            if self.debug:
                print(f"[Overcast SDK] Request error: {e}")
            raise OvercastConnectionError(f"Request failed: {e}")
        except Exception as e:
            if self.debug:
                print(f"[Overcast SDK] Unexpected error: {e}")
            raise OvercastError(f"Unexpected error: {e}")

    def error(self, message: str, **kwargs) -> bool:
        """
        Log an ERROR level message.
        
        Args:
            message: Error message
            **kwargs: Additional metadata (service, user_id, request_id, etc.)
            
        Returns:
            bool: True if successful
            
        Example:
            overcast.error("Database connection failed", service="auth", user_id=123)
        """
        return self._log("ERROR", message, **kwargs)

    def warning(self, message: str, **kwargs) -> bool:
        """
        Log a WARNING level message.
        
        Args:
            message: Warning message
            **kwargs: Additional metadata
            
        Returns:
            bool: True if successful
        """
        return self._log("WARNING", message, **kwargs)

    def info(self, message: str, **kwargs) -> bool:
        """
        Log an INFO level message.
        
        Args:
            message: Info message
            **kwargs: Additional metadata
            
        Returns:
            bool: True if successful
        """
        return self._log("INFO", message, **kwargs)

    def debug(self, message: str, **kwargs) -> bool:
        """
        Log a DEBUG level message.
        
        Args:
            message: Debug message
            **kwargs: Additional metadata
            
        Returns:
            bool: True if successful
        """
        return self._log("DEBUG", message, **kwargs)

    def exception(self, message: str, exception: Optional[BaseException] = None, **kwargs) -> bool:
        """
        Log an exception with automatic stack trace capture.
        
        Args:
            message: Error message
            exception: Exception object (if None, captures current exception)
            **kwargs: Additional metadata
            
        Returns:
            bool: True if successful
            
        Example:
            try:
                dangerous_operation()
            except Exception as e:
                overcast.exception("Operation failed", exception=e, user_id=123)
                
            # Or capture current exception automatically
            try:
                dangerous_operation()
            except Exception:
                overcast.exception("Operation failed", user_id=123)
        """
        if exception is None:
            # Capture current exception from sys.exc_info()
            exc_type, exc_value, exc_traceback = sys.exc_info()
            if exc_value:
                exception = exc_value
                
        return self._log("ERROR", message, exception=exception, **kwargs)

    def close(self):
        """Close the underlying HTTP session."""
        if self._session:
            self._session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
