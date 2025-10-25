from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from griptape_nodes.retained_mode.events.base_events import (
    RequestPayload,
    ResultPayloadFailure,
    ResultPayloadSuccess,
    WorkflowNotAlteredMixin,
)
from griptape_nodes.retained_mode.events.payload_registry import PayloadRegistry

if TYPE_CHECKING:
    from griptape_nodes.retained_mode.managers.resource_components.resource_instance import Requirements
    from griptape_nodes.retained_mode.managers.resource_components.resource_type import ResourceType
    from griptape_nodes.retained_mode.managers.resource_manager import ResourceStatus


# List Registered Resource Types Events
@dataclass
@PayloadRegistry.register
class ListRegisteredResourceTypesRequest(RequestPayload):
    """List all registered resource types.

    Use when: Discovering what types of resources are available for allocation
    and management.
    """


@dataclass
@PayloadRegistry.register
class ListRegisteredResourceTypesResultSuccess(WorkflowNotAlteredMixin, ResultPayloadSuccess):
    """Registered resource types listed successfully."""

    resource_type_names: list[str]


@dataclass
@PayloadRegistry.register
class ListRegisteredResourceTypesResultFailure(WorkflowNotAlteredMixin, ResultPayloadFailure):
    """Registered resource types listing failed."""


# Register Resource Type Events
@dataclass
@PayloadRegistry.register
class RegisterResourceTypeRequest(RequestPayload):
    """Register a new resource type handler.

    Use when: Adding support for a new type of resource (GPU, CPU, Pipeline, etc.)
    that the ResourceManager should be able to allocate and manage.

    Args:
        resource_type: The ResourceType instance to register
    """

    resource_type: "ResourceType"


@dataclass
@PayloadRegistry.register
class RegisterResourceTypeResultSuccess(WorkflowNotAlteredMixin, ResultPayloadSuccess):
    """Resource type registered successfully."""


@dataclass
@PayloadRegistry.register
class RegisterResourceTypeResultFailure(WorkflowNotAlteredMixin, ResultPayloadFailure):
    """Resource type registration failed. Common causes: resource type already registered, invalid resource type."""


# Create Resource Instance Events
@dataclass
@PayloadRegistry.register
class CreateResourceInstanceRequest(RequestPayload):
    """Create a new resource instance.

    Use when: Creating a new instance of a resource that can be tracked, locked,
    and managed by the ResourceManager.

    Args:
        resource_type_name: The name of the resource type to create an instance of
        capabilities: Dict of capabilities for the new instance
    """

    resource_type_name: str
    capabilities: dict[str, Any]


@dataclass
@PayloadRegistry.register
class CreateResourceInstanceResultSuccess(WorkflowNotAlteredMixin, ResultPayloadSuccess):
    """Resource instance created successfully."""

    instance_id: str


@dataclass
@PayloadRegistry.register
class CreateResourceInstanceResultFailure(WorkflowNotAlteredMixin, ResultPayloadFailure):
    """Resource instance creation failed. Common causes: invalid capabilities, resource creation error."""


# Free Resource Instance Events
@dataclass
@PayloadRegistry.register
class FreeResourceInstanceRequest(RequestPayload):
    """Free a resource instance.

    Use when: Permanently removing a resource instance from tracking and freeing
    its resources.

    Args:
        instance_id: The ID of the instance to free
        force_unlock: If True, force unlock locked instances. If False, raise exception for locked instances.
    """

    instance_id: str
    force_unlock: bool = False


@dataclass
@PayloadRegistry.register
class FreeResourceInstanceResultSuccess(WorkflowNotAlteredMixin, ResultPayloadSuccess):
    """Resource instance freed successfully."""


@dataclass
@PayloadRegistry.register
class FreeResourceInstanceResultFailure(WorkflowNotAlteredMixin, ResultPayloadFailure):
    """Resource instance freeing failed. Common causes: instance not found, instance locked and force_unlock=False."""


# Acquire Resource Lock Events
@dataclass
@PayloadRegistry.register
class AcquireResourceInstanceLockRequest(RequestPayload):
    """Acquire a lock on an existing resource instance.

    Use when: Attempting to acquire exclusive access to a resource instance that
    matches specific requirements.

    Args:
        owner_id: The ID of the entity requesting the lock
        resource_type_name: The name of the resource type to acquire
        requirements: Optional requirements the resource must satisfy
    """

    owner_id: str
    resource_type_name: str
    requirements: "Requirements | None" = None


