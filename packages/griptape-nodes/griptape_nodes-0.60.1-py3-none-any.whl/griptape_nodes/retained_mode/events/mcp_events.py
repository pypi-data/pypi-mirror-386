"""MCP (Model Context Protocol) server management events."""

from dataclasses import dataclass
from typing import Any, TypedDict

from griptape_nodes.retained_mode.events.base_events import (
    RequestPayload,
    ResultPayloadFailure,
    ResultPayloadSuccess,
    WorkflowAlteredMixin,
    WorkflowNotAlteredMixin,
)
from griptape_nodes.retained_mode.events.payload_registry import PayloadRegistry


# Type definitions for better clarity
class MCPServerConfig(TypedDict, total=False):
    """Configuration for an MCP server."""

    name: str
    transport: str  # Transport protocol type
    enabled: bool
    command: str | None  # Process command for stdio transport
    args: list[str] | None  # Process arguments for stdio transport
    env: dict[str, str] | None  # Environment variables for stdio transport
    cwd: str | None  # Working directory for stdio transport
    encoding: str  # Text encoding for stdio transport
    encoding_error_handler: str  # Error handling strategy for stdio transport
    url: str | None  # Connection URL for HTTP-based transports
    headers: dict[str, str] | None  # HTTP headers for HTTP-based transports
    timeout: float | None  # Connection timeout for HTTP-based transports
    sse_read_timeout: float | None  # Read timeout for SSE transport
    terminate_on_close: bool  # Session termination behavior for streamable HTTP transport
    description: str | None
    capabilities: list[str] | None


class MCPServerCapability(TypedDict):
    """Information about an MCP server capability."""

    name: str
    description: str | None
    input_schema: dict[str, Any] | None  # JSON schema for capability inputs
    output_schema: dict[str, Any] | None  # JSON schema for capability outputs


class MCPServerInfo(TypedDict, total=False):
    """Information about an MCP server."""

    name: str
    version: str | None  # Server version identifier
    description: str | None  # Human-readable server description
    capabilities: list[str] | None  # List of supported capability names


# MCP Server Management Events


# Capability Discovery Events
@dataclass
@PayloadRegistry.register
class DiscoverMCPServerCapabilitiesRequest(RequestPayload):
    """Discover capabilities from a running MCP server.

    Args:
        name: The MCP server identifier to discover capabilities from
        timeout: Maximum time to wait for server response in seconds
    """

    name: str
    timeout: int = 30


@dataclass
@PayloadRegistry.register
class DiscoverMCPServerCapabilitiesResultSuccess(WorkflowNotAlteredMixin, ResultPayloadSuccess):
    """MCP server capabilities discovered successfully."""

    name: str
    capabilities: list[str]
    detailed_tools: list[MCPServerCapability] | None = None
    server_info: MCPServerInfo | None = None


@dataclass
@PayloadRegistry.register
class DiscoverMCPServerCapabilitiesResultFailure(WorkflowNotAlteredMixin, ResultPayloadFailure):
    """Failed to discover MCP server capabilities."""


@dataclass
@PayloadRegistry.register
class ListMCPServersRequest(RequestPayload):
    """List all configured MCP servers.

    Args:
        include_disabled: Whether to include disabled servers in the results
    """

    include_disabled: bool = False


@dataclass
@PayloadRegistry.register
class ListMCPServersResultSuccess(WorkflowNotAlteredMixin, ResultPayloadSuccess):
    """MCP servers listed successfully."""

    servers: dict[str, MCPServerConfig]


@dataclass
@PayloadRegistry.register
class ListMCPServersResultFailure(WorkflowNotAlteredMixin, ResultPayloadFailure):
    """Failed to list MCP servers."""


@dataclass
@PayloadRegistry.register
class GetMCPServerRequest(RequestPayload):
    """Get configuration for a specific MCP server.

    Args:
        name: The unique identifier for the MCP server
    """

    name: str


@dataclass
@PayloadRegistry.register
class GetMCPServerResultSuccess(WorkflowNotAlteredMixin, ResultPayloadSuccess):
    """MCP server configuration retrieved successfully."""

    server_config: MCPServerConfig


@dataclass
@PayloadRegistry.register
class GetMCPServerResultFailure(WorkflowNotAlteredMixin, ResultPayloadFailure):
    """Failed to get MCP server configuration."""


@dataclass
@PayloadRegistry.register
class CreateMCPServerRequest(RequestPayload):
    """Create a new MCP server configuration.

    Args:
        name: Unique identifier for the server
        transport: Transport protocol type
        command: Process command to start the server (required for stdio transport)
        args: Process arguments to pass to the command (stdio transport)
        env: Environment variables for the server process (stdio transport)
        cwd: Working directory for the server process (stdio transport)
        encoding: Text encoding for stdio communication
        encoding_error_handler: Encoding error handling strategy for stdio
        url: Connection URL for HTTP-based transports
        headers: HTTP headers for HTTP-based connections
        timeout: Connection timeout in seconds
        sse_read_timeout: SSE read timeout in seconds
        terminate_on_close: Session termination behavior for streamable HTTP transport
        description: Optional description of the server
        capabilities: List of server capabilities
        enabled: Whether the server is enabled by default
    """

    name: str
    transport: str = "stdio"
    enabled: bool = True

    # StdioConnection fields
    command: str | None = None
    args: list[str] | None = None
    env: dict[str, str] | None = None
    cwd: str | None = None
    encoding: str = "utf-8"
    encoding_error_handler: str = "strict"

    # HTTP-based connection fields
    url: str | None = None
    headers: dict[str, str] | None = None
    timeout: float | None = None
    sse_read_timeout: float | None = None
    terminate_on_close: bool = True

    # Common fields
    description: str | None = None
    capabilities: list[str] | None = None


