"""Main Sandbox class - E2B inspired pattern."""

from typing import Optional, List, Iterator, Dict, Any
import logging

# Public API models (enhanced with generated models + convenience)
from .models import (
    SandboxInfo,
    Template,
    ExecutionResult,  # ExecuteResponse + convenience methods
    RichOutput,
    MetricsSnapshot,
    Language,
)

from ._client import HTTPClient
from ._agent_client import AgentHTTPClient
from ._utils import remove_none_values
from .files import Files
from .commands import Commands
from .desktop import Desktop
from .env_vars import EnvironmentVariables
from .cache import Cache
from ._ws_client import WebSocketClient
from .terminal import Terminal

logger = logging.getLogger(__name__)


class Sandbox:
    """
    Bunnyshell Sandbox - lightweight VM management.
    
    Create and manage sandboxes (microVMs) with a simple, intuitive API.
    
    Example:
        >>> from bunnyshell import Sandbox
        >>> 
        >>> # Create sandbox
        >>> sandbox = Sandbox.create(template="code-interpreter")
        >>> print(sandbox.get_info().public_host)
        >>> 
        >>> # Use and cleanup
        >>> sandbox.kill()
    """
    
    def __init__(
        self,
        sandbox_id: str,
        *,
        api_key: Optional[str] = None,
        base_url: str = "https://api.hopx.dev",
        timeout: int = 60,
        max_retries: int = 3,
    ):
        """
        Initialize Sandbox instance.
        
        Note: Prefer using Sandbox.create() or Sandbox.connect() instead of direct instantiation.
        
        Args:
            sandbox_id: Sandbox ID
            api_key: API key (or use BUNNYSHELL_API_KEY env var)
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        self.sandbox_id = sandbox_id
        self._client = HTTPClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._agent_client: Optional[AgentHTTPClient] = None
        self._ws_client: Optional[WebSocketClient] = None
        self._files: Optional[Files] = None
        self._commands: Optional[Commands] = None
        self._desktop: Optional[Desktop] = None
        self._env: Optional[EnvironmentVariables] = None
        self._cache: Optional[Cache] = None
        self._terminal: Optional[Terminal] = None
    
    @property
    def files(self) -> Files:
        """
        File operations resource.
        
        Lazy initialization - gets agent URL on first access.
        
        Returns:
            Files resource instance
        
        Example:
            >>> sandbox = Sandbox.create(template="code-interpreter")
            >>> content = sandbox.files.read('/workspace/data.txt')
        """
        if self._files is None:
            self._ensure_agent_client()
            # WS client is lazy-loaded in Files.watch() - not needed for basic operations
            self._files = Files(self._agent_client, self)
        return self._files
    
    @property
    def commands(self) -> Commands:
        """
        Command execution resource.
        
        Lazy initialization - gets agent URL on first access.
        
        Returns:
            Commands resource instance
        
        Example:
            >>> sandbox = Sandbox.create(template="nodejs")
            >>> result = sandbox.commands.run('npm install')
        """
        if self._commands is None:
            self._ensure_agent_client()
            self._commands = Commands(self._agent_client)
        return self._commands
    
    @property
    def desktop(self) -> Desktop:
        """
        Desktop automation resource.
        
        Lazy initialization - checks desktop availability on first access.
        
        Provides methods for:
        - VNC server management
        - Mouse and keyboard control
        - Screenshot capture
        - Screen recording
        - Window management
        - Display configuration
        
        Returns:
            Desktop resource instance
        
        Raises:
            DesktopNotAvailableError: If template doesn't support desktop automation
        
        Example:
            >>> sandbox = Sandbox.create(template="desktop")
            >>> 
            >>> # Start VNC
            >>> vnc_info = sandbox.desktop.start_vnc()
            >>> print(f"VNC at: {vnc_info.url}")
            >>> 
            >>> # Mouse control
            >>> sandbox.desktop.click(100, 100)
            >>> sandbox.desktop.type("Hello World")
            >>> 
            >>> # Screenshot
            >>> img = sandbox.desktop.screenshot()
            >>> with open('screen.png', 'wb') as f:
            ...     f.write(img)
            >>> 
            >>> # If desktop not available:
            >>> try:
            ...     sandbox.desktop.click(100, 100)
            ... except DesktopNotAvailableError as e:
            ...     print(e.message)
            ...     print(e.install_command)
        """
        if self._desktop is None:
            self._ensure_agent_client()
            self._desktop = Desktop(self._agent_client)
        return self._desktop
    
    @property
    def env(self) -> EnvironmentVariables:
        """
        Environment variables resource.
        
        Lazy initialization - gets agent URL on first access.
        
        Provides methods for:
        - Get all environment variables
        - Set/replace all environment variables
        - Update specific environment variables (merge)
        - Delete environment variables
        
        Returns:
            EnvironmentVariables resource instance
        
        Example:
            >>> sandbox = Sandbox.create(template="code-interpreter")
            >>> 
            >>> # Get all environment variables
            >>> env = sandbox.env.get_all()
            >>> print(env.get("PATH"))
            >>> 
            >>> # Set a single variable
            >>> sandbox.env.set("API_KEY", "sk-prod-xyz")
            >>> 
            >>> # Update multiple variables (merge)
            >>> sandbox.env.update({
            ...     "NODE_ENV": "production",
            ...     "DEBUG": "false"
            ... })
            >>> 
            >>> # Get a specific variable
            >>> api_key = sandbox.env.get("API_KEY")
            >>> 
            >>> # Delete a variable
            >>> sandbox.env.delete("DEBUG")
        """
        if self._env is None:
            self._ensure_agent_client()
            self._env = EnvironmentVariables(self._agent_client)
        return self._env
    
    @property
    def cache(self) -> Cache:
        """
        Cache management resource.
        
        Lazy initialization - gets agent URL on first access.
        
        Provides methods for:
        - Get cache statistics
        - Clear cache
        
        Returns:
            Cache resource instance
        
        Example:
            >>> sandbox = Sandbox.create(template="code-interpreter")
            >>> 
            >>> # Get cache stats
            >>> stats = sandbox.cache.stats()
            >>> print(f"Cache hits: {stats['hits']}")
            >>> print(f"Cache size: {stats['size']} MB")
            >>> 
            >>> # Clear cache
            >>> sandbox.cache.clear()
        """
        if self._cache is None:
            self._ensure_agent_client()
            self._cache = Cache(self._agent_client)
        return self._cache
    
    @property
    def terminal(self) -> Terminal:
        """
        Interactive terminal resource via WebSocket.
        
        Lazy initialization - gets agent URL and WebSocket client on first access.
        
        Provides methods for:
        - Connect to interactive terminal
        - Send input to terminal
        - Resize terminal
        - Receive output stream
        
        Returns:
            Terminal resource instance
        
        Note:
            Requires websockets library: pip install websockets
        
        Example:
            >>> import asyncio
            >>> 
            >>> async def run_terminal():
            ...     sandbox = Sandbox.create(template="code-interpreter")
            ...     
            ...     # Connect to terminal
            ...     async with await sandbox.terminal.connect() as ws:
            ...         # Send command
            ...         await sandbox.terminal.send_input(ws, "ls -la\\n")
            ...         
            ...         # Receive output
            ...         async for message in sandbox.terminal.iter_output(ws):
            ...             if message['type'] == 'output':
            ...                 print(message['data'], end='')
            ...             elif message['type'] == 'exit':
            ...                 break
            >>> 
            >>> asyncio.run(run_terminal())
        """
        if self._terminal is None:
            self._ensure_ws_client()
            self._terminal = Terminal(self._ws_client)
        return self._terminal
    
    def _ensure_agent_client(self) -> None:
        """Ensure agent HTTP client is initialized."""
        if self._agent_client is None:
            info = self.get_info()
            agent_url = info.public_host.rstrip('/')
            self._agent_client = AgentHTTPClient(
                agent_url=agent_url,
                timeout=60,  # Default 60s for agent operations
                max_retries=3
            )
            logger.debug(f"Agent client initialized: {agent_url}")
    
    def _ensure_ws_client(self) -> None:
        """Ensure WebSocket client is initialized."""
        if self._ws_client is None:
            info = self.get_info()
            agent_url = info.public_host.rstrip('/')
            self._ws_client = WebSocketClient(agent_url)
            logger.debug(f"WebSocket client initialized: {agent_url}")
    
    # =============================================================================
    # CLASS METHODS (Static - for creating/listing sandboxes)
    # =============================================================================
    
    @classmethod
    def create(
        cls,
        template: str,
        *,
        vcpu: int = 2,
        memory_mb: int = 2048,
        disk_gb: Optional[int] = None,
        region: Optional[str] = None,
        timeout: int = 300,  # 5 minutes default
        env_vars: Optional[Dict[str, str]] = None,
        api_key: Optional[str] = None,
        base_url: str = "https://api.hopx.dev",
    ) -> "Sandbox":
        """
        Create a new sandbox.
        
        Args:
            template: Template name (e.g., "code-interpreter", "nodejs", "python")
            vcpu: Number of vCPUs (default: 2)
            memory_mb: Memory in MB (default: 2048)
            disk_gb: Disk size in GB (optional, uses template default)
            region: Preferred region (optional, auto-selected if not specified)
            timeout: Sandbox timeout in seconds (default: 300 = 5 minutes)
            env_vars: Environment variables to set in the sandbox (optional)
            api_key: API key (or use BUNNYSHELL_API_KEY env var)
            base_url: API base URL (default: production)
        
        Returns:
            Sandbox instance
        
        Raises:
            ValidationError: Invalid parameters
            ResourceLimitError: Insufficient resources
            APIError: API request failed
        
        Example:
            >>> sandbox = Sandbox.create(template="code-interpreter")
            >>> print(sandbox.get_info().public_host)
            
            >>> # With custom resources and environment variables
            >>> sandbox = Sandbox.create(
            ...     template="nodejs",
            ...     vcpu=4,
            ...     memory_mb=4096,
            ...     timeout=600,
            ...     env_vars={
            ...         "API_KEY": "sk-prod-xyz",
            ...         "DATABASE_URL": "postgres://localhost/db",
            ...         "NODE_ENV": "production"
            ...     }
            ... )
        """
        # Create HTTP client
        client = HTTPClient(api_key=api_key, base_url=base_url)
        
        # Build request payload
        data = remove_none_values({
            "template_name": template,
            "vcpu": vcpu,
            "memory_mb": memory_mb,
            "disk_gb": disk_gb,
            "region": region,
            "env_vars": env_vars,
        })
        
        # Create sandbox via API
        response = client.post("/v1/sandboxes", json=data)
        sandbox_id = response["id"]
        
        # Return Sandbox instance
        return cls(
            sandbox_id=sandbox_id,
            api_key=api_key,
            base_url=base_url,
        )
    
    @classmethod
    def connect(
        cls,
        sandbox_id: str,
        *,
        api_key: Optional[str] = None,
        base_url: str = "https://api.hopx.dev",
    ) -> "Sandbox":
        """
        Connect to an existing sandbox.
        
        Args:
            sandbox_id: Sandbox ID
            api_key: API key (or use BUNNYSHELL_API_KEY env var)
            base_url: API base URL
        
        Returns:
            Sandbox instance
        
        Raises:
            NotFoundError: Sandbox not found
        
        Example:
            >>> sandbox = Sandbox.connect("1761048129dsaqav4n")
            >>> info = sandbox.get_info()
            >>> print(info.status)
        """
        # Create instance
        instance = cls(
            sandbox_id=sandbox_id,
            api_key=api_key,
            base_url=base_url,
        )
        
        # Verify it exists by fetching info
        instance.get_info()
        
        return instance
    
    @classmethod
    def iter(
        cls,
        *,
        status: Optional[str] = None,
        region: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: str = "https://api.hopx.dev",
    ) -> Iterator["Sandbox"]:
        """
        Lazy iterator for sandboxes.
        
        Yields sandboxes one by one, fetching pages as needed.
        Doesn't load all sandboxes into memory at once.
        
        Args:
            status: Filter by status (running, stopped, paused, creating)
            region: Filter by region
            api_key: API key (or use BUNNYSHELL_API_KEY env var)
            base_url: API base URL
        
        Yields:
            Sandbox instances
        
        Example:
            >>> # Lazy loading - fetches pages as needed
            >>> for sandbox in Sandbox.iter(status="running"):
            ...     print(f"{sandbox.sandbox_id}")
            ...     if found:
            ...         break  # Doesn't fetch remaining pages!
        """
        client = HTTPClient(api_key=api_key, base_url=base_url)
        limit = 100
        has_more = True
        cursor = None
        
        while has_more:
            params = {"limit": limit}
            if status:
                params["status"] = status
            if region:
                params["region"] = region
            if cursor:
                params["cursor"] = cursor
            
            logger.debug(f"Fetching sandboxes page (cursor: {cursor})")
            response = client.get("/v1/sandboxes", params=params)
            
            for item in response.get("data", []):
                yield cls(
                    sandbox_id=item["id"],
                    api_key=api_key,
                    base_url=base_url,
                )
            
            has_more = response.get("has_more", False)
            cursor = response.get("next_cursor")
            
            if has_more:
                logger.debug(f"More results available, next cursor: {cursor}")
    
    @classmethod
    def list(
        cls,
        *,
        status: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 100,
        api_key: Optional[str] = None,
        base_url: str = "https://api.hopx.dev",
    ) -> List["Sandbox"]:
        """
        List all sandboxes (loads all into memory).
        
        For lazy loading (better memory usage), use Sandbox.iter() instead.
        
        Args:
            status: Filter by status (running, stopped, paused, creating)
            region: Filter by region
            limit: Maximum number of results (default: 100)
            api_key: API key (or use BUNNYSHELL_API_KEY env var)
            base_url: API base URL
        
        Returns:
            List of Sandbox instances (all loaded into memory)
        
        Example:
            >>> # List all running sandboxes (loads all into memory)
            >>> sandboxes = Sandbox.list(status="running")
            >>> for sb in sandboxes:
            ...     print(f"{sb.sandbox_id}")
            
            >>> # For better memory usage, use iter():
            >>> for sb in Sandbox.iter(status="running"):
            ...     print(f"{sb.sandbox_id}")
        """
        client = HTTPClient(api_key=api_key, base_url=base_url)
        
        params = remove_none_values({
            "status": status,
            "region": region,
            "limit": limit,
        })
        
        response = client.get("/v1/sandboxes", params=params)
        sandboxes_data = response.get("data", [])
        
        # Create Sandbox instances
        return [
            cls(
                sandbox_id=sb["id"],
                api_key=api_key,
                base_url=base_url,
            )
            for sb in sandboxes_data
        ]
    
    @classmethod
    def list_templates(
        cls,
        *,
        category: Optional[str] = None,
        language: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: str = "https://api.hopx.dev",
    ) -> List[Template]:
        """
        List available templates.
        
        Args:
            category: Filter by category (development, infrastructure, operating-system)
            language: Filter by language (python, nodejs, etc.)
            api_key: API key (or use BUNNYSHELL_API_KEY env var)
            base_url: API base URL
        
        Returns:
            List of Template objects
        
        Example:
            >>> templates = Sandbox.list_templates()
            >>> for t in templates:
            ...     print(f"{t.name}: {t.display_name}")
            
            >>> # Filter by category
            >>> dev_templates = Sandbox.list_templates(category="development")
        """
        client = HTTPClient(api_key=api_key, base_url=base_url)
        
        params = remove_none_values({
            "category": category,
            "language": language,
        })
        
        response = client.get("/v1/templates", params=params)
        templates_data = response.get("data", [])
        
        return [Template(**t) for t in templates_data]
    
    @classmethod
    def get_template(
        cls,
        name: str,
        *,
        api_key: Optional[str] = None,
        base_url: str = "https://api.hopx.dev",
    ) -> Template:
        """
        Get template details.
        
        Args:
            name: Template name
            api_key: API key (or use BUNNYSHELL_API_KEY env var)
            base_url: API base URL
        
        Returns:
            Template object
        
        Raises:
            NotFoundError: Template not found
        
        Example:
            >>> template = Sandbox.get_template("code-interpreter")
            >>> print(template.description)
            >>> print(f"Default: {template.default_resources.vcpu} vCPU")
        """
        client = HTTPClient(api_key=api_key, base_url=base_url)
        response = client.get(f"/v1/templates/{name}")
        return Template(**response)
    
    # =============================================================================
    # INSTANCE METHODS (for managing individual sandbox)
    # =============================================================================
    
    def get_info(self) -> SandboxInfo:
        """
        Get current sandbox information.
        
        Returns:
            SandboxInfo with current state
        
        Raises:
            NotFoundError: Sandbox not found
        
        Example:
            >>> sandbox = Sandbox.create(template="nodejs")
            >>> info = sandbox.get_info()
            >>> print(f"Status: {info.status}")
            >>> print(f"URL: {info.public_host}")
            >>> print(f"Ends at: {info.end_at}")
        """
        response = self._client.get(f"/v1/sandboxes/{self.sandbox_id}")
        return SandboxInfo(
            sandbox_id=response["id"],
            template_id=response.get("template_id"),
            template_name=response.get("template_name"),
            organization_id=response.get("organization_id", ""),
            node_id=response.get("node_id"),
            region=response.get("region"),
            status=response["status"],
            public_host=response.get("public_host") or response.get("direct_url", ""),
            vcpu=response.get("resources", {}).get("vcpu"),
            memory_mb=response.get("resources", {}).get("memory_mb"),
            disk_mb=response.get("resources", {}).get("disk_mb"),
            created_at=response.get("created_at"),
            started_at=None,  # TODO: Add when API provides it
            end_at=None,  # TODO: Add when API provides it
        )
    
    def get_agent_metrics(self) -> Dict[str, Any]:
        """
        Get real-time agent metrics.
        
        Returns agent performance and health metrics including uptime,
        request counts, error counts, and performance statistics.
        
        Returns:
            Dict with metrics including:
            - uptime_seconds: Agent uptime
            - total_requests: Total requests count
            - total_errors: Total errors count
            - requests_total: Per-endpoint request counts
            - avg_duration_ms: Average request duration by endpoint
        
        Example:
            >>> metrics = sandbox.get_agent_metrics()
            >>> print(f"Uptime: {metrics['uptime_seconds']}s")
            >>> print(f"Total requests: {metrics.get('total_requests', 0)}")
            >>> print(f"Errors: {metrics.get('total_errors', 0)}")
        
        Note:
            Requires Agent v3.1.0+
        """
        self._ensure_agent_client()
        
        logger.debug("Getting agent metrics")
        
        response = self._agent_client.get(
            "/metrics/snapshot",
            operation="get agent metrics"
        )
        
        return response.json()
    
    def run_code(
        self,
        code: str,
        *,
        language: str = "python",
        timeout: int = 60,
        env: Optional[Dict[str, str]] = None,
        working_dir: str = "/workspace",
    ) -> ExecutionResult:
        """
        Execute code with rich output capture (plots, DataFrames, etc.).
        
        This method automatically captures visual outputs like matplotlib plots,
        pandas DataFrames, and plotly charts.
        
        Args:
            code: Code to execute
            language: Language (python, javascript, bash, go)
            timeout: Execution timeout in seconds (default: 60)
            env: Optional environment variables for this execution only.
                 Priority: Request env > Global env > Agent env
            working_dir: Working directory for execution (default: /workspace)
        
        Returns:
            ExecutionResult with stdout, stderr, rich_outputs
        
        Raises:
            CodeExecutionError: If execution fails
            TimeoutError: If execution times out
        
        Example:
            >>> # Simple code execution
            >>> result = sandbox.run_code('print("Hello, World!")')
            >>> print(result.stdout)  # "Hello, World!\n"
            >>> 
            >>> # With environment variables
            >>> result = sandbox.run_code(
            ...     'import os; print(os.environ["API_KEY"])',
            ...     env={"API_KEY": "sk-test-123", "DEBUG": "true"}
            ... )
            >>> 
            >>> # Execute with matplotlib plot
            >>> code = '''
            ... import matplotlib.pyplot as plt
            ... plt.plot([1, 2, 3, 4])
            ... plt.savefig('/workspace/plot.png')
            ... '''
            >>> result = sandbox.run_code(code)
            >>> print(f"Generated {result.rich_count} outputs")
            >>> 
            >>> # Check for errors
            >>> result = sandbox.run_code('print(undefined_var)')
            >>> if not result.success:
            ...     print(f"Error: {result.stderr}")
            >>> 
            >>> # With custom timeout for long-running code
            >>> result = sandbox.run_code(long_code, timeout=300)
        """
        self._ensure_agent_client()
        
        logger.debug(f"Executing {language} code ({len(code)} chars)")
        
        # Build request payload
        payload = {
            "language": language,
            "code": code,
            "working_dir": working_dir,
            "timeout": timeout
        }
        
        # Add optional environment variables
        if env:
            payload["env"] = env
        
        # Use /execute/rich endpoint for automatic rich output capture
        response = self._agent_client.post(
            "/execute/rich",
            json=payload,
            operation="execute code",
            context={"language": language},
            timeout=timeout + 5  # Add buffer to HTTP timeout
        )
        
        data = response.json() if response.content else {}
        
        # Parse rich outputs
        rich_outputs = []
        if data and isinstance(data, dict):
            rich_outputs_data = data.get("rich_outputs") or []
            for output in rich_outputs_data:
                if output:
                    rich_outputs.append(RichOutput(
                        type=output.get("type", ""),
                        data=output.get("data", {}),
                        metadata=output.get("metadata"),
                        timestamp=output.get("timestamp")
                    ))
        
        # Create result
        result = ExecutionResult(
            success=data.get("success", True) if data else False,
            stdout=data.get("stdout", "") if data else "",
            stderr=data.get("stderr", "") if data else "",
            exit_code=data.get("exit_code", 0) if data else 1,
            execution_time=data.get("execution_time", 0.0) if data else 0.0,
            rich_outputs=rich_outputs
        )
        
        return result
    
    def run_code_async(
        self,
        code: str,
        callback_url: str,
        *,
        language: str = "python",
        timeout: int = 1800,
        env: Optional[Dict[str, str]] = None,
        working_dir: str = "/workspace",
        callback_headers: Optional[Dict[str, str]] = None,
        callback_signature_secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute code asynchronously with webhook callback.
        
        For long-running code (>5 minutes). Agent will POST results to callback_url when complete.
        
        Args:
            code: Code to execute
            callback_url: URL to POST results to when execution completes
            language: Language (python, javascript, bash, go)
            timeout: Execution timeout in seconds (default: 1800 = 30 min)
            env: Optional environment variables
            working_dir: Working directory (default: /workspace)
            callback_headers: Custom headers to include in callback request
            callback_signature_secret: Secret to sign callback payload (HMAC-SHA256)
        
        Returns:
            Dict with execution_id, status, callback_url
        
        Example:
            >>> # Start async execution
            >>> response = sandbox.run_code_async(
            ...     code='import time; time.sleep(600); print("Done!")',
            ...     callback_url='https://app.com/webhooks/ml/training',
            ...     callback_headers={'Authorization': 'Bearer secret'},
            ...     callback_signature_secret='webhook-secret-123'
            ... )
            >>> print(f"Execution ID: {response['execution_id']}")
            >>> 
            >>> # Agent will POST to callback_url when done:
            >>> # POST https://app.com/webhooks/ml/training
            >>> # X-HOPX-Signature: sha256=...
            >>> # X-HOPX-Timestamp: 1698765432
            >>> # Authorization: Bearer secret
            >>> # {
            >>> #   "execution_id": "abc123",
            >>> #   "status": "completed",
            >>> #   "stdout": "Done!",
            >>> #   "stderr": "",
            >>> #   "exit_code": 0,
            >>> #   "execution_time": 600.123
            >>> # }
        """
        self._ensure_agent_client()
        
        logger.debug(f"Starting async {language} execution ({len(code)} chars)")
        
        # Build request payload
        payload = {
            "code": code,
            "language": language,
            "timeout": timeout,
            "working_dir": working_dir,
            "callback_url": callback_url,
        }
        
        if env:
            payload["env"] = env
        if callback_headers:
            payload["callback_headers"] = callback_headers
        if callback_signature_secret:
            payload["callback_signature_secret"] = callback_signature_secret
        
        response = self._agent_client.post(
            "/execute/async",
            json=payload,
            operation="async execute code",
            context={"language": language},
            timeout=10  # Quick response
        )
        
        return response.json()
    
    def run_code_background(
        self,
        code: str,
        *,
        language: str = "python",
        timeout: int = 300,
        env: Optional[Dict[str, str]] = None,
        working_dir: str = "/workspace",
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute code in background and return immediately.
        
        Use list_processes() to check status and kill_process() to terminate.
        
        Args:
            code: Code to execute
            language: Language (python, javascript, bash, go)
            timeout: Execution timeout in seconds (default: 300 = 5 min)
            env: Optional environment variables
            working_dir: Working directory (default: /workspace)
            name: Optional process name for identification
        
        Returns:
            Dict with process_id, execution_id, status
        
        Example:
            >>> # Start background execution
            >>> result = sandbox.run_code_background(
            ...     code='long_running_task()',
            ...     name='ml-training',
            ...     env={"GPU": "enabled"}
            ... )
            >>> process_id = result['process_id']
            >>> 
            >>> # Check status
            >>> processes = sandbox.list_processes()
            >>> for p in processes:
            ...     if p['process_id'] == process_id:
            ...         print(f"Status: {p['status']}")
            >>> 
            >>> # Kill if needed
            >>> sandbox.kill_process(process_id)
        """
        self._ensure_agent_client()
        
        logger.debug(f"Starting background {language} execution ({len(code)} chars)")
        
        # Build request payload
        payload = {
            "code": code,
            "language": language,
            "timeout": timeout,
            "working_dir": working_dir,
        }
        
        if env:
            payload["env"] = env
        if name:
            payload["name"] = name
        
        response = self._agent_client.post(
            "/execute/background",
            json=payload,
            operation="background execute code",
            context={"language": language},
            timeout=10  # Quick response
        )
        
        return response.json()
    
    def list_processes(self) -> List[Dict[str, Any]]:
        """
        List all background execution processes.
        
        Returns:
            List of process dictionaries with status
        
        Example:
            >>> processes = sandbox.list_processes()
            >>> for p in processes:
            ...     print(f"{p['name']}: {p['status']} (PID: {p['process_id']})")
        """
        self._ensure_agent_client()
        
        response = self._agent_client.get(
            "/execute/processes",
            operation="list processes"
        )
        
        data = response.json()
        return data.get("processes", [])
    
    def kill_process(self, process_id: str) -> Dict[str, Any]:
        """
        Kill a background execution process.
        
        Args:
            process_id: Process ID to kill
        
        Returns:
            Dict with confirmation message
        
        Example:
            >>> sandbox.kill_process("proc_abc123")
        """
        self._ensure_agent_client()
        
        response = self._agent_client.post(
            f"/execute/kill/{process_id}",
            operation="kill process",
            context={"process_id": process_id}
        )
        
        return response.json()
    
    def get_metrics_snapshot(self) -> Dict[str, Any]:
        """
        Get current system metrics snapshot.
        
        Returns:
            Dict with system metrics (CPU, memory, disk), process metrics, cache stats
        
        Example:
            >>> metrics = sandbox.get_metrics_snapshot()
            >>> print(f"CPU: {metrics['system']['cpu']['usage_percent']}%")
            >>> print(f"Memory: {metrics['system']['memory']['usage_percent']}%")
            >>> print(f"Processes: {metrics['process']['count']}")
            >>> print(f"Cache size: {metrics['cache']['size']}")
        """
        self._ensure_agent_client()
        
        response = self._agent_client.get(
            "/metrics/snapshot",
            operation="get metrics snapshot"
        )
        
        return response.json()
    
    def run_ipython(
        self,
        code: str,
        *,
        timeout: int = 60,
        env: Optional[Dict[str, str]] = None,
    ) -> ExecutionResult:
        """
        Execute code in persistent IPython kernel.
        
        Variables and state persist across executions.
        Supports magic commands and interactive features.
        
        Args:
            code: Code to execute in IPython
            timeout: Execution timeout in seconds (default: 60)
            env: Optional environment variables
        
        Returns:
            ExecutionResult with stdout, stderr
        
        Example:
            >>> # First execution - define variable
            >>> sandbox.run_ipython("x = 10")
            >>> 
            >>> # Second execution - x persists!
            >>> result = sandbox.run_ipython("print(x)")
            >>> print(result.stdout)  # "10"
            >>> 
            >>> # Magic commands work
            >>> sandbox.run_ipython("%timeit sum(range(100))")
        """
        self._ensure_agent_client()
        
        logger.debug(f"Executing IPython code ({len(code)} chars)")
        
        # Build request payload
        payload = {
            "code": code,
            "timeout": timeout,
        }
        
        if env:
            payload["env"] = env
        
        response = self._agent_client.post(
            "/execute/ipython",
            json=payload,
            operation="execute ipython",
            timeout=timeout + 5
        )
        
        data = response.json()
        
        return ExecutionResult(
            success=data.get("success", True),
            stdout=data.get("stdout", ""),
            stderr=data.get("stderr", ""),
            exit_code=data.get("exit_code", 0),
            execution_time=data.get("execution_time", 0.0)
        )
    
    async def run_code_stream(
        self,
        code: str,
        *,
        language: str = "python",
        timeout: int = 60,
        env: Optional[Dict[str, str]] = None,
        working_dir: str = "/workspace"
    ):
        """
        Execute code with real-time output streaming via WebSocket.
        
        Stream stdout/stderr as it's generated (async generator).
        
        Args:
            code: Code to execute
            language: Language (python, javascript, bash, go)
            timeout: Execution timeout in seconds
            env: Optional environment variables
            working_dir: Working directory
        
        Yields:
            Message dictionaries:
            - {"type": "stdout", "data": "...", "timestamp": "..."}
            - {"type": "stderr", "data": "...", "timestamp": "..."}
            - {"type": "result", "exit_code": 0, "execution_time": 1.23}
            - {"type": "complete", "success": True}
        
        Note:
            Requires websockets library: pip install websockets
        
        Example:
            >>> import asyncio
            >>> 
            >>> async def stream_execution():
            ...     sandbox = Sandbox.create(template="code-interpreter")
            ...     
            ...     code = '''
            ...     import time
            ...     for i in range(5):
            ...         print(f"Step {i+1}/5")
            ...         time.sleep(1)
            ...     '''
            ...     
            ...     async for message in sandbox.run_code_stream(code):
            ...         if message['type'] == 'stdout':
            ...             print(message['data'], end='')
            ...         elif message['type'] == 'result':
            ...             print(f"\\nExit code: {message['exit_code']}")
            >>> 
            >>> asyncio.run(stream_execution())
        """
        self._ensure_ws_client()
        
        # Connect to streaming endpoint
        async with await self._ws_client.connect("/execute/stream") as ws:
            # Send execution request
            request = {
                "type": "execute",
                "code": code,
                "language": language,
                "timeout": timeout,
                "working_dir": working_dir
            }
            if env:
                request["env"] = env
            
            await self._ws_client.send_message(ws, request)
            
            # Stream messages
            async for message in self._ws_client.iter_messages(ws):
                yield message
                
                # Stop on complete
                if message.get('type') == 'complete':
                    break
    
    def set_timeout(self, seconds: int) -> None:
        """
        Extend sandbox timeout.
        
        The new timeout will be 'seconds' from now.
        
        Args:
            seconds: New timeout duration in seconds from now
        
        Example:
            >>> sandbox = Sandbox.create(template="nodejs", timeout=300)
            >>> # Extend to 10 minutes from now
            >>> sandbox.set_timeout(600)
        
        Note:
            This feature may not be available in all plans.
        """
        # TODO: Implement when API supports it
        # For now, this is a placeholder matching E2B's API
        raise NotImplementedError(
            "set_timeout() will be available soon. "
            "For now, create sandbox with desired timeout: "
            "Sandbox.create(template='...', timeout=600)"
        )
    
    def stop(self) -> None:
        """
        Stop the sandbox.
        
        A stopped sandbox can be started again with start().
        
        Example:
            >>> sandbox.stop()
            >>> # ... do something else ...
            >>> sandbox.start()
        """
        self._client.post(f"/v1/sandboxes/{self.sandbox_id}/stop")
    
    def start(self) -> None:
        """
        Start a stopped sandbox.
        
        Example:
            >>> sandbox.start()
        """
        self._client.post(f"/v1/sandboxes/{self.sandbox_id}/start")
    
    def pause(self) -> None:
        """
        Pause the sandbox.
        
        A paused sandbox can be resumed with resume().
        
        Example:
            >>> sandbox.pause()
            >>> # ... do something else ...
            >>> sandbox.resume()
        """
        self._client.post(f"/v1/sandboxes/{self.sandbox_id}/pause")
    
    def resume(self) -> None:
        """
        Resume a paused sandbox.
        
        Example:
            >>> sandbox.resume()
        """
        self._client.post(f"/v1/sandboxes/{self.sandbox_id}/resume")
    
    def kill(self) -> None:
        """
        Destroy the sandbox immediately.
        
        This action is irreversible. All data in the sandbox will be lost.
        
        Example:
            >>> sandbox = Sandbox.create(template="nodejs")
            >>> # ... use sandbox ...
            >>> sandbox.kill()  # Clean up
        """
        self._client.delete(f"/v1/sandboxes/{self.sandbox_id}")
    
    # =============================================================================
    # CONTEXT MANAGER (auto-cleanup)
    # =============================================================================
    
    def __enter__(self) -> "Sandbox":
        """Context manager entry."""
        return self
    
    def __exit__(self, *args) -> None:
        """Context manager exit - auto cleanup."""
        try:
            self.kill()
        except Exception:
            # Ignore errors on cleanup
            pass
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def __repr__(self) -> str:
        return f"<Sandbox {self.sandbox_id}>"
    
    def __str__(self) -> str:
        try:
            info = self.get_info()
            return f"Sandbox(id={self.sandbox_id}, status={info.status}, url={info.public_host})"
        except Exception:
            return f"Sandbox(id={self.sandbox_id})"

