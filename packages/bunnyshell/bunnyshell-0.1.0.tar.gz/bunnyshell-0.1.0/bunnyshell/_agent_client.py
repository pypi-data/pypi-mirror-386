"""HTTP client for agent operations with retry logic."""

import time
import logging
from typing import Optional, Dict, Any
import httpx
from .errors import (
    FileNotFoundError,
    FileOperationError,
    CodeExecutionError,
    CommandExecutionError,
    DesktopNotAvailableError,
    AgentError,
    NetworkError,
    TimeoutError as BunnyshellTimeoutError,
)

logger = logging.getLogger(__name__)


class AgentHTTPClient:
    """
    HTTP client for agent operations with retry logic and error handling.
    
    Features:
    - Connection pooling (reuses TCP connections)
    - Automatic retries with exponential backoff
    - Proper error wrapping to Bunnyshell exceptions
    - Configurable timeouts
    """
    
    def __init__(
        self,
        agent_url: str,
        *,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize agent HTTP client.
        
        Args:
            agent_url: Agent base URL (e.g., https://7777-{id}.domain)
            timeout: Default timeout in seconds
            max_retries: Maximum retry attempts
        """
        self._agent_url = agent_url.rstrip('/')
        self._timeout = timeout
        self._max_retries = max_retries
        
        # Create reusable HTTP client with connection pooling
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
        
        logger.debug(f"Agent client initialized: {self._agent_url}")
    
    def _should_retry(self, status_code: int) -> bool:
        """Check if request should be retried based on status code."""
        return status_code in {429, 500, 502, 503, 504}
    
    def _get_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff."""
        return min(2 ** attempt, 10)  # Max 10 seconds
    
    def _wrap_error(
        self,
        error: Exception,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentError:
        """
        Wrap httpx errors into Bunnyshell exceptions.
        
        Uses Agent v3.1.1+ error codes for precise exception mapping:
        - FILE_NOT_FOUND -> FileNotFoundError
        - PATH_NOT_ALLOWED -> FileOperationError
        - EXECUTION_FAILED/TIMEOUT -> CodeExecutionError
        - COMMAND_FAILED -> CommandExecutionError
        - DESKTOP_NOT_AVAILABLE -> DesktopNotAvailableError
        
        Falls back to HTTP status code + context for older agents.
        """
        context = context or {}
        
        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code
            # Extract request ID from response headers (case-insensitive)
            request_id = (
                error.response.headers.get("X-Request-ID") or
                error.response.headers.get("x-request-id") or
                error.response.headers.get("X-Request-Id")
            )
            
            # Try to get error message, code, and details from response (Agent v3.1.1+)
            error_code = None
            error_details = {}
            try:
                error_data = error.response.json()
                message = error_data.get("error", error_data.get("message", str(error)))
                error_code = error_data.get("code")  # Machine-readable error code (v3.1.1+)
                error_details = error_data.get("details", {})
            except:
                message = f"HTTP {status_code}: {error.response.text[:100]}"
            
            # Map error codes to specific exceptions (Agent v3.1.1+)
            # Note: Agent returns UPPERCASE error codes (e.g., "FILE_NOT_FOUND")
            if error_code:
                # File-related errors
                if error_code == "FILE_NOT_FOUND":
                    return FileNotFoundError(
                        message=message,
                        path=error_details.get("path") or context.get("path"),
                        request_id=request_id,
                        code=error_code
                    )
                
                if error_code == "PATH_NOT_ALLOWED":
                    return FileOperationError(
                        message=message,
                        operation=operation,
                        request_id=request_id,
                        code=error_code
                    )
                
                if error_code in ("DIRECTORY_NOT_FOUND", "INVALID_PATH", "FILE_ALREADY_EXISTS"):
                    return FileOperationError(
                        message=message,
                        operation=operation,
                        request_id=request_id,
                        code=error_code
                    )
                
                # Execution errors
                if error_code in ("EXECUTION_FAILED", "EXECUTION_TIMEOUT"):
                    return CodeExecutionError(
                        message=message,
                        language=context.get("language"),
                        request_id=request_id,
                        code=error_code
                    )
                
                if error_code == "COMMAND_FAILED":
                    return CommandExecutionError(
                        message=message,
                        command=context.get("command"),
                        request_id=request_id,
                        code=error_code
                    )
                
                # Desktop errors
                if error_code == "DESKTOP_NOT_AVAILABLE":
                    missing_deps = error_details.get("missing_dependencies", [])
                    return DesktopNotAvailableError(
                        message=message,
                        missing_dependencies=missing_deps,
                        request_id=request_id,
                        code=error_code
                    )
                
                # Generic errors with code
                return AgentError(
                    message=message,
                    code=error_code,
                    request_id=request_id
                )
            
            # Fallback: Map by status code + context (for older agents without error codes)
            if status_code in (403, 404):
                if "file" in operation.lower() or "read" in operation.lower() or "download" in operation.lower():
                    # 403/404 for files usually means not found
                    return FileNotFoundError(
                        message=message,
                        path=context.get("path"),
                        request_id=request_id
                    )
            
            # File operation errors
            if "file" in operation.lower():
                return FileOperationError(
                    message=message,
                    operation=operation,
                    request_id=request_id
                )
            
            # Code execution errors
            if "code" in operation.lower() or "execute" in operation.lower():
                return CodeExecutionError(
                    message=message,
                    language=context.get("language"),
                    request_id=request_id
                )
            
            # Command execution errors
            if "command" in operation.lower():
                return CommandExecutionError(
                    message=message,
                    command=context.get("command"),
                    request_id=request_id
                )
            
            # Generic agent error
            return AgentError(
                message=message,
                code=f"HTTP_{status_code}",
                request_id=request_id
            )
        
        elif isinstance(error, httpx.TimeoutException):
            return BunnyshellTimeoutError(
                f"{operation} timed out after {self._timeout}s"
            )
        
        elif isinstance(error, httpx.NetworkError):
            return NetworkError(f"{operation} failed: {error}")
        
        else:
            return AgentError(f"{operation} failed: {error}")
    
    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., /files/read)
            operation: Operation name for error messages
            context: Additional context for error handling
            timeout: Request timeout (overrides default)
            **kwargs: Additional arguments for httpx request
        
        Returns:
            HTTP response
        
        Raises:
            AgentError: On request failure
        """
        url = f"{self._agent_url}{endpoint}"
        timeout_val = timeout or self._timeout
        
        for attempt in range(self._max_retries):
            try:
                logger.debug(f"{method} {url} (attempt {attempt + 1}/{self._max_retries})")
                
                response = self._client.request(
                    method=method,
                    url=url,
                    timeout=timeout_val,
                    **kwargs
                )
                
                # Raise for 4xx and 5xx status codes
                response.raise_for_status()
                
                return response
            
            except httpx.HTTPStatusError as e:
                # Check if should retry
                if attempt < self._max_retries - 1 and self._should_retry(e.response.status_code):
                    delay = self._get_retry_delay(attempt)
                    logger.warning(
                        f"{operation} failed with {e.response.status_code}, "
                        f"retrying in {delay}s (attempt {attempt + 1}/{self._max_retries})"
                    )
                    time.sleep(delay)
                    continue
                
                # No more retries, raise wrapped error
                raise self._wrap_error(e, operation, context)
            
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                # Retry on timeout/network errors
                if attempt < self._max_retries - 1:
                    delay = self._get_retry_delay(attempt)
                    logger.warning(
                        f"{operation} failed: {e}, "
                        f"retrying in {delay}s (attempt {attempt + 1}/{self._max_retries})"
                    )
                    time.sleep(delay)
                    continue
                
                # No more retries
                raise self._wrap_error(e, operation, context)
            
            except Exception as e:
                # Unexpected error, don't retry
                raise self._wrap_error(e, operation, context)
        
        # Should never reach here
        raise AgentError(f"{operation} failed after {self._max_retries} attempts")
    
    def get(self, endpoint: str, *, operation: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        """Make GET request."""
        return self._request("GET", endpoint, operation=operation, context=context, **kwargs)
    
    def post(self, endpoint: str, *, operation: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        """Make POST request."""
        return self._request("POST", endpoint, operation=operation, context=context, **kwargs)
    
    def put(self, endpoint: str, *, operation: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        """Make PUT request."""
        return self._request("PUT", endpoint, operation=operation, context=context, **kwargs)
    
    def patch(self, endpoint: str, *, operation: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        """Make PATCH request."""
        return self._request("PATCH", endpoint, operation=operation, context=context, **kwargs)
    
    def delete(self, endpoint: str, *, operation: str, context: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        """Make DELETE request."""
        return self._request("DELETE", endpoint, operation=operation, context=context, **kwargs)
    
    def close(self):
        """Close HTTP client and release connections."""
        self._client.close()
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.close()
        except:
            pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, *args):
        """Context manager exit."""
        self.close()