@dataclass
@PayloadRegistry.register
class CreateMCPServerResultSuccess(WorkflowAlteredMixin, ResultPayloadSuccess):
    """MCP server created successfully."""

    name: str


@dataclass
@PayloadRegistry.register
class CreateMCPServerResultFailure(WorkflowAlteredMixin, ResultPayloadFailure):
    """Failed to create MCP server."""


@dataclass
@PayloadRegistry.register
class UpdateMCPServerRequest(RequestPayload):
    """Update an existing MCP server configuration.

    Args:
        name: The unique identifier for the MCP server
        new_name: Updated display name for the server
        transport: Updated transport protocol type
        command: Updated process command to start the server (stdio transport)
        args: Updated process arguments to pass to the command (stdio transport)
        env: Updated environment variables for the server process (stdio transport)
        cwd: Updated working directory for the server process (stdio transport)
        encoding: Updated text encoding for stdio communication
        encoding_error_handler: Updated encoding error handling strategy for stdio
        url: Updated connection URL for HTTP-based transports
        headers: Updated HTTP headers for HTTP-based connections
        timeout: Updated connection timeout in seconds
        sse_read_timeout: Updated SSE read timeout in seconds
        terminate_on_close: Updated session termination behavior for streamable HTTP transport
        description: Updated description of the server
        capabilities: Updated list of server capabilities
    """

    name: str
    new_name: str | None = None
    transport: str | None = None
    enabled: bool | None = None

    # StdioConnection fields
    command: str | None = None
    args: list[str] | None = None
    env: dict[str, str] | None = None
    cwd: str | None = None
    encoding: str | None = None
    encoding_error_handler: str | None = None

    # HTTP-based connection fields
    url: str | None = None
    headers: dict[str, str] | None = None
    timeout: float | None = None
    sse_read_timeout: float | None = None
    terminate_on_close: bool | None = None

    # Common fields
    description: str | None = None
    capabilities: list[str] | None = None


@dataclass
@PayloadRegistry.register
class UpdateMCPServerResultSuccess(WorkflowAlteredMixin, ResultPayloadSuccess):
    """MCP server updated successfully."""

    name: str


@dataclass
@PayloadRegistry.register
class UpdateMCPServerResultFailure(WorkflowAlteredMixin, ResultPayloadFailure):
    """Failed to update MCP server."""


@dataclass
@PayloadRegistry.register
class DeleteMCPServerRequest(RequestPayload):
    """Delete an MCP server configuration.

    Args:
        name: The unique identifier for the MCP server to delete
    """

    name: str


@dataclass
@PayloadRegistry.register
class DeleteMCPServerResultSuccess(WorkflowAlteredMixin, ResultPayloadSuccess):
    """MCP server deleted successfully."""

    name: str


@dataclass
@PayloadRegistry.register
class DeleteMCPServerResultFailure(WorkflowAlteredMixin, ResultPayloadFailure):
    """Failed to delete MCP server."""


@dataclass
@PayloadRegistry.register
class EnableMCPServerRequest(RequestPayload):
    """Enable an MCP server.

    Args:
        name: The unique identifier for the MCP server to enable
    """

    name: str


@dataclass
@PayloadRegistry.register
class EnableMCPServerResultSuccess(WorkflowAlteredMixin, ResultPayloadSuccess):
    """MCP server enabled successfully."""

    name: str


@dataclass
@PayloadRegistry.register
class EnableMCPServerResultFailure(WorkflowAlteredMixin, ResultPayloadFailure):
    """Failed to enable MCP server."""


@dataclass
@PayloadRegistry.register
class DisableMCPServerRequest(RequestPayload):
    """Disable an MCP server.

    Args:
        name: The unique identifier for the MCP server to disable
    """

    name: str


@dataclass
@PayloadRegistry.register
class DisableMCPServerResultSuccess(WorkflowAlteredMixin, ResultPayloadSuccess):
    """MCP server disabled successfully."""

    name: str


@dataclass
@PayloadRegistry.register
class DisableMCPServerResultFailure(WorkflowAlteredMixin, ResultPayloadFailure):
    """Failed to disable MCP server."""


@dataclass
@PayloadRegistry.register
class GetEnabledMCPServersRequest(RequestPayload):
    """Get all enabled MCP servers."""


@dataclass
@PayloadRegistry.register
class GetEnabledMCPServersResultSuccess(WorkflowNotAlteredMixin, ResultPayloadSuccess):
    """Enabled MCP servers retrieved successfully."""

    servers: dict[str, MCPServerConfig]


@dataclass
@PayloadRegistry.register
class GetEnabledMCPServersResultFailure(WorkflowNotAlteredMixin, ResultPayloadFailure):
    """Failed to get enabled MCP servers."""
