"""
Custom exceptions for universal-api-connector.

All exceptions follow Python naming conventions (PascalCase for classes).
"""


class ConnectorError(Exception):
    """Base exception for all connector errors."""
    pass


class ConfigurationError(ConnectorError):
    """Raised when configuration is invalid."""
    pass


class ConnectionError(ConnectorError):
    """Raised when connection to API fails."""
    pass


class RequestError(ConnectorError):
    """Raised when API request fails."""
    pass


class ValidationError(ConnectorError):
    """Raised when data validation fails."""
    pass


class TimeoutError(ConnectorError):
    """Raised when request times out."""
    pass