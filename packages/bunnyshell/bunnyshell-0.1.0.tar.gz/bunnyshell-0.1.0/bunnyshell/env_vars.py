"""Environment variables resource for Bunnyshell Sandboxes."""

from typing import Dict, Optional
import logging
from ._agent_client import AgentHTTPClient

logger = logging.getLogger(__name__)


class EnvironmentVariables:
    """
    Environment variables resource.
    
    Provides methods for managing environment variables inside the sandbox at runtime.
    
    Features:
    - Get all environment variables
    - Set/replace all environment variables
    - Update specific environment variables (merge)
    - Delete individual environment variables
    
    Example:
        >>> sandbox = Sandbox.create(template="code-interpreter")
        >>> 
        >>> # Get all environment variables
        >>> env = sandbox.env.get_all()
        >>> print(env)
        >>> 
        >>> # Set multiple variables (replaces all)
        >>> sandbox.env.set_all({
        ...     "API_KEY": "sk-prod-xyz",
        ...     "DATABASE_URL": "postgres://localhost/db"
        ... })
        >>> 
        >>> # Update specific variables (merge)
        >>> sandbox.env.update({
        ...     "NODE_ENV": "production",
        ...     "DEBUG": "false"
        ... })
        >>> 
        >>> # Delete a variable
        >>> sandbox.env.delete("DEBUG")
    """
    
    def __init__(self, client: AgentHTTPClient):
        """
        Initialize EnvironmentVariables resource.
        
        Args:
            client: Shared agent HTTP client
        """
        self._client = client
        logger.debug("EnvironmentVariables resource initialized")
    
    def get_all(self, *, timeout: Optional[int] = None) -> Dict[str, str]:
        """
        Get all environment variables.
        
        Args:
            timeout: Request timeout in seconds (overrides default)
        
        Returns:
            Dictionary of environment variables
        
        Example:
            >>> env = sandbox.env.get_all()
            >>> print(env.get("PATH"))
            >>> print(env.get("HOME"))
        """
        logger.debug("Getting all environment variables")
        
        response = self._client.get(
            "/env",
            operation="get environment variables",
            timeout=timeout
        )
        
        data = response.json()
        return data.get("env_vars", {})
    
    def set_all(
        self,
        env_vars: Dict[str, str],
        *,
        timeout: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Set/replace all environment variables.
        
        This replaces ALL existing environment variables with the provided ones.
        Use update() if you want to merge instead.
        
        Args:
            env_vars: Dictionary of environment variables to set
            timeout: Request timeout in seconds (overrides default)
        
        Returns:
            Updated dictionary of all environment variables
        
        Example:
            >>> sandbox.env.set_all({
            ...     "API_KEY": "sk-prod-xyz",
            ...     "DATABASE_URL": "postgres://localhost/db",
            ...     "NODE_ENV": "production"
            ... })
        """
        logger.debug(f"Setting {len(env_vars)} environment variables (replace all)")
        
        response = self._client.put(
            "/env",
            json={"env_vars": env_vars},
            operation="set environment variables",
            timeout=timeout
        )
        
        data = response.json()
        return data.get("env_vars", {})
    
    def update(
        self,
        env_vars: Dict[str, str],
        *,
        timeout: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Update specific environment variables (merge).
        
        This merges the provided variables with existing ones.
        Existing variables not specified are preserved.
        
        Args:
            env_vars: Dictionary of environment variables to update/add
            timeout: Request timeout in seconds (overrides default)
        
        Returns:
            Updated dictionary of all environment variables
        
        Example:
            >>> # Add/update specific variables
            >>> sandbox.env.update({
            ...     "NODE_ENV": "production",
            ...     "DEBUG": "false"
            ... })
            >>> 
            >>> # Existing variables like PATH, HOME, etc. are preserved
        """
        logger.debug(f"Updating {len(env_vars)} environment variables (merge)")
        
        response = self._client.patch(
            "/env",
            json={"env_vars": env_vars},
            operation="update environment variables",
            timeout=timeout
        )
        
        # Handle empty response
        if response.content:
            data = response.json()
            return data.get("env_vars", {})
        else:
            # Return success (empty response means success for PATCH)
            return env_vars
    
    def delete(self, key: str, *, timeout: Optional[int] = None) -> Dict[str, str]:
        """
        Delete an environment variable.
        
        Args:
            key: Environment variable name to delete
            timeout: Request timeout in seconds (overrides default)
        
        Returns:
            Updated dictionary of all environment variables
        
        Example:
            >>> sandbox.env.delete("DEBUG")
            >>> sandbox.env.delete("TEMP_TOKEN")
        """
        logger.debug(f"Deleting environment variable: {key}")
        
        response = self._client.delete(
            f"/env/{key}",
            operation="delete environment variable",
            context={"key": key},
            timeout=timeout
        )
        
        data = response.json()
        return data.get("env_vars", {})
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a specific environment variable value.
        
        Convenience method that fetches all variables and returns the requested one.
        
        Args:
            key: Environment variable name
            default: Default value if variable doesn't exist
        
        Returns:
            Variable value or default
        
        Example:
            >>> api_key = sandbox.env.get("API_KEY")
            >>> db_url = sandbox.env.get("DATABASE_URL", "postgres://localhost/db")
        """
        env_vars = self.get_all()
        return env_vars.get(key, default)
    
    def set(self, key: str, value: str, *, timeout: Optional[int] = None) -> Dict[str, str]:
        """
        Set a single environment variable.
        
        Convenience method that updates just one variable (merge).
        
        Args:
            key: Environment variable name
            value: Environment variable value
            timeout: Request timeout in seconds (overrides default)
        
        Returns:
            Updated dictionary of all environment variables
        
        Example:
            >>> sandbox.env.set("API_KEY", "sk-prod-xyz")
            >>> sandbox.env.set("NODE_ENV", "production")
        """
        return self.update({key: value}, timeout=timeout)
    
    def __repr__(self) -> str:
        return f"<EnvironmentVariables client={self._client}>"