@dataclass
@PayloadRegistry.register
class AcquireResourceInstanceLockResultSuccess(WorkflowNotAlteredMixin, ResultPayloadSuccess):
    """Resource instance lock acquired successfully."""

    instance_id: str


@dataclass
@PayloadRegistry.register
class AcquireResourceInstanceLockResultFailure(WorkflowNotAlteredMixin, ResultPayloadFailure):
    """Resource instance lock acquisition failed. Common causes: no compatible instances available, all instances locked."""


# Release Resource Lock Events
@dataclass
@PayloadRegistry.register
class ReleaseResourceInstanceLockRequest(RequestPayload):
    """Release a lock on a resource instance.

    Use when: Releasing exclusive access to a resource instance that was
    previously acquired.

    Args:
        instance_id: The ID of the resource instance to release
        owner_id: The ID of the entity releasing the lock
    """

    instance_id: str
    owner_id: str


@dataclass
@PayloadRegistry.register
class ReleaseResourceInstanceLockResultSuccess(WorkflowNotAlteredMixin, ResultPayloadSuccess):
    """Resource instance lock released successfully."""


@dataclass
@PayloadRegistry.register
class ReleaseResourceInstanceLockResultFailure(WorkflowNotAlteredMixin, ResultPayloadFailure):
    """Resource instance lock release failed. Common causes: instance not found, not locked by specified owner."""


# List Compatible Resource Instances Events
@dataclass
@PayloadRegistry.register
class ListCompatibleResourceInstancesRequest(RequestPayload):
    """List resource instances compatible with requirements.

    Use when: Discovering what resource instances are available that match
    specific criteria, without acquiring locks.

    Args:
        resource_type_name: The name of the resource type to filter by
        requirements: Optional requirements to match. If None, returns all instances of the type.
        include_locked: If True, also include locked instances
    """

    resource_type_name: str
    requirements: "Requirements | None" = None
    include_locked: bool = False


@dataclass
@PayloadRegistry.register
class ListCompatibleResourceInstancesResultSuccess(WorkflowNotAlteredMixin, ResultPayloadSuccess):
    """Compatible resource instances listed successfully."""

    instance_ids: list[str]


@dataclass
@PayloadRegistry.register
class ListCompatibleResourceInstancesResultFailure(WorkflowNotAlteredMixin, ResultPayloadFailure):
    """Compatible resource instances listing failed. Common causes: invalid resource type, invalid requirements."""


# Get Resource Instance Status Events
@dataclass
@PayloadRegistry.register
class GetResourceInstanceStatusRequest(RequestPayload):
    """Get status information for a resource instance.

    Use when: Checking the current state of a specific resource instance,
    including capabilities and lock status.

    Args:
        instance_id: The ID of the instance to get status for
    """

    instance_id: str


@dataclass
@PayloadRegistry.register
class GetResourceInstanceStatusResultSuccess(WorkflowNotAlteredMixin, ResultPayloadSuccess):
    """Resource instance status retrieved successfully."""

    status: "ResourceStatus"


@dataclass
@PayloadRegistry.register
class GetResourceInstanceStatusResultFailure(WorkflowNotAlteredMixin, ResultPayloadFailure):
    """Resource instance status retrieval failed. Common causes: instance not found."""


# List Resource Instances By Type Events
@dataclass
@PayloadRegistry.register
class ListResourceInstancesByTypeRequest(RequestPayload):
    """List resource instances of a specific type.

    Use when: Listing all instances of a particular resource type for
    management or monitoring purposes.

    Args:
        resource_type_name: The name of the resource type to list instances for
        include_locked: If True, also include locked instances
    """

    resource_type_name: str
    include_locked: bool = True


@dataclass
@PayloadRegistry.register
class ListResourceInstancesByTypeResultSuccess(WorkflowNotAlteredMixin, ResultPayloadSuccess):
    """Resource instances by type listed successfully."""

    instance_ids: list[str]


@dataclass
@PayloadRegistry.register
class ListResourceInstancesByTypeResultFailure(WorkflowNotAlteredMixin, ResultPayloadFailure):
    """Resource instances by type listing failed. Common causes: invalid resource type."""
