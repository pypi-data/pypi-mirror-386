"""
Universal API Connector - Minimal implementation.

This connector handles HTTP requests to any REST API.
Users provide their own authentication logic.

All class and method names follow Python naming conventions:
- Classes: PascalCase
- Methods/Functions: snake_case
- Constants: UPPER_SNAKE_CASE
"""

import requests
from typing import Dict, Any, Optional, Union, Callable
from .exceptions import ConnectionError, RequestError, TimeoutError
from .utils.logger import setup_logger
from .utils.validators import validate_url, validate_timeout


class APIConnector:
    """
    Universal connector for any REST API.
    
    This connector handles HTTP requests. Users provide their own
    authentication through headers or an auth_handler function.
    
    Attributes:
        base_url: Base URL of the API
        session: Requests session for connection pooling
        default_headers: Headers to include in all requests
        timeout: Default request timeout in seconds
        verify_ssl: Whether to verify SSL certificates
        proxies: Proxy configuration
        
    Example with static headers:
        >>> connector = APIConnector(
        ...     base_url='https://api.example.com',
        ...     headers={'Authorization': 'Bearer token'}
        ... )
        >>> data = connector.get('/users')
        
    Example with auth handler:
        >>> def get_auth_headers():
        ...     return {'Authorization': 'Bearer my-token'}
        >>> 
        >>> connector = APIConnector(
        ...     base_url='https://api.example.com',
        ...     auth_handler=get_auth_headers
        ... )
        >>> data = connector.get('/users')
    """
    
    def __init__(
        self,
        base_url: str,
        auth_handler: Optional[Callable[[], Dict[str, str]]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        verify_ssl: bool = True,
        proxies: Optional[Dict[str, str]] = None,
        log_level: str = "INFO",
        log_file: Optional[str] = None
    ):
        """
        Initialize the API connector.
        
        Args:
            base_url: Base URL of the API (required)
            auth_handler: Optional function that returns auth headers
            headers: Static headers to include in all requests
            timeout: Request timeout in seconds (default: 30)
            verify_ssl: Verify SSL certificates (default: True)
            proxies: Proxy configuration dict
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path
            
        Raises:
            ValidationError: If base_url is invalid
        """
        self.logger = setup_logger(__name__, level=log_level, log_file=log_file)
        self.logger.info("Initializing APIConnector")
        
        # Validate and set base URL
        validate_url(base_url)
        self.base_url = base_url.rstrip('/')
        
        # Validate timeout
        validate_timeout(timeout)
        self.timeout = timeout
        
        # Set authentication handler
        self._auth_handler = auth_handler
        
        # Set other attributes
        self.default_headers = headers or {}
        self.verify_ssl = verify_ssl
        self.proxies = proxies
        
        # Create session for connection pooling
        self.session = requests.Session()
        
        self.logger.info(f"APIConnector initialized for {self.base_url}")
    
    def _build_url(self, endpoint: str) -> str:
        """
        Build complete URL from base URL and endpoint.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Complete URL string
        """
        endpoint = endpoint.lstrip('/')
        return f"{self.base_url}/{endpoint}"
    
    def _get_headers(
        self,
        additional_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Get headers including auth and additional headers.
        
        Args:
            additional_headers: Headers specific to this request
            
        Returns:
            Complete headers dictionary
        """
        headers = self.default_headers.copy()
        
        # Add authentication headers if handler provided
        if self._auth_handler:
            try:
                auth_headers = self._auth_handler()
                if auth_headers:
                    headers.update(auth_headers)
            except Exception as e:
                self.logger.error(f"Auth handler failed: {e}")
                raise
        
        # Add request-specific headers
        if additional_headers:
            headers.update(additional_headers)
        
        return headers
    
    def _handle_response(
        self,
        response: requests.Response
    ) -> Union[Dict, str, bytes]:
        """
        Handle API response based on content type.
        
        Args:
            response: Response object from requests
            
        Returns:
            Parsed response data (JSON dict, text, or bytes)
            
        Raises:
            RequestError: If response indicates an error
        """
        try:
            response.raise_for_status()
            
            content_type = response.headers.get('Content-Type', '')
            
            # Parse based on content type
            if 'application/json' in content_type:
                return response.json()
            elif 'text/' in content_type:
                return response.text
            else:
                return response.content
                
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP Error: {e}")
            raise RequestError(
                f"Request failed with status {response.status_code}: {response.text}"
            )
    
    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Union[Dict, str, bytes]:
        """
        Make HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH, etc.)
            endpoint: API endpoint path
            params: URL query parameters
            data: Request body data
            json: JSON request body
            headers: Additional headers for this request
            timeout: Custom timeout for this request (seconds)
            **kwargs: Additional arguments passed to requests
            
        Returns:
            Response data (parsed JSON, text, or bytes)
            
        Raises:
            ConnectionError: If connection fails
            RequestError: If request fails
            TimeoutError: If request times out
            
        Example:
            >>> connector.request('GET', '/users', params={'page': 1})
            >>> connector.request('POST', '/users', json={'name': 'John'})
        """
        url = self._build_url(endpoint)
        headers = self._get_headers(headers)
        timeout = timeout or self.timeout
        
        self.logger.debug(f"Making {method} request to {url}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json,
                headers=headers,
                timeout=timeout,
                verify=self.verify_ssl,
                proxies=self.proxies,
                **kwargs
            )
            
            return self._handle_response(response)
            
        except requests.exceptions.Timeout:
            self.logger.error(f"Request timed out after {timeout}s")
            raise TimeoutError(
                f"Request to {url} timed out after {timeout} seconds"
            )
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection failed: {e}")
            raise ConnectionError(f"Failed to connect to {url}: {str(e)}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise RequestError(f"Request failed: {str(e)}")
    
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Union[Dict, str, bytes]:
        """
        Make GET request.
        
        Args:
            endpoint: API endpoint path
            params: URL query parameters
            **kwargs: Additional arguments
            
        Returns:
            Response data
            
        Example:
            >>> data = connector.get('/users', params={'status': 'active'})
        """
        return self.request('GET', endpoint, params=params, **kwargs)
    
    def post(
        self,
        endpoint: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Union[Dict, str, bytes]:
        """
        Make POST request.
        
        Args:
            endpoint: API endpoint path
            data: Request body data
            json: JSON request body
            **kwargs: Additional arguments
            
        Returns:
            Response data
            
        Example:
            >>> new_user = connector.post('/users', json={'name': 'John'})
        """
        return self.request('POST', endpoint, data=data, json=json, **kwargs)
    
    def put(
        self,
        endpoint: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Union[Dict, str, bytes]:
        """
        Make PUT request.
        
        Args:
            endpoint: API endpoint path
            data: Request body data
            json: JSON request body
            **kwargs: Additional arguments
            
        Returns:
            Response data
            
        Example:
            >>> updated = connector.put('/users/123', json={'name': 'Jane'})
        """
        return self.request('PUT', endpoint, data=data, json=json, **kwargs)
    
    def patch(
        self,
        endpoint: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Union[Dict, str, bytes]:
        """
        Make PATCH request.
        
        Args:
            endpoint: API endpoint path
            data: Request body data
            json: JSON request body
            **kwargs: Additional arguments
            
        Returns:
            Response data
            
        Example:
            >>> patched = connector.patch('/users/123', json={'email': 'new@email.com'})
        """
        return self.request('PATCH', endpoint, data=data, json=json, **kwargs)
    
    def delete(
        self,
        endpoint: str,
        **kwargs
    ) -> Union[Dict, str, bytes]:
        """
        Make DELETE request.
        
        Args:
            endpoint: API endpoint path
            **kwargs: Additional arguments
            
        Returns:
            Response data
            
        Example:
            >>> connector.delete('/users/123')
        """
        return self.request('DELETE', endpoint, **kwargs)
    
    def close(self) -> None:
        """
        Close the session and clean up resources.
        
        Should be called when done using the connector,
        or use the connector as a context manager.
        """
        self.session.close()
        self.logger.info("APIConnector closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __repr__(self) -> str:
        """String representation of connector."""
        return f"APIConnector(base_url='{self.base_url}')"