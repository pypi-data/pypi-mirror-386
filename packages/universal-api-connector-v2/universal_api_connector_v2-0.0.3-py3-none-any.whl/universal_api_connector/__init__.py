"""
Universal API Connector

A minimal Python package for connecting to any REST API.
Users provide their own authentication logic - nothing is hardcoded.

Key Features:
- Minimal and focused
- Works with any REST API
- User-provided authentication
- Proper error handling
- Clean Python naming conventions

Example:
    >>> from universal_api_connector import APIConnector
    >>> 
    >>> connector = APIConnector(
    ...     base_url='https://api.example.com',
    ...     headers={'Authorization': 'Bearer token'}
    ... )
    >>> 
    >>> with connector:
    ...     data = connector.get('/users')
"""

from .connector import APIConnector
from .exceptions import (
    ConnectorError,
    ConfigurationError,
    ConnectionError,
    RequestError,
    ValidationError,
    TimeoutError
)

__version__ = '0.0.1'
__author__ = 'Logesh'
__all__ = [
    'APIConnector',
    'ConnectorError',
    'ConfigurationError',
    'ConnectionError',
    'RequestError',
    'ValidationError',
    'TimeoutError'
]