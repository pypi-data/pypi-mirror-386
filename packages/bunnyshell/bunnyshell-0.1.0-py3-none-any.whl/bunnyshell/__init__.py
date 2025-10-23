"""
Bunnyshell Python SDK

Official Python client for Bunnyshell Sandboxes.

Sync Example:
    >>> from bunnyshell import Sandbox
    >>> 
    >>> # Create sandbox
    >>> sandbox = Sandbox.create(template="code-interpreter")
    >>> print(sandbox.get_info().public_host)
    >>> 
    >>> # Cleanup
    >>> sandbox.kill()

Async Example:
    >>> from bunnyshell import AsyncSandbox
    >>> 
    >>> async with AsyncSandbox.create(template="nodejs") as sandbox:
    ...     info = await sandbox.get_info()
    ...     print(f"Running at: {info.public_host}")
    # Automatically killed when exiting context
"""

from .sandbox import Sandbox
from .async_sandbox import AsyncSandbox
from .models import (
    SandboxInfo,
    Template,
    TemplateResources,
    ExecutionResult,
    CommandResult,
    FileInfo,
    RichOutput,
    # Desktop models
    VNCInfo,
    WindowInfo,
    RecordingInfo,
    DisplayInfo,
)
from .errors import (
    BunnyshellError,
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ResourceLimitError,
    ValidationError,
    ServerError,
    NetworkError,
    TimeoutError,
    # Agent operation errors
    AgentError,
    FileNotFoundError,
    FileOperationError,
    CodeExecutionError,
    CommandExecutionError,
    DesktopNotAvailableError,
)

__version__ = "0.1.0"
__all__ = [
    "Sandbox",
    "AsyncSandbox",
    "SandboxInfo",
    "Template",
    "TemplateResources",
    "ExecutionResult",
    "CommandResult",
    "FileInfo",
    "RichOutput",
    # Desktop models
    "VNCInfo",
    "WindowInfo",
    "RecordingInfo",
    "DisplayInfo",
    # Errors
    "BunnyshellError",
    "APIError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError",
    "ResourceLimitError",
    "ValidationError",
    "ServerError",
    "NetworkError",
    "TimeoutError",
    # Agent operation errors
    "AgentError",
    "FileNotFoundError",
    "FileOperationError",
    "CodeExecutionError",
    "CommandExecutionError",
    "DesktopNotAvailableError",
]

