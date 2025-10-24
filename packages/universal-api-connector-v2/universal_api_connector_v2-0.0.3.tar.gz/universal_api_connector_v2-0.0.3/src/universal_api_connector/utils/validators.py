"""
Validation utilities for configuration parameters.

All functions follow Python naming conventions (snake_case).
"""

from urllib.parse import urlparse
from ..exceptions import ValidationError


def validate_url(url: str) -> bool:
    """
    Validate if string is a proper URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If URL is invalid
        
    Example:
        >>> validate_url('https://api.example.com')
        True
    """
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValidationError(f"Invalid URL format: {url}")
        if result.scheme not in ['http', 'https']:
            raise ValidationError(f"URL must use http or https: {url}")
        return True
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(f"URL validation failed: {str(e)}")


def validate_timeout(timeout: int) -> bool:
    """
    Validate timeout value.
    
    Args:
        timeout: Timeout in seconds
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If timeout is invalid
        
    Example:
        >>> validate_timeout(30)
        True
    """
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValidationError(
            f"Timeout must be a positive number, got: {timeout}"
        )
    return True