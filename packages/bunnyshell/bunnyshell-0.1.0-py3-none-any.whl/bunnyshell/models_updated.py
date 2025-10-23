"""
Data models for Bunnyshell Sandboxes SDK.

This module combines hand-crafted models (SandboxInfo, Template) with
auto-generated models from OpenAPI spec for type safety and maintainability.

Auto-generated models are re-exported for convenience with backward-compatible names.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# Import auto-generated models
from ._generated.models import (
    # Execution models (auto-generated)
    ExecuteResponse as _ExecuteResponse,
    ExecuteRequest as _ExecuteRequest,
    RichOutput as _RichOutput,
    Language,
    
    # File models (auto-generated)
    FileInfo as _FileInfo,
    FileListResponse,
    FileContentResponse,
    FileWriteRequest,
    FileResponse,
    
    # Command models (auto-generated)
    CommandResponse as _CommandResponse,
    
    # Desktop models (auto-generated)
    VNCInfo as _VNCInfo,
    WindowInfo as _WindowInfo,
    RecordingInfo as _RecordingInfo,
    DisplayInfo as _DisplayInfo,
    ScreenshotResponse,
    
    # Error models (auto-generated)
    ErrorResponse,
    ErrorCode,
    
    # Metrics models (auto-generated)
    MetricsSnapshot,
    SystemMetrics,
    HealthResponse,
    InfoResponse as _InfoResponse,
)


# =============================================================================
# ENHANCED MODELS (Auto-generated + Convenience Methods for DX)
# =============================================================================

class RichOutput(_RichOutput):
    """
    Rich output from code execution (plots, DataFrames, etc.).
    
    Auto-generated from OpenAPI spec with convenience methods added.
    """
    
    def __repr__(self) -> str:
        return f"<RichOutput type={self.type}>"


class ExecutionResult(_ExecuteResponse):
    """
    Result of code execution.
    
    Auto-generated from OpenAPI spec (ExecuteResponse) with convenience methods.
    This is an alias for backward compatibility while adding DX improvements.
    """
    
    @property
    def rich_count(self) -> int:
        """Number of rich outputs."""
        return len(self.rich_outputs) if self.rich_outputs else 0
    
    def __repr__(self) -> str:
        status = "✅" if self.success else "❌"
        return f"<ExecutionResult {status} time={self.execution_time:.3f}s rich={self.rich_count}>"


class CommandResult(_CommandResponse):
    """
    Result of command execution.
    
    Auto-generated from OpenAPI spec (CommandResponse) with convenience methods.
    """
    
    @property
    def success(self) -> bool:
        """Whether command succeeded (exit code 0)."""
        return self.exit_code == 0
    
    def __repr__(self) -> str:
        status = "✅" if self.success else "❌"
        return f"<CommandResult {status} exit={self.exit_code} time={self.execution_time:.3f}s>"


class FileInfo(_FileInfo):
    """
    File or directory information.
    
    Auto-generated from OpenAPI spec with convenience methods.
    """
    
    @property
    def is_file(self) -> bool:
        """Whether this is a file (not directory)."""
        return not self.is_directory
    
    @property
    def is_dir(self) -> bool:
        """Alias for is_directory (backward compat)."""
        return self.is_directory
    
    @property
    def size_kb(self) -> float:
        """Size in kilobytes."""
        return self.size / 1024
    
    @property
    def size_mb(self) -> float:
        """Size in megabytes."""
        return self.size / (1024 * 1024)
    
    def __repr__(self) -> str:
        type_icon = "📁" if self.is_directory else "📄"
        return f"<FileInfo {type_icon} {self.name} ({self.size} bytes)>"


class VNCInfo(_VNCInfo):
    """VNC server information with convenience properties."""
    
    @property
    def running(self) -> bool:
        """Whether VNC server is running (always True if we have this info)."""
        return True


class WindowInfo(_WindowInfo):
    """Window information with convenience properties."""
    pass


class RecordingInfo(_RecordingInfo):
    """Screen recording information with convenience properties."""
    
    @property
    def is_recording(self) -> bool:
        """Whether recording is in progress."""
        return self.status == "recording"
    
    @property
    def is_ready(self) -> bool:
        """Whether recording is ready to download."""
        return self.status == "stopped"


class DisplayInfo(_DisplayInfo):
    """Display information with convenience properties."""
    
    @property
    def resolution(self) -> str:
        """Resolution as string (e.g., '1920x1080')."""
        return f"{self.width}x{self.height}"


# =============================================================================
# HAND-CRAFTED MODELS (Not in Agent API - for Sandbox Management)
# =============================================================================

class Resources(BaseModel):
    """Resource specifications."""
    
    vcpu: int = Field(..., description="Number of vCPUs")
    memory_mb: int = Field(..., description="Memory in MB")
    disk_mb: int = Field(..., description="Disk size in MB")


class SandboxInfo(BaseModel):
    """Sandbox information."""
    
    sandbox_id: str = Field(..., description="Sandbox ID")
    template_id: Optional[str] = Field(None, description="Template ID")
    template_name: Optional[str] = Field(None, description="Template name")
    organization_id: int = Field(..., description="Organization ID")
    node_id: Optional[str] = Field(None, description="Node ID where VM is running")
    region: Optional[str] = Field(None, description="Region")
    status: str = Field(..., description="Sandbox status (running, stopped, paused, creating)")
    public_host: str = Field(..., description="Public URL to access sandbox")
    resources: Optional[Resources] = Field(None, description="Resource allocation")
    started_at: Optional[datetime] = Field(None, description="When sandbox started")
    end_at: Optional[datetime] = Field(None, description="When sandbox will be terminated")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    def __repr__(self) -> str:
        return f"<SandboxInfo {self.sandbox_id}: {self.status}>"
    
    def __str__(self) -> str:
        return f"SandboxInfo(sandbox_id={self.sandbox_id}, status={self.status}, url={self.public_host})"


class TemplateResources(BaseModel):
    """Template resource specifications."""
    
    vcpu: Optional[int] = None
    memory_mb: Optional[int] = None
    disk_gb: Optional[int] = None


class Template(BaseModel):
    """VM template."""
    
    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name (slug)")
    display_name: str = Field(..., description="Display name")
    description: Optional[str] = Field(None, description="Description")
    category: Optional[str] = Field(None, description="Category")
    language: Optional[str] = Field(None, description="Primary language")
    icon: Optional[str] = Field(None, description="Icon URL or emoji")
    default_resources: Optional[TemplateResources] = None
    min_resources: Optional[TemplateResources] = None
    max_resources: Optional[TemplateResources] = None
    features: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    popularity_score: Optional[int] = None
    docs_url: Optional[str] = None
    is_active: bool = Field(default=True)
    
    def __repr__(self) -> str:
        return f"<Template {self.name}: {self.display_name}>"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enhanced models (auto-generated + convenience)
    "ExecutionResult",
    "CommandResult",
    "FileInfo",
    "RichOutput",
    "VNCInfo",
    "WindowInfo",
    "RecordingInfo",
    "DisplayInfo",
    
    # Hand-crafted models
    "SandboxInfo",
    "Template",
    "Resources",
    "TemplateResources",
    
    # Auto-generated models (direct exports)
    "Language",
    "ErrorResponse",
    "ErrorCode",
    "MetricsSnapshot",
    "SystemMetrics",
    "HealthResponse",
    "FileListResponse",
    "FileContentResponse",
    "FileWriteRequest",
    "FileResponse",
    "ScreenshotResponse",
]

