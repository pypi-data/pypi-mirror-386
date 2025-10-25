import copy
import logging
import pickle
from typing import Any, NamedTuple, cast
from uuid import uuid4

from griptape_nodes.exe_types.core_types import (
    BaseNodeElement,
    Parameter,
    ParameterContainer,
    ParameterGroup,
    ParameterMessage,
    ParameterMode,
    ParameterType,
    ParameterTypeBuiltin,
)
from griptape_nodes.exe_types.flow import ControlFlow
from griptape_nodes.exe_types.node_types import (
    BaseNode,
    EndLoopNode,
    ErrorProxyNode,
    NodeDependencies,
    NodeGroupProxyNode,
    NodeResolutionState,
    StartLoopNode,
)
from griptape_nodes.exe_types.type_validator import TypeValidator
from griptape_nodes.machines.sequential_resolution import SequentialResolutionMachine
from griptape_nodes.node_library.library_registry import LibraryNameAndVersion, LibraryRegistry
from griptape_nodes.retained_mode.events.base_events import (
    ResultDetails,
    ResultPayload,
    ResultPayloadFailure,
)
from griptape_nodes.retained_mode.events.connection_events import (
    CreateConnectionRequest,
    CreateConnectionResultSuccess,
    DeleteConnectionRequest,
    DeleteConnectionResultFailure,
    DeleteConnectionResultSuccess,
    IncomingConnection,
    ListConnectionsForNodeRequest,
    ListConnectionsForNodeResultFailure,
    ListConnectionsForNodeResultSuccess,
    OutgoingConnection,
)
from griptape_nodes.retained_mode.events.execution_events import (
    CancelFlowRequest,
    ResolveNodeRequest,
    ResolveNodeResultFailure,
    ResolveNodeResultSuccess,
    StartFlowResultFailure,
)
from griptape_nodes.retained_mode.events.flow_events import (
    ListNodesInFlowRequest,
    ListNodesInFlowResultSuccess,
)
from griptape_nodes.retained_mode.events.library_events import (
    GetLibraryMetadataRequest,
    GetLibraryMetadataResultSuccess,
)
from griptape_nodes.retained_mode.events.node_events import (
    BatchSetNodeMetadataRequest,
    BatchSetNodeMetadataResultFailure,
    BatchSetNodeMetadataResultSuccess,
    CreateNodeRequest,
    CreateNodeResultFailure,
    CreateNodeResultSuccess,
    DeleteNodeRequest,
    DeleteNodeResultFailure,
    DeleteNodeResultSuccess,
    DeserializeNodeFromCommandsRequest,
    DeserializeNodeFromCommandsResultFailure,
    DeserializeNodeFromCommandsResultSuccess,
    DeserializeSelectedNodesFromCommandsRequest,
    DeserializeSelectedNodesFromCommandsResultFailure,
    DeserializeSelectedNodesFromCommandsResultSuccess,
    DuplicateSelectedNodesRequest,
    DuplicateSelectedNodesResultFailure,
    DuplicateSelectedNodesResultSuccess,
    GetAllNodeInfoRequest,
    GetAllNodeInfoResultFailure,
    GetAllNodeInfoResultSuccess,
    GetFlowForNodeRequest,
    GetFlowForNodeResultFailure,
    GetFlowForNodeResultSuccess,
    GetNodeMetadataRequest,
    GetNodeMetadataResultFailure,
    GetNodeMetadataResultSuccess,
    GetNodeResolutionStateRequest,
    GetNodeResolutionStateResultFailure,
    GetNodeResolutionStateResultSuccess,
    ListParametersOnNodeRequest,
    ListParametersOnNodeResultFailure,
    ListParametersOnNodeResultSuccess,
    SendNodeMessageRequest,
    SendNodeMessageResultFailure,
    SendNodeMessageResultSuccess,
    SerializedNodeCommands,
    SerializedParameterValueTracker,
    SerializedSelectedNodesCommands,
    SerializeNodeToCommandsRequest,
    SerializeNodeToCommandsResultFailure,
    SerializeNodeToCommandsResultSuccess,
    SerializeSelectedNodesToCommandsRequest,
    SerializeSelectedNodesToCommandsResultSuccess,
    SetLockNodeStateRequest,
    SetLockNodeStateResultFailure,
    SetLockNodeStateResultSuccess,
    SetNodeMetadataRequest,
    SetNodeMetadataResultFailure,
    SetNodeMetadataResultSuccess,
)
from griptape_nodes.retained_mode.events.parameter_events import (
    AddParameterToNodeRequest,
    AddParameterToNodeResultFailure,
    AddParameterToNodeResultSuccess,
    AlterParameterDetailsRequest,
    AlterParameterDetailsResultFailure,
    AlterParameterDetailsResultSuccess,
    GetCompatibleParametersRequest,
    GetCompatibleParametersResultFailure,
    GetCompatibleParametersResultSuccess,
    GetConnectionsForParameterRequest,
    GetConnectionsForParameterResultFailure,
    GetConnectionsForParameterResultSuccess,
    GetNodeElementDetailsRequest,
    GetNodeElementDetailsResultFailure,
    GetNodeElementDetailsResultSuccess,
    GetParameterDetailsRequest,
    GetParameterDetailsResultFailure,
    GetParameterDetailsResultSuccess,
    GetParameterValueRequest,
    GetParameterValueResultFailure,
    GetParameterValueResultSuccess,
    MigrateParameterRequest,
    MigrateParameterResultFailure,
    MigrateParameterResultSuccess,
    ParameterAndMode,
    RemoveParameterFromNodeRequest,
    RemoveParameterFromNodeResultFailure,
    RemoveParameterFromNodeResultSuccess,
    RenameParameterRequest,
    RenameParameterResultFailure,
    RenameParameterResultSuccess,
    SetParameterValueRequest,
    SetParameterValueResultFailure,
    SetParameterValueResultSuccess,
)
from griptape_nodes.retained_mode.events.validation_events import (
    ValidateNodeDependenciesRequest,
    ValidateNodeDependenciesResultFailure,
    ValidateNodeDependenciesResultSuccess,
)
from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes
from griptape_nodes.retained_mode.managers.event_manager import EventManager
from griptape_nodes.retained_mode.retained_mode import RetainedMode

logger = logging.getLogger("griptape_nodes")


class SerializedParameterValues(NamedTuple):
    """Result of serializing parameter output values.

    Attributes:
        parameter_output_values: Either raw values or UUID references if pickling was used
        unique_parameter_uuid_to_values: Dictionary of pickled values (None if no pickling needed)
    """

    parameter_output_values: dict[str, Any]
    unique_parameter_uuid_to_values: dict[Any, Any] | None


class NodeManager:
    _name_to_parent_flow_name: dict[str, str]

    def __init__(self, event_manager: EventManager) -> None:
        self._name_to_parent_flow_name = {}

        event_manager.assign_manager_to_request_type(CreateNodeRequest, self.on_create_node_request)
        event_manager.assign_manager_to_request_type(DeleteNodeRequest, self.on_delete_node_request)
        event_manager.assign_manager_to_request_type(
            GetNodeResolutionStateRequest, self.on_get_node_resolution_state_request
        )
        event_manager.assign_manager_to_request_type(GetNodeMetadataRequest, self.on_get_node_metadata_request)
        event_manager.assign_manager_to_request_type(SetNodeMetadataRequest, self.on_set_node_metadata_request)
        event_manager.assign_manager_to_request_type(
            BatchSetNodeMetadataRequest, self.on_batch_set_node_metadata_request
        )
        event_manager.assign_manager_to_request_type(
            ListConnectionsForNodeRequest, self.on_list_connections_for_node_request
        )
        event_manager.assign_manager_to_request_type(
            GetConnectionsForParameterRequest, self.on_get_connections_for_parameter_request
        )
        event_manager.assign_manager_to_request_type(
            ListParametersOnNodeRequest, self.on_list_parameters_on_node_request
        )
        event_manager.assign_manager_to_request_type(AddParameterToNodeRequest, self.on_add_parameter_to_node_request)
        event_manager.assign_manager_to_request_type(
            RemoveParameterFromNodeRequest, self.on_remove_parameter_from_node_request
        )
        event_manager.assign_manager_to_request_type(GetParameterDetailsRequest, self.on_get_parameter_details_request)
        event_manager.assign_manager_to_request_type(
            AlterParameterDetailsRequest, self.on_alter_parameter_details_request
        )
        event_manager.assign_manager_to_request_type(GetParameterValueRequest, self.on_get_parameter_value_request)
        event_manager.assign_manager_to_request_type(SetParameterValueRequest, self.on_set_parameter_value_request)
        event_manager.assign_manager_to_request_type(RenameParameterRequest, self.on_rename_parameter_request)
        event_manager.assign_manager_to_request_type(MigrateParameterRequest, self.on_migrate_parameter_request)
        event_manager.assign_manager_to_request_type(ResolveNodeRequest, self.on_resolve_from_node_request)
        event_manager.assign_manager_to_request_type(GetAllNodeInfoRequest, self.on_get_all_node_info_request)
        event_manager.assign_manager_to_request_type(
            GetCompatibleParametersRequest, self.on_get_compatible_parameters_request
        )
        event_manager.assign_manager_to_request_type(
            ValidateNodeDependenciesRequest, self.on_validate_node_dependencies_request
        )
        event_manager.assign_manager_to_request_type(
            GetNodeElementDetailsRequest, self.on_get_node_element_details_request
        )
        event_manager.assign_manager_to_request_type(SerializeNodeToCommandsRequest, self.on_serialize_node_to_commands)
        event_manager.assign_manager_to_request_type(
            DeserializeNodeFromCommandsRequest, self.on_deserialize_node_from_commands
        )
        event_manager.assign_manager_to_request_type(
            SerializeSelectedNodesToCommandsRequest, self.on_serialize_selected_nodes_to_commands
        )
        event_manager.assign_manager_to_request_type(
            DeserializeSelectedNodesFromCommandsRequest, self.on_deserialize_selected_nodes_from_commands
        )
        event_manager.assign_manager_to_request_type(DuplicateSelectedNodesRequest, self.on_duplicate_selected_nodes)
        event_manager.assign_manager_to_request_type(SetLockNodeStateRequest, self.on_toggle_lock_node_request)
        event_manager.assign_manager_to_request_type(GetFlowForNodeRequest, self.on_get_flow_for_node_request)
        event_manager.assign_manager_to_request_type(SendNodeMessageRequest, self.on_send_node_message_request)

    def handle_node_rename(self, old_name: str, new_name: str) -> None:
        # Get the node itself
        node = self.get_node_by_name(old_name)
        # Get all connections for this node and update them.
        flow_name = self.get_node_parent_flow_by_name(old_name)
        flow = GriptapeNodes.FlowManager().get_flow_by_name(flow_name)
        connections = GriptapeNodes.FlowManager().get_connections()
        # Get all incoming and outgoing connections and update them.
        if old_name in connections.incoming_index:
            incoming_connections = connections.incoming_index[old_name]
            for connection_ids in incoming_connections.values():
                for connection_id in connection_ids:
                    connection = connections.connections[connection_id]
                    connection.target_node.name = new_name
            temp = connections.incoming_index.pop(old_name)
            connections.incoming_index[new_name] = temp
        if old_name in connections.outgoing_index:
            outgoing_connections = connections.outgoing_index[old_name]
            for connection_ids in outgoing_connections.values():
                for connection_id in connection_ids:
                    connection = connections.connections[connection_id]
                    connection.source_node.name = new_name
            temp = connections.outgoing_index.pop(old_name)
            connections.outgoing_index[new_name] = temp
        # update the node in the flow!
        flow.remove_node(old_name)
        node.name = new_name
        flow.add_node(node)
        # Replace the old node name and its parent.
        parent = self._name_to_parent_flow_name[old_name]
        self._name_to_parent_flow_name[new_name] = parent
        del self._name_to_parent_flow_name[old_name]

    def handle_flow_rename(self, old_name: str, new_name: str) -> None:
        # Find all instances where a node had the old parent and update it to the new one.
        for node_name, parent_flow_name in self._name_to_parent_flow_name.items():
            if parent_flow_name == old_name:
                self._name_to_parent_flow_name[node_name] = new_name

    def on_create_node_request(self, request: CreateNodeRequest) -> ResultPayload:  # noqa: C901, PLR0912, PLR0915
        # Validate as much as possible before we actually create one.
        parent_flow_name = request.override_parent_flow_name
        parent_flow = None
        if parent_flow_name is None:
            # Try to get the current context flow
            if not GriptapeNodes.ContextManager().has_current_flow():
                details = (
                    "Attempted to create Node in the Current Context. Failed because the Current Context was empty."
                )
                return CreateNodeResultFailure(result_details=details)
            parent_flow = GriptapeNodes.ContextManager().get_current_flow()
            parent_flow_name = parent_flow.name

        # Does this flow actually exist?
        if parent_flow is None:
            flow_mgr = GriptapeNodes.FlowManager()
            try:
                parent_flow = flow_mgr.get_flow_by_name(parent_flow_name)
            except KeyError as err:
                details = f"Attempted to create Node of type '{request.node_type}'. Failed when attempting to find the parent Flow. Error: {err}"
                return CreateNodeResultFailure(result_details=details)

        # Now ensure that we're giving a valid name.
        requested_node_name = request.node_name
        if requested_node_name is None:
            # The ask is to use the node's DISPLAY name if no name was specified. If that's blank, we'll use the node type.
            try:
                dest_library = LibraryRegistry.get_library_for_node_type(
                    node_type=request.node_type, specific_library_name=request.specific_library_name
                )
            except KeyError as err:
                details = f"Attempted to create Node of type '{request.node_type}'. Failed when attempting to find the library this node type was in. Error: {err}"
                return CreateNodeResultFailure(result_details=details)

            node_metadata = dest_library.get_node_metadata(request.node_type)
            requested_node_name = node_metadata.display_name
            if not requested_node_name:
                # Fall back to the class name
                requested_node_name = request.node_type

        obj_mgr = GriptapeNodes.ObjectManager()
        final_node_name = obj_mgr.generate_name_for_object(
            type_name=request.node_type, requested_name=requested_node_name
        )
        remapped_requested_node_name = (request.node_name is not None) and (request.node_name != final_node_name)

        # OK, let's try and create the Node.
        node = None
        try:
            node = LibraryRegistry.create_node(
                name=final_node_name,
                node_type=request.node_type,
                specific_library_name=request.specific_library_name,
                metadata=request.metadata,
            )
        # modifying to exception to try to catch all possible issues with node creation.
        except Exception as err:
            import traceback

            traceback.print_exc()
            details = f"Could not create Node '{final_node_name}' of type '{request.node_type}': {err}"

            # Check if we should create an Error Proxy node instead of failing
            if request.create_error_proxy_on_failure:
                try:
                    # Create ErrorProxyNode directly since it needs special initialization
                    node = ErrorProxyNode(
                        name=final_node_name,
                        original_node_type=request.node_type,
                        original_library_name=request.specific_library_name or "Unknown",
                        failure_reason=str(err),
                        metadata=request.metadata,
                    )

                    logger.warning(
                        "Created Error Proxy (placeholder) node '%s' to substitute for failed '%s'",
                        final_node_name,
                        request.node_type,
                    )
                except Exception as proxy_err:
                    details = f"Failed to create Error Proxy (placeholder) node: {proxy_err}"
                    return CreateNodeResultFailure(result_details=details)
            else:
                return CreateNodeResultFailure(result_details=details)
        # Add it to the Flow.
        parent_flow.add_node(node)

        # Record keeping.
        obj_mgr.add_object_by_name(node.name, node)
        self._name_to_parent_flow_name[node.name] = parent_flow_name

        # We don't want to start in a resolving state, bump it back to unresolved.
        state = request.resolution
        if state == NodeResolutionState.RESOLVING:
            state = NodeResolutionState.UNRESOLVED
            logger.warning(
                "Node '%s' was created in a RESOLVING state. This is not allowed. Setting to UNRESOLVED.", node.name
            )
        node.state = NodeResolutionState(state)

        # See if we want to push this into the context of the current flow.
        if request.set_as_new_context:
            GriptapeNodes.ContextManager().push_node(node=node)

        # Success message based on whether we used Current Context or explicit flow
        if request.override_parent_flow_name is None:
            details = (
                f"Successfully created Node '{final_node_name}' in the Current Context (Flow '{parent_flow_name}')"
            )
        else:
            details = f"Successfully created Node '{final_node_name}' in Flow '{parent_flow_name}'"

        log_level = logging.DEBUG
        if remapped_requested_node_name:
            log_level = logging.WARNING
            details = f"{details}. WARNING: Had to rename from original node name requested '{request.node_name}' as an object with this name already existed."

        # Special handling for paired classes (e.g., create a Start node and it automatically creates a corresponding End node already connected).
        if isinstance(node, StartLoopNode) and not request.initial_setup:
            # If it's StartLoop, create an EndLoop and connect it to the StartLoop.
            # Get the class name of the node
            node_class_name = node.__class__.__name__

            # Get the opposing EndNode
            # TODO: (griptape) Get paired classes implemented so we dont need to do name stuff. https://github.com/griptape-ai/griptape-nodes/issues/1549
            end_class_name = node_class_name.replace("Start", "End")

            # Check and see if the class exists
            libraries_with_node_type = LibraryRegistry.get_libraries_with_node_type(end_class_name)
            if not libraries_with_node_type:
                msg = f"Attempted to create a paired set of nodes for Node '{final_node_name}'. Failed because paired class '{end_class_name}' does not exist for start class '{node_class_name}'. The corresponding node will have to be created by hand and attached manually."
                logger.error(msg)  # while this is bad, it's not unsalvageable, so we'll consider this a success.
            else:
                # Create the EndNode
                end_loop = GriptapeNodes.handle_request(
                    CreateNodeRequest(
                        node_type=end_class_name,
                        metadata={
                            "position": {"x": node.metadata["position"]["x"] + 650, "y": node.metadata["position"]["y"]}
                        },
                        override_parent_flow_name=parent_flow_name,
                    )
                )
                if not isinstance(end_loop, CreateNodeResultSuccess):
                    msg = f"Attempted to create a paried set of nodes for Node '{final_node_name}'. Failed because paired class '{end_class_name}' failed to get created. The corresponding node will have to be created by hand and attached manually."
                    logger.error(msg)  # while this is bad, it's not unsalvageable, so we'll consider this a success.
                else:
                    # Create Loop between output and input to the start node.
                    GriptapeNodes.handle_request(
                        CreateConnectionRequest(
                            source_node_name=node.name,
                            source_parameter_name="loop",
                            target_node_name=end_loop.node_name,
                            target_parameter_name="from_start",
                        )
                    )
                    end_node = self.get_node_by_name(end_loop.node_name)
                    if not isinstance(end_node, EndLoopNode):
                        msg = f"Attempted to create a paried set of nodes for Node '{final_node_name}'. Failed because paired node '{end_loop.node_name}' was not a proper EndLoop instance. The corresponding node will have to be created by hand and attached manually."
                        logger.error(
                            msg
                        )  # while this is bad, it's not unsalvageable, so we'll consider this a success.
                    else:
                        # create the connection - only when we've confirmed correct types
                        node.end_node = end_node
                        end_node.start_node = node

        return CreateNodeResultSuccess(
            node_name=node.name,
            node_type=node.__class__.__name__,
            specific_library_name=request.specific_library_name,
            result_details=ResultDetails(message=details, level=log_level),
        )

    def cancel_conditionally(
        self, parent_flow: ControlFlow, parent_flow_name: str, node: BaseNode
    ) -> ResultPayload | None:
        """Conditionally cancels a parent flow if it's currently executing nodes are connected to the specified node.

        This method checks if the parent flow is running, and if so, determines whether the currently
        executing or resolving node is connected to the specified node. If a connection exists, the parent
        flow is cancelled to prevent operations on the deleted node.

        Args:
            parent_flow: The control flow object that may need to be cancelled.
            parent_flow_name: The name of the parent flow for use in cancellation requests.
            node: The base node that is trying to be deleted.

        Returns:
            ResultPayload: A DeleteNodeResultFailure if cancellation was attempted but failed.
            None: If no cancellation was needed or cancellation succeeded.

        Note:
            This method also clears the flow queue regardless of whether cancellation occurred,
            to ensure the specified node is not processed in the future.
        """
        if GriptapeNodes.FlowManager().check_for_existing_running_flow():
            # get the current node executing / resolving
            # if it's in connected nodes, cancel flow.
            # otherwise, leave it.
            control_node_names, resolving_node_names, _ = GriptapeNodes.FlowManager().flow_state(parent_flow)
            connected_nodes = parent_flow.get_all_connected_nodes(node)
            cancelled = False
            if control_node_names is not None:
                for control_node_name in control_node_names:
                    control_node = GriptapeNodes.ObjectManager().get_object_by_name(control_node_name)
                    if control_node in connected_nodes:
                        result = GriptapeNodes.handle_request(CancelFlowRequest(flow_name=parent_flow_name))
                        cancelled = True
                        if not result.succeeded():
                            details = f"Attempted to delete a Node '{node.name}'. Failed because running flow could not cancel."
                            return DeleteNodeResultFailure(result_details=details)
            if resolving_node_names is not None and not cancelled:
                for resolving_node_name in resolving_node_names:
                    resolving_node = GriptapeNodes.ObjectManager().get_object_by_name(resolving_node_name)
                    if resolving_node in connected_nodes:
                        result = GriptapeNodes.handle_request(CancelFlowRequest(flow_name=parent_flow_name))
                        if not result.succeeded():
                            details = f"Attempted to delete a Node '{node.name}'. Failed because running flow could not cancel."
                            return DeleteNodeResultFailure(result_details=details)
                        break  # Only need to cancel once
            # Clear the execution queue, because we don't want to hit this node eventually.
            parent_flow.clear_execution_queue()
        return None

    def on_delete_node_request(self, request: DeleteNodeRequest) -> ResultPayload:  # noqa: C901, PLR0911, PLR0912 (complex logic, lots of edge cases)
        node_name = request.node_name
        node = None
        if node_name is None:
            # Get from the current context.
            if not GriptapeNodes.ContextManager().has_current_node():
                details = (
                    "Attempted to delete a Node from the Current Context. Failed because the Current Context is empty."
                )
                return DeleteNodeResultFailure(result_details=details)

            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name
        if node is None:
            node = GriptapeNodes.ObjectManager().attempt_get_object_by_name_as_type(node_name, BaseNode)
        if node is None:
            details = f"Attempted to delete a Node '{node_name}', but no such Node was found."
            return DeleteNodeResultFailure(result_details=details)

        with GriptapeNodes.ContextManager().node(node=node):
            parent_flow_name = self._name_to_parent_flow_name[node_name]
            try:
                parent_flow = GriptapeNodes.FlowManager().get_flow_by_name(parent_flow_name)
            except KeyError as err:
                details = f"Attempted to delete a Node '{node_name}'. Error: {err}"
                return DeleteNodeResultFailure(result_details=details)

            cancel_result = self.cancel_conditionally(parent_flow, parent_flow_name, node)
            if cancel_result is not None:
                return cancel_result
            # Remove all connections from this Node using a loop to handle cascading deletions
            any_connections_remain = True
            while any_connections_remain:
                # Assume we're done
                any_connections_remain = False

                list_node_connections_request = ListConnectionsForNodeRequest(node_name=node_name)
                list_connections_result = GriptapeNodes.handle_request(request=list_node_connections_request)
                if not isinstance(list_connections_result, ListConnectionsForNodeResultSuccess):
                    details = f"Attempted to delete a Node '{node_name}'. Failed because it could not gather Connections to the Node."
                    return DeleteNodeResultFailure(result_details=details)

                # Check incoming connections
                if list_connections_result.incoming_connections:
                    any_connections_remain = True
                    connection = list_connections_result.incoming_connections[0]
                    delete_request = DeleteConnectionRequest(
                        source_node_name=connection.source_node_name,
                        source_parameter_name=connection.source_parameter_name,
                        target_node_name=node_name,
                        target_parameter_name=connection.target_parameter_name,
                    )
                    delete_result = GriptapeNodes.handle_request(delete_request)
                    if isinstance(delete_result, ResultPayloadFailure):
                        details = (
                            f"Attempted to delete a Node '{node_name}'. Failed when attempting to delete Connection."
                        )
                        return DeleteNodeResultFailure(result_details=details)
                    continue  # Refresh connection list after cascading deletions

                # Check outgoing connections
                if list_connections_result.outgoing_connections:
                    any_connections_remain = True
                    connection = list_connections_result.outgoing_connections[0]
                    delete_request = DeleteConnectionRequest(
                        source_node_name=node_name,
                        source_parameter_name=connection.source_parameter_name,
                        target_node_name=connection.target_node_name,
                        target_parameter_name=connection.target_parameter_name,
                    )
                    delete_result = GriptapeNodes.handle_request(delete_request)
                    if isinstance(delete_result, ResultPayloadFailure):
                        details = (
                            f"Attempted to delete a Node '{node_name}'. Failed when attempting to delete Connection."
                        )
                        return DeleteNodeResultFailure(result_details=details)

        # Remove from the owning Flow
        parent_flow.remove_node(node.name)

        # Now remove the record keeping
        GriptapeNodes.ObjectManager().del_obj_by_name(node_name)
        del self._name_to_parent_flow_name[node_name]

        # If we were part of the Current Context, pop it.
        if request.node_name is None:
            GriptapeNodes.ContextManager().pop_node()

        details = f"Successfully deleted Node '{node_name}'."
        return DeleteNodeResultSuccess(result_details=details)

    def on_get_node_resolution_state_request(self, request: GetNodeResolutionStateRequest) -> ResultPayload:
        node_name = request.node_name
        node = None
        if node_name is None:
            # Get from the current context.
            if not GriptapeNodes.ContextManager().has_current_node():
                details = "Attempted to get resolution state for a Node from the Current Context. Failed because the Current Context is empty."
                return GetNodeResolutionStateResultFailure(result_details=details)

            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name

        if node is None:
            # Does this node exist?
            obj_mgr = GriptapeNodes.ObjectManager()
            node = obj_mgr.attempt_get_object_by_name_as_type(node_name, BaseNode)
            if node is None:
                details = f"Attempted to get resolution state for a Node '{node_name}', but no such Node was found."
                result = GetNodeResolutionStateResultFailure(result_details=details)
                return result

        node_state = node.state

        details = f"Successfully got resolution state for Node '{node_name}'."
        result = GetNodeResolutionStateResultSuccess(state=node_state.name, result_details=details)
        return result

    def on_get_node_metadata_request(self, request: GetNodeMetadataRequest) -> ResultPayload:
        node_name = request.node_name
        node = None
        if node_name is None:
            # Get from the current context.
            if not GriptapeNodes.ContextManager().has_current_node():
                details = "Attempted to get metadata for a Node from the Current Context. Failed because the Current Context is empty."
                return GetNodeMetadataResultFailure(result_details=details)

            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name

        # Does this node exist?
        if node is None:
            obj_mgr = GriptapeNodes.ObjectManager()

            node = obj_mgr.attempt_get_object_by_name_as_type(node_name, BaseNode)
            if node is None:
                details = f"Attempted to get metadata for a Node '{node_name}', but no such Node was found."

                result = GetNodeMetadataResultFailure(result_details=details)
                return result

        metadata = node.metadata
        details = f"Successfully retrieved metadata for a Node '{node_name}'."
        result = GetNodeMetadataResultSuccess(metadata=metadata, result_details=details)
        return result

    def on_set_node_metadata_request(self, request: SetNodeMetadataRequest) -> ResultPayload:
        node_name = request.node_name
        node = None
        if node_name is None:
            # Get from the current context.
            if not GriptapeNodes.ContextManager().has_current_node():
                details = "Attempted to set metadata for a Node from the Current Context. Failed because the Current Context is empty."
                return SetNodeMetadataResultFailure(result_details=details)

            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name

        # Does this node exist?
        if node is None:
            obj_mgr = GriptapeNodes.ObjectManager()

            node = obj_mgr.attempt_get_object_by_name_as_type(node_name, BaseNode)
            if node is None:
                details = f"Attempted to set metadata for a Node '{node_name}', but no such Node was found."

                result = SetNodeMetadataResultFailure(result_details=details)
                return result

        # We can't completely overwrite metadata.
        for key, value in request.metadata.items():
            node.metadata[key] = value
        details = f"Successfully set metadata for a Node '{node_name}'."
        result = SetNodeMetadataResultSuccess(result_details=details)
        return result

    def on_batch_set_node_metadata_request(self, request: BatchSetNodeMetadataRequest) -> ResultPayload:
        updated_nodes = []
        failed_nodes = {}

        for node_name, metadata_update in request.node_metadata_updates.items():
            # Resolve node name and get node object
            node = None
            if node_name is None:
                # Get from current context
                if not GriptapeNodes.ContextManager().has_current_node():
                    failed_nodes["current_context"] = "No current context node available"
                    continue
                node = GriptapeNodes.ContextManager().get_current_node()
                actual_node_name = node.name
            else:
                actual_node_name = node_name

            # Look up node if we don't have it yet
            if node is None:
                obj_mgr = GriptapeNodes.ObjectManager()
                node = obj_mgr.attempt_get_object_by_name_as_type(actual_node_name, BaseNode)
                if node is None:
                    failed_nodes[actual_node_name] = f"Node '{actual_node_name}' not found"
                    continue

            single_request = SetNodeMetadataRequest(node_name=actual_node_name, metadata=metadata_update)
            result = self.on_set_node_metadata_request(single_request)

            if isinstance(result, SetNodeMetadataResultSuccess):
                updated_nodes.append(actual_node_name)
            else:
                failed_nodes[actual_node_name] = result.result_details

        if failed_nodes:
            return BatchSetNodeMetadataResultFailure(
                result_details=f"Failed to update any nodes. Failed nodes: {failed_nodes}"
            )

        return BatchSetNodeMetadataResultSuccess(
            updated_nodes=updated_nodes,
            failed_nodes=failed_nodes,
            result_details=f"Successfully updated metadata for {len(updated_nodes)} nodes.",
        )

    def on_list_connections_for_node_request(self, request: ListConnectionsForNodeRequest) -> ResultPayload:
        node_name = request.node_name
        node = None
        if node_name is None:
            # Get from the current context.
            if not GriptapeNodes.ContextManager().has_current_node():
                details = "Attempted to list Connections for a Node from the Current Context. Failed because the Current Context is empty."
                return ListConnectionsForNodeResultFailure(result_details=details)

            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name

        # Does this node exist?
        if node is None:
            obj_mgr = GriptapeNodes.ObjectManager()

            node = obj_mgr.attempt_get_object_by_name_as_type(node_name, BaseNode)
            if node is None:
                details = f"Attempted to list Connections for a Node '{node_name}', but no such Node was found."

                result = ListConnectionsForNodeResultFailure(result_details=details)
                return result

        parent_flow_name = self._name_to_parent_flow_name[node_name]
        try:
            GriptapeNodes.FlowManager().get_flow_by_name(parent_flow_name)
        except KeyError as err:
            details = f"Attempted to list Connections for a Node '{node_name}'. Error: {err}"

            result = ListConnectionsForNodeResultFailure(result_details=details)
            return result

        # Kinda gross, but let's do it
        connection_mgr = GriptapeNodes.FlowManager().get_connections()
        # get outgoing connections
        outgoing_connections_list = []
        if node_name in connection_mgr.outgoing_index:
            outgoing_connections_list = [
                OutgoingConnection(
                    source_parameter_name=connection.source_parameter.name,
                    target_node_name=connection.target_node.name,
                    target_parameter_name=connection.target_parameter.name,
                )
                for connection_lists in connection_mgr.outgoing_index[node_name].values()
                for connection_id in connection_lists
                for connection in [connection_mgr.connections[connection_id]]
            ]
        # get incoming connections
        incoming_connections_list = []
        if node_name in connection_mgr.incoming_index:
            incoming_connections_list = [
                IncomingConnection(
                    source_node_name=connection.source_node.name,
                    source_parameter_name=connection.source_parameter.name,
                    target_parameter_name=connection.target_parameter.name,
                )
                for connection_lists in connection_mgr.incoming_index[node_name].values()
                for connection_id in connection_lists
                for connection in [
                    connection_mgr.connections[connection_id]
                ]  # This creates a temporary one-item list with the connection
            ]

        details = f"Successfully listed all Connections to and from Node '{node_name}'."
        result = ListConnectionsForNodeResultSuccess(
            incoming_connections=incoming_connections_list,
            outgoing_connections=outgoing_connections_list,
            result_details=details,
        )
        return result

    def on_get_connections_for_parameter_request(
        self, request: GetConnectionsForParameterRequest
    ) -> GetConnectionsForParameterResultFailure | GetConnectionsForParameterResultSuccess:
        parameter_name = request.parameter_name
        node_name = request.node_name
        node = None

        if node_name is None:
            # Get from the current context.
            if not GriptapeNodes.ContextManager().has_current_node():
                details = "Attempted to get connections for a parameter from the Current Context. Failed because the Current Context is empty."
                return GetConnectionsForParameterResultFailure(result_details=details)

            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name

        # Does this node exist?
        if node is None:
            obj_mgr = GriptapeNodes.ObjectManager()
            node = obj_mgr.attempt_get_object_by_name_as_type(node_name, BaseNode)
            if node is None:
                details = f"Attempted to get connections for parameter '{parameter_name}' on node '{node_name}', but no such node was found."
                return GetConnectionsForParameterResultFailure(result_details=details)

        # Does this parameter exist on the node?
        parameter = node.get_parameter_by_name(parameter_name)
        if parameter is None:
            details = f"Attempted to get connections for parameter '{parameter_name}' on node '{node_name}', but no such parameter was found."
            return GetConnectionsForParameterResultFailure(result_details=details)

        parent_flow_name = self._name_to_parent_flow_name[node_name]
        try:
            GriptapeNodes.FlowManager().get_flow_by_name(parent_flow_name)
        except KeyError as err:
            details = (
                f"Attempted to get connections for parameter '{parameter_name}' on node '{node_name}'. Error: {err}"
            )
            return GetConnectionsForParameterResultFailure(result_details=details)

        # Get connections for this specific parameter
        connection_mgr = GriptapeNodes.FlowManager().get_connections()

        # Get outgoing connections for this parameter
        outgoing_connections_list = []
        if node_name in connection_mgr.outgoing_index and parameter_name in connection_mgr.outgoing_index[node_name]:
            outgoing_connections_list = [
                OutgoingConnection(
                    source_parameter_name=connection.source_parameter.name,
                    target_node_name=connection.target_node.name,
                    target_parameter_name=connection.target_parameter.name,
                )
                for connection_id in connection_mgr.outgoing_index[node_name][parameter_name]
                for connection in [connection_mgr.connections[connection_id]]
            ]

        # Get incoming connections for this parameter
        incoming_connections_list = []
        if node_name in connection_mgr.incoming_index and parameter_name in connection_mgr.incoming_index[node_name]:
            incoming_connections_list = [
                IncomingConnection(
                    source_node_name=connection.source_node.name,
                    source_parameter_name=connection.source_parameter.name,
                    target_parameter_name=connection.target_parameter.name,
                )
                for connection_id in connection_mgr.incoming_index[node_name][parameter_name]
                for connection in [connection_mgr.connections[connection_id]]
            ]

        details = f"Successfully retrieved connections for parameter '{parameter_name}' on node '{node_name}'."
        result = GetConnectionsForParameterResultSuccess(
            parameter_name=parameter_name,
            node_name=node_name,
            incoming_connections=incoming_connections_list,
            outgoing_connections=outgoing_connections_list,
            result_details=details,
        )
        return result

    def on_list_parameters_on_node_request(self, request: ListParametersOnNodeRequest) -> ResultPayload:
        node_name = request.node_name
        node = None

        if node_name is None:
            # Get from the current context.
            if not GriptapeNodes.ContextManager().has_current_node():
                details = "Attempted to list Parameters for a Node from the Current Context. Failed because the Current Context is empty."
                return ListParametersOnNodeResultFailure(result_details=details)

            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name

        # Does this node exist?
        if node is None:
            obj_mgr = GriptapeNodes.ObjectManager()
            node = obj_mgr.attempt_get_object_by_name_as_type(node_name, BaseNode)
            if node is None:
                details = f"Attempted to list Parameters for a Node '{node_name}', but no such Node was found."

                result = ListParametersOnNodeResultFailure(result_details=details)
                return result

        ret_list = [param.name for param in node.parameters]

        details = f"Successfully listed Parameters for Node '{node_name}'."
        result = ListParametersOnNodeResultSuccess(parameter_names=ret_list, result_details=details)
        return result

    def generate_unique_parameter_name(self, node: BaseNode, base_name: str) -> str:
        """Generate a unique parameter name for a node by appending a number if needed.

        Args:
            node: The node to check for existing parameter names
            base_name: The desired base name for the parameter

        Returns:
            A unique parameter name that doesn't conflict with existing parameters
        """
        if node.get_parameter_by_name(base_name) is None:
            return base_name

        counter = 1
        while node.get_parameter_by_name(f"{base_name}_{counter}") is not None:
            counter += 1
        return f"{base_name}_{counter}"

    def on_add_parameter_to_node_request(self, request: AddParameterToNodeRequest) -> ResultPayload:  # noqa: C901, PLR0911, PLR0912, PLR0915
        node_name = request.node_name
        node = None
        parent_group: ParameterGroup | None = None

        if node_name is None:
            # Get from the current context.
            if not GriptapeNodes.ContextManager().has_current_node():
                details = "Attempted to add Parameter to a Node from the Current Context. Failed because the Current Context is empty."
                return AddParameterToNodeResultFailure(result_details=details)

            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name

        # Does this node exist?
        if node is None:
            obj_mgr = GriptapeNodes.ObjectManager()
            node = obj_mgr.attempt_get_object_by_name_as_type(node_name, BaseNode)
            if node is None:
                details = f"Attempted to add Parameter '{request.parameter_name}' to a Node '{node_name}', but no such Node was found."

                result = AddParameterToNodeResultFailure(result_details=details)
                return result

        # Check if node is locked
        if node.lock:
            details = f"Attempted to add Parameter '{request.parameter_name}' to Node '{node_name}'. Failed because the Node was locked."
            result = AddParameterToNodeResultFailure(result_details=details)
            return result

        if request.parent_container_name and not request.initial_setup:
            parameter = node.get_parameter_by_name(request.parent_container_name)
            if parameter is None:
                details = f"Attempted to add Parameter to Container Parameter '{request.parent_container_name}' in node '{node_name}'. Failed because parameter didn't exist."
                result = AddParameterToNodeResultFailure(result_details=details)
                return result
            if not isinstance(parameter, ParameterContainer):
                details = f"Attempted to add Parameter to Container Parameter '{request.parent_container_name}' in node '{node_name}'. Failed because parameter wasn't a container."
                result = AddParameterToNodeResultFailure(result_details=details)
                return result
            try:
                new_param = parameter.add_child_parameter()
            except Exception as e:
                details = f"Attempted to add Parameter to Container Parameter '{request.parent_container_name}' in node '{node_name}'. Failed: {e}."
                logger.exception(details)
                result = AddParameterToNodeResultFailure(result_details=details)
                return result

            return AddParameterToNodeResultSuccess(
                parameter_name=new_param.name,
                type=new_param.type,
                node_name=node_name,
                result_details=f"Successfully added parameter '{new_param.name}' to container parameter '{request.parent_container_name}' in node '{node_name}'.",
            )
        if request.parent_element_name is not None:
            parent_element = node.get_element_by_name_and_type(request.parent_element_name)
            if parent_element is None:
                details = f"Attempted to add Parameter to Parent Element '{request.parent_element_name}' in node '{node_name}'. Failed because element didn't exist."
                result = AddParameterToNodeResultFailure(result_details=details)
                return result
            # Handle ParameterGroup parentage with potential to expand in future to other element types.
            if isinstance(parent_element, ParameterGroup):
                parent_group = parent_element
        if request.parameter_name is None or request.tooltip is None:
            details = f"Attempted to add Parameter to node '{node_name}'. Failed because default_value, tooltip, or parameter_name was not defined."
            result = AddParameterToNodeResultFailure(result_details=details)
            return result

        # Generate a unique parameter name if needed
        requested_parameter_name = request.parameter_name
        if requested_parameter_name is None:
            # Not allowed to have a parameter with no name, so we'll give it a default name
            requested_parameter_name = "parameter"

        final_param_name = self.generate_unique_parameter_name(node, requested_parameter_name)

        # Let's see if the Parameter is properly formed.
        # If a Parameter is intended for Control, it needs to have that be the exclusive type.
        # The 'type', 'types', and 'output_type' are a little weird to handle (see Parameter definition for details)
        has_control_type = False
        has_non_control_types = False
        if request.type is not None:
            if request.type.lower() == ParameterTypeBuiltin.CONTROL_TYPE.value.lower():
                has_control_type = True
            else:
                has_non_control_types = True
        if request.input_types is not None:
            for test_type in request.input_types:
                if test_type.lower() == ParameterTypeBuiltin.CONTROL_TYPE.value.lower():
                    has_control_type = True
                else:
                    has_non_control_types = True
        if request.output_type is not None:
            if request.output_type.lower() == ParameterTypeBuiltin.CONTROL_TYPE.value.lower():
                has_control_type = True
            else:
                has_non_control_types = True

        if has_control_type and has_non_control_types:
            details = f"Attempted to add Parameter '{request.parameter_name}' to Node '{node_name}'. Failed because it had 'ParameterControlType' AND at least one other non-control type. If a Parameter is intended for control, it must only accept that type."

            result = AddParameterToNodeResultFailure(result_details=details)
            return result

        allowed_modes = set()
        if request.mode_allowed_input:
            allowed_modes.add(ParameterMode.INPUT)
        if request.mode_allowed_property:
            allowed_modes.add(ParameterMode.PROPERTY)
        if request.mode_allowed_output:
            allowed_modes.add(ParameterMode.OUTPUT)

        # Let's roll, I guess.
        new_param = Parameter(
            name=final_param_name,
            type=request.type,
            input_types=request.input_types,
            output_type=request.output_type,
            default_value=request.default_value,
            user_defined=request.is_user_defined,
            tooltip=request.tooltip,
            tooltip_as_input=request.tooltip_as_input,
            tooltip_as_property=request.tooltip_as_property,
            tooltip_as_output=request.tooltip_as_output,
            allowed_modes=allowed_modes,
            ui_options=request.ui_options,
            parent_container_name=request.parent_container_name,
            parent_element_name=parent_group.name if parent_group is not None else None,
            settable=request.settable,
        )
        try:
            if request.parent_container_name and request.initial_setup:
                parameter_parent = node.get_parameter_by_name(request.parent_container_name)
                if parameter_parent is not None:
                    parameter_parent.add_child(new_param)
            elif parent_group is not None:
                parent_group.add_child(new_param)
            else:
                node.add_parameter(new_param)
        except Exception as e:
            details = f"Couldn't add parameter with name {request.parameter_name} to Node '{node_name}'. Error: {e}"
            return AddParameterToNodeResultFailure(result_details=details)

        details = f"Successfully added Parameter '{final_param_name}' to Node '{node_name}'."
        log_level = logging.DEBUG
        if final_param_name != requested_parameter_name:
            log_level = logging.WARNING
            details = f"{details} WARNING: Had to rename from original parameter name '{requested_parameter_name}' as a parameter with this name already existed in node '{node_name}'."

        logger.log(level=log_level, msg=details)

        result = AddParameterToNodeResultSuccess(
            parameter_name=new_param.name, type=new_param.type, node_name=node_name, result_details=details
        )
        return result

    def on_remove_parameter_from_node_request(self, request: RemoveParameterFromNodeRequest) -> ResultPayload:  # noqa: C901, PLR0911, PLR0912, PLR0915
        node_name = request.node_name
        node = None

        if node_name is None:
            # Get the Current Context
            if not GriptapeNodes.ContextManager().has_current_node():
                details = f"Attempted to remove Parameter '{request.parameter_name}' from a Node, but no Current Context was found."

                result = RemoveParameterFromNodeResultFailure(result_details=details)
                return result

            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name

        # Does this node exist?
        if node is None:
            obj_mgr = GriptapeNodes.ObjectManager()
            node = obj_mgr.attempt_get_object_by_name_as_type(node_name, BaseNode)
            if node is None:
                details = f"Attempted to remove Parameter '{request.parameter_name}' from a Node '{node_name}', but no such Node was found."

                result = RemoveParameterFromNodeResultFailure(result_details=details)
                return result
        # Check if the node is locked
        if node.lock:
            details = f"Attempted to remove Element '{request.parameter_name}' from Node '{node_name}'. Failed because the Node was locked."

            result = RemoveParameterFromNodeResultFailure(result_details=details)
            return result
        # Does the Element actually exist on the Node?
        element = node.get_element_by_name_and_type(request.parameter_name)
        if element is None:
            details = f"Attempted to remove Element '{request.parameter_name}' from Node '{node_name}'. Failed because it didn't have an Element with that name on it."

            result = RemoveParameterFromNodeResultFailure(result_details=details)
            return result

        # If it's a ParameterGroup, we need to remove all the Parameters inside it.
        if isinstance(element, ParameterGroup):
            for child in element.find_elements_by_type(Parameter):
                GriptapeNodes.handle_request(RemoveParameterFromNodeRequest(child.name, node_name))
            node.remove_node_element(element)

            return RemoveParameterFromNodeResultSuccess(
                result_details=f"Successfully removed parameter group '{request.parameter_name}' and all its children from node '{node_name}'."
            )

        if isinstance(element, ParameterMessage):
            node.remove_node_element(element)

            return RemoveParameterFromNodeResultSuccess(
                result_details=f"Successfully removed parameter message '{request.parameter_name}' from node '{node_name}'."
            )

        # No tricky stuff, users!
        # if user_defined doesn't exist, or is false, then it's not user-defined
        if not getattr(element, "user_defined", False):
            details = f"Attempted to remove Element '{request.parameter_name}' from Node '{node_name}'. Failed because the Element was not user-defined (i.e., critical to the Node implementation). Only user-defined Elements can be removed from a Node."

            result = RemoveParameterFromNodeResultFailure(result_details=details)
            return result

        # Get all the connections to/from this Parameter.
        if isinstance(element, Parameter):
            list_node_connections_request = ListConnectionsForNodeRequest(node_name=node_name)
            list_connections_result = GriptapeNodes.handle_request(request=list_node_connections_request)
            if not isinstance(list_connections_result, ListConnectionsForNodeResultSuccess):
                details = f"Attempted to remove Parameter '{request.parameter_name}' from Node '{node_name}'. Failed because we were unable to get a list of Connections for the Parameter's Node."

                result = RemoveParameterFromNodeResultFailure(result_details=details)
                return result

            # We have a list of all connections to the NODE. Sift down to just those that are about this PARAMETER.

            # Destroy all the incoming Connections to this PARAMETER
            for incoming_connection in list_connections_result.incoming_connections:
                if incoming_connection.target_parameter_name == request.parameter_name:
                    delete_request = DeleteConnectionRequest(
                        source_node_name=incoming_connection.source_node_name,
                        source_parameter_name=incoming_connection.source_parameter_name,
                        target_node_name=node_name,
                        target_parameter_name=incoming_connection.target_parameter_name,
                    )
                    delete_result = GriptapeNodes.handle_request(delete_request)
                    if isinstance(delete_result, DeleteConnectionResultFailure):
                        details = f"Attempted to remove Parameter '{request.parameter_name}' from Node '{node_name}'. Failed because we were unable to delete a Connection for that Parameter."

                        result = RemoveParameterFromNodeResultFailure(result_details=details)

            # Destroy all the outgoing Connections from this PARAMETER
            for outgoing_connection in list_connections_result.outgoing_connections:
                if outgoing_connection.source_parameter_name == request.parameter_name:
                    delete_request = DeleteConnectionRequest(
                        source_node_name=node_name,
                        source_parameter_name=outgoing_connection.source_parameter_name,
                        target_node_name=outgoing_connection.target_node_name,
                        target_parameter_name=outgoing_connection.target_parameter_name,
                    )
                    delete_result = GriptapeNodes.handle_request(delete_request)
                    if isinstance(delete_result, DeleteConnectionResultFailure):
                        details = f"Attempted to remove Parameter '{request.parameter_name}' from Node '{node_name}'. Failed because we were unable to delete a Connection for that Parameter."

                        result = RemoveParameterFromNodeResultFailure(result_details=details)

        # Delete the Element itself.
        if element is not None:
            node.remove_parameter_element(element)
        else:
            details = f"Attempted to remove Element '{request.parameter_name}' from Node '{node_name}'. Failed because element didn't exist."

            result = RemoveParameterFromNodeResultFailure(result_details=details)

        details = f"Successfully removed Element '{request.parameter_name}' from Node '{node_name}'."
        result = RemoveParameterFromNodeResultSuccess(result_details=details)
        return result

    def on_get_parameter_details_request(self, request: GetParameterDetailsRequest) -> ResultPayload:
        node_name = request.node_name
        node = None

        if node_name is None:
            if not GriptapeNodes.ContextManager().has_current_node():
                details = f"Attempted to get details for Parameter '{request.parameter_name}' from a Node, but no Current Context was found."

                result = GetParameterDetailsResultFailure(result_details=details)
                return result
            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name

        # Does this node exist?
        if node is None:
            obj_mgr = GriptapeNodes.ObjectManager()
            node = obj_mgr.attempt_get_object_by_name_as_type(node_name, BaseNode)
            if node is None:
                details = f"Attempted to get details for Parameter '{request.parameter_name}' from a Node '{node_name}', but no such Node was found."

                result = GetParameterDetailsResultFailure(result_details=details)
                return result

        # Does the Element actually exist on the Node?
        element = node.get_element_by_name_and_type(request.parameter_name)

        if element is None:
            details = f"Attempted to get details for Element '{request.parameter_name}' from Node '{node_name}'. Failed because it didn't have an Element with that name on it."
            return GetParameterDetailsResultFailure(result_details=details)

        # Let's bundle up the details.
        allows_input = False
        allows_property = False
        allows_output = False

        if isinstance(element, Parameter):
            modes_allowed = element.allowed_modes
            allows_input = ParameterMode.INPUT in modes_allowed
            allows_property = ParameterMode.PROPERTY in modes_allowed
            allows_output = ParameterMode.OUTPUT in modes_allowed

        details = f"Successfully got details for Element '{request.parameter_name}' from Node '{node_name}'."
        result = GetParameterDetailsResultSuccess(
            element_id=element.element_id,
            type=getattr(element, "type", ""),
            input_types=getattr(element, "input_types", []),
            output_type=getattr(element, "output_type", ""),
            default_value=getattr(element, "default_value", None),
            tooltip=getattr(element, "tooltip", ""),
            tooltip_as_input=getattr(element, "tooltip_as_input", None),
            tooltip_as_property=getattr(element, "tooltip_as_property", None),
            tooltip_as_output=getattr(element, "tooltip_as_output", None),
            mode_allowed_input=allows_input,
            mode_allowed_property=allows_property,
            mode_allowed_output=allows_output,
            is_user_defined=getattr(element, "user_defined", False),
            settable=getattr(element, "settable", None),
            ui_options=getattr(element, "ui_options", None),
            result_details=details,
        )
        return result

    def on_get_node_element_details_request(self, request: GetNodeElementDetailsRequest) -> ResultPayload:
        node_name = request.node_name
        node = None

        if node_name is None:
            if not GriptapeNodes.ContextManager().has_current_node():
                details = f"Attempted to get element details for element '{request.specific_element_id}` from a Node, but no Current Context was found."

                return GetNodeElementDetailsResultFailure(result_details=details)
            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name

        # Does this node exist?
        if node is None:
            obj_mgr = GriptapeNodes.ObjectManager()
            node = obj_mgr.attempt_get_object_by_name_as_type(node_name, BaseNode)
            if node is None:
                details = f"Attempted to get element details for Node '{node_name}', but no such Node was found."

                return GetNodeElementDetailsResultFailure(result_details=details)

        # Did they ask for a specific element ID?
        if request.specific_element_id is None:
            # No? Use the node's root element to search from.
            element = node.root_ui_element
        else:
            element = node.root_ui_element.find_element_by_id(request.specific_element_id)
            if element is None:
                details = f"Attempted to get element details for element '{request.specific_element_id}' from Node '{node_name}'. Failed because it didn't have an element with that ID on it."

                return GetNodeElementDetailsResultFailure(result_details=details)

        element_details = element.to_dict()
        # We need to get element values from here
        param_to_value = {}
        self._set_param_to_value(node, element, param_to_value)
        if param_to_value:
            element_details["element_id_to_value"] = param_to_value
        details = f"Successfully got element details for Node '{node_name}'."
        result = GetNodeElementDetailsResultSuccess(element_details=element_details, result_details=details)
        return result

    def _set_param_to_value(self, node: BaseNode, element: BaseNodeElement, param_to_value: dict) -> None:
        """This method builds our element_id_to_value mapping to eventually return in the Element Details Request."""
        # Get all parameters
        for parameter in element.find_elements_by_type(Parameter):
            # Check if they have an output value, that takes priority
            if parameter.name in node.parameter_output_values:
                value = node.parameter_output_values[parameter.name]
            else:
                # Otherwise grab the set value or default value
                value = node.get_parameter_value(parameter.name)
            if value is not None:
                element_id = parameter.element_id
                # Check if the value is in builtins. If it isn't we need to handle it specially.
                if value.__class__.__module__ != "builtins":
                    # Check if it has a to_dict method. Use that, if it's been implemented.
                    if hasattr(value, "to_dict"):
                        # If the object has a __dict__, use that
                        param_to_value[element_id] = value.to_dict()
                        continue
                    # Otherwise use __dict__.
                    if hasattr(value, "__dict__"):
                        param_to_value[element_id] = value.__dict__
                        continue
                # Otherwise, just set it here. It'll be handled in .json() when we send it over.
                param_to_value[element_id] = value

    def modify_alterable_fields(self, request: AlterParameterDetailsRequest, parameter: BaseNodeElement) -> None:
        if isinstance(parameter, Parameter):
            if request.tooltip:
                parameter.tooltip = request.tooltip
            if request.tooltip_as_input is not None:
                parameter.tooltip_as_input = request.tooltip_as_input
            if request.tooltip_as_property is not None:
                parameter.tooltip_as_property = request.tooltip_as_property
            if request.tooltip_as_output is not None:
                parameter.tooltip_as_output = request.tooltip_as_output
        if request.ui_options is not None and hasattr(parameter, "ui_options"):
            parameter.ui_options = request.ui_options  # type: ignore[attr-defined]

    def modify_key_parameter_fields(self, request: AlterParameterDetailsRequest, parameter: Parameter) -> None:  # noqa: C901, PLR0912
        if request.type is not None:
            parameter.type = request.type
        if request.input_types is not None:
            parameter.input_types = request.input_types
        if request.output_type is not None:
            parameter.output_type = request.output_type
        if request.mode_allowed_input is not None:
            # TODO: https://github.com/griptape-ai/griptape-nodes/issues/828
            if request.mode_allowed_input is True:
                parameter.allowed_modes.add(ParameterMode.INPUT)
            else:
                parameter.allowed_modes.discard(ParameterMode.INPUT)
        if request.mode_allowed_property is not None:
            # TODO: https://github.com/griptape-ai/griptape-nodes/issues/828
            if request.mode_allowed_property is True:
                parameter.allowed_modes.add(ParameterMode.PROPERTY)
            else:
                parameter.allowed_modes.discard(ParameterMode.PROPERTY)
        if request.mode_allowed_output is not None:
            # TODO: https://github.com/griptape-ai/griptape-nodes/issues/828
            if request.mode_allowed_output is True:
                parameter.allowed_modes.add(ParameterMode.OUTPUT)
            else:
                parameter.allowed_modes.discard(ParameterMode.OUTPUT)
        if request.settable is not None:
            parameter.settable = request.settable

    def _validate_and_break_invalid_connections(
        self, node_name: str, parameter: Parameter, request: AlterParameterDetailsRequest
    ) -> ResultPayload | None:
        """Validate and break any connections that are no longer valid after a parameter type change.

        This method checks both incoming and outgoing connections for a parameter and removes
        any that are no longer type-compatible after the parameter's type has been changed.

        Returns:
            ResultPayload | None: Returns AlterParameterDetailsResultFailure if any connection deletion fails,
                                 None otherwise.
        """
        # Get all connections for this node
        list_connections_request = ListConnectionsForNodeRequest(node_name=node_name)
        list_connections_result = self.on_list_connections_for_node_request(list_connections_request)

        if not isinstance(list_connections_result, ListConnectionsForNodeResultSuccess):
            # No connections exist for this node, which is not a failure - just nothing to validate
            return None

        # Check and break invalid incoming connections
        for conn in list_connections_result.incoming_connections:
            if conn.target_parameter_name == request.parameter_name:
                source_node = self.get_node_by_name(conn.source_node_name)
                source_param = source_node.get_parameter_by_name(conn.source_parameter_name)
                if source_param and not parameter.is_incoming_type_allowed(source_param.output_type):
                    delete_result = GriptapeNodes.FlowManager().on_delete_connection_request(
                        DeleteConnectionRequest(
                            source_node_name=conn.source_node_name,
                            source_parameter_name=conn.source_parameter_name,
                            target_node_name=node_name,
                            target_parameter_name=request.parameter_name,
                        )
                    )
                    if isinstance(delete_result, ResultPayloadFailure):
                        details = f"Failed to delete incompatible incoming connection from {conn.source_node_name}.{conn.source_parameter_name} to {node_name}.{request.parameter_name}: {delete_result}"
                        return AlterParameterDetailsResultFailure(result_details=details)

        # Check and break invalid outgoing connections
        for conn in list_connections_result.outgoing_connections:
            if conn.source_parameter_name == request.parameter_name:
                target_node = self.get_node_by_name(conn.target_node_name)
                target_param = target_node.get_parameter_by_name(conn.target_parameter_name)
                if target_param and not target_param.is_incoming_type_allowed(parameter.output_type):
                    delete_result = GriptapeNodes.FlowManager().on_delete_connection_request(
                        DeleteConnectionRequest(
                            source_node_name=node_name,
                            source_parameter_name=request.parameter_name,
                            target_node_name=conn.target_node_name,
                            target_parameter_name=conn.target_parameter_name,
                        )
                    )
                    if isinstance(delete_result, ResultPayloadFailure):
                        details = f"Failed to delete incompatible outgoing connection from {node_name}.{request.parameter_name} to {conn.target_node_name}.{conn.target_parameter_name}: {delete_result}"
                        return AlterParameterDetailsResultFailure(result_details=details)

        return None

    def on_alter_parameter_details_request(self, request: AlterParameterDetailsRequest) -> ResultPayload:  # noqa: C901, PLR0911, PLR0912
        node_name = request.node_name
        node = None

        if node_name is None:
            if not GriptapeNodes.ContextManager().has_current_node():
                details = f"Attempted to alter details for Parameter '{request.parameter_name}' from node in the Current Context. Failed because there was no such Node."

                return AlterParameterDetailsResultFailure(result_details=details)
            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name

        # Does this node exist?
        if node is None:
            obj_mgr = GriptapeNodes.ObjectManager()
            node = obj_mgr.attempt_get_object_by_name_as_type(node_name, BaseNode)
            if node is None:
                details = f"Attempted to alter details for Parameter '{request.parameter_name}' from Node '{node_name}', but no such Node was found."

                return AlterParameterDetailsResultFailure(result_details=details)

        # Is the node locked?
        if node.lock:
            details = f"Attempted to alter details for Parameter '{request.parameter_name}' from Node '{node_name}'. Failed because the Node was locked."
            return AlterParameterDetailsResultFailure(result_details=details)

        # Handle ErrorProxyNode parameter alteration requests
        if isinstance(node, ErrorProxyNode):
            if request.initial_setup:
                # Record the alteration request for serialization replay
                node.record_initialization_request(request)

                # Early return with warning - we're just preserving the original changes
                details = f"Parameter '{request.parameter_name}' alteration recorded for ErrorProxyNode '{node_name}'. Original node '{node.original_node_type}' had loading errors - preserving changes for correct recreation when dependency '{node.original_library_name}' is resolved."

                result_details = ResultDetails(message=details, level=logging.WARNING)
                return AlterParameterDetailsResultSuccess(result_details=result_details)

            # Reject runtime parameter alterations on ErrorProxy
            details = f"Cannot modify parameter '{request.parameter_name}' on placeholder node '{node_name}'. This placeholder preserves your workflow structure but doesn't allow parameter modifications, as they could cause issues when the original node is restored."
            return AlterParameterDetailsResultFailure(result_details=details)

        # Does the Element actually exist on the Node?
        element = node.get_element_by_name_and_type(request.parameter_name)
        if element is None:
            details = f"Attempted to alter details for Element '{request.parameter_name}' from Node '{node_name}'. Failed because it didn't have an Element with that name on it."
            return AlterParameterDetailsResultFailure(result_details=details)
        if request.ui_options is not None:
            element.ui_options = request.ui_options  # type: ignore[attr-defined]

        # Check and handle connections if type was changed
        if isinstance(element, Parameter) and (
            request.type is not None or request.input_types is not None or request.output_type is not None
        ):
            result = self._validate_and_break_invalid_connections(node_name, element, request)
            if isinstance(result, AlterParameterDetailsResultFailure):
                return result

        # TODO: https://github.com/griptape-ai/griptape-nodes/issues/827
        # Now change all the values on the Element.
        self.modify_alterable_fields(request, element)

        # The rest of these are not alterable
        if isinstance(element, Parameter):
            if hasattr(element, "user_defined") and element.user_defined is False and request.request_id:  # type: ignore[attr-defined]
                # TODO: https://github.com/griptape-ai/griptape-nodes/issues/826
                details = f"Attempted to alter details for Element '{request.parameter_name}' from Node '{node_name}'. Could only alter some values because the Element was not user-defined (i.e., critical to the Node implementation). Only user-defined Elements can be totally modified from a Node."
                return AlterParameterDetailsResultSuccess(
                    result_details=ResultDetails(message=details, level=logging.WARNING)
                )
            self.modify_key_parameter_fields(request, element)

        # This field requires the node as well
        if request.default_value is not None:
            # TODO: https://github.com/griptape-ai/griptape-nodes/issues/825
            node.parameter_values[request.parameter_name] = request.default_value

        details = f"Successfully altered details for Element '{request.parameter_name}' from Node '{node_name}'."
        result = AlterParameterDetailsResultSuccess(result_details=details)
        return result

    # For C901 (too complex): Need to give customers explicit reasons for failure on each case.
    def on_get_parameter_value_request(self, request: GetParameterValueRequest) -> ResultPayload:
        node_name = request.node_name
        node = None

        if node_name is None:
            if not GriptapeNodes.ContextManager().has_current_node():
                details = f"Attempted to get value for Parameter '{request.parameter_name}' from node in the Current Context. Failed because there was no such Node."

                return GetParameterValueResultFailure(result_details=details)
            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name

        # Parse the parameter name to check for list indexing
        param_name = request.parameter_name

        # Does this node exist?
        if node is None:
            obj_mgr = GriptapeNodes.ObjectManager()
            node = obj_mgr.attempt_get_object_by_name_as_type(node_name, BaseNode)
            if node is None:
                details = f'"{node_name}" not found'
                return GetParameterValueResultFailure(result_details=details)

        # Does the Parameter actually exist on the Node?
        parameter = node.get_parameter_by_name(param_name)
        if parameter is None:
            details = f'"{node_name}.{param_name}" not found'
            return GetParameterValueResultFailure(result_details=details)

        # Values are actually stored on the NODE, so let's ask them.
        if param_name not in node.parameter_values:
            # Check if it might be in output values (for output parameters)
            if param_name in node.parameter_output_values:
                data_value = node.parameter_output_values[param_name]
            else:
                # Use the default if not found in either place
                data_value = parameter.default_value
        else:
            data_value = node.parameter_values[param_name]

        # Cool.
        details = f"{node_name}.{request.parameter_name} = {data_value}"
        result = GetParameterValueResultSuccess(
            input_types=parameter.input_types,
            type=parameter.type,
            output_type=parameter.output_type,
            value=TypeValidator.safe_serialize(data_value),
            result_details=details,
        )
        return result

    class ModifiedReturnValue(NamedTuple):
        """Wrapper for a value and a boolean indicating if it was modified."""

        value: Any
        modified: bool

    # added ignoring C901 since this method is overly long because of granular error checking, not actual complexity.
    def on_set_parameter_value_request(self, request: SetParameterValueRequest) -> ResultPayload:  # noqa: C901, PLR0911, PLR0912, PLR0915
        node_name = request.node_name
        node = None

        if node_name is None:
            if not GriptapeNodes.ContextManager().has_current_node():
                details = f"Attempted to set parameter '{request.parameter_name}' value. Failed because no Node was found in the Current Context."
                return SetParameterValueResultFailure(result_details=details)
            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name

        # Parse the parameter name to check for list indexing
        param_name = request.parameter_name

        # Does this node exist?
        if node is None:
            obj_mgr = GriptapeNodes.ObjectManager()
            node = obj_mgr.attempt_get_object_by_name_as_type(node_name, BaseNode)
            if node is None:
                details = f"Attempted to set parameter '{param_name}' value on node '{node_name}'. Failed because no such Node could be found."
                return SetParameterValueResultFailure(result_details=details)

        # Is the node locked?
        if node.lock:
            details = f"Attempted to set parameter '{param_name}' value on node '{node_name}'. Failed because the Node was locked."
            return SetParameterValueResultFailure(result_details=details)

        # Handle ErrorProxyNode parameter value requests
        if isinstance(node, ErrorProxyNode):
            if request.initial_setup:
                # For initial_setup, actually create the parameter and set the value
                # This allows normal serialization to handle it, rather than recording the command
                node.on_attempt_set_parameter_value(param_name)
                # Continue with normal parameter value setting logic below
                logger.debug(
                    "Created parameter '%s' on ErrorProxyNode '%s' during initial setup", param_name, node_name
                )
            else:
                # Reject runtime parameter value changes on ErrorProxy
                details = f"Cannot set parameter '{param_name}' on placeholder node '{node_name}'. This placeholder preserves your workflow structure but doesn't allow parameter changes, as they could cause issues when the original node is restored."
                return SetParameterValueResultFailure(result_details=details)
        elif isinstance(node, NodeGroupProxyNode):
            # For NodeGroupProxyNode, set the value on both the proxy AND the original node
            node.set_parameter_value(param_name, request.value)

            # Forward the value to the original node if this proxy parameter maps to one
            result = None
            if param_name in node._proxy_param_to_node_param:
                original_node, original_param_name = node._proxy_param_to_node_param[param_name]
                result = GriptapeNodes.handle_request(
                    SetParameterValueRequest(
                        parameter_name=original_param_name,
                        node_name=original_node.name,
                        value=request.value,
                        data_type=request.data_type,
                        incoming_connection_source_node_name=request.incoming_connection_source_node_name,
                        incoming_connection_source_parameter_name=request.incoming_connection_source_parameter_name,
                    )
                )
                logger.debug(
                    "Forwarded parameter value from proxy '%s.%s' to original '%s.%s'",
                    node.name,
                    param_name,
                    original_node.name,
                    original_param_name,
                )
            details = f"Attempted to set parameter value for '{node_name}.{param_name}'. Successfully set value on the NodeGroupProxyNode '{node_name}', but failed to set value on the original node'."
            return result if result else SetParameterValueResultFailure(result_details=details)

        # Does the Parameter actually exist on the Node?
        parameter = node.get_parameter_by_name(param_name)
        if parameter is None:
            details = f"Attempted to set parameter value for '{node_name}.{param_name}'. Failed because no parameter with that name could be found."

            result = SetParameterValueResultFailure(result_details=details)
            return result

        # Validate incoming connection source fields consistency
        incoming_node_set = request.incoming_connection_source_node_name is not None
        incoming_param_set = request.incoming_connection_source_parameter_name is not None
        if incoming_node_set != incoming_param_set:
            details = f"Attempted to set parameter value for '{node_name}.{request.parameter_name}'. Failed because incoming connection source fields must both be None or both be set. Got incoming_connection_source_node_name={request.incoming_connection_source_node_name}, incoming_connection_source_parameter_name={request.incoming_connection_source_parameter_name}."
            result = SetParameterValueResultFailure(result_details=details)
            return result

        # Prevent manual property setting on parameters that have both INPUT and PROPERTY modes when they have incoming connections
        # When a parameter can accept both input connections AND manual property values, having an active connection should
        # make the parameter non-settable as a property to avoid conflicts between connected values and manual values
        # Skip this check if: initial_setup (workflow loading), or incoming_connection_source fields are set (system passing upstream values)
        if (
            not request.initial_setup
            and not incoming_node_set  # If incoming connection source fields are set, this is a legitimate upstream value pass
            and ParameterMode.INPUT in parameter.allowed_modes
            and ParameterMode.PROPERTY in parameter.allowed_modes
        ):
            # Check if this parameter has any incoming connections
            connections = GriptapeNodes.FlowManager().get_connections()
            target_connections = connections.incoming_index.get(node_name)
            if target_connections is not None:
                param_connections = target_connections.get(request.parameter_name)
                if param_connections:  # Has incoming connections
                    # TODO: https://github.com/griptape-ai/griptape-nodes/issues/1965 Consider emitting UI events when parameters become settable/unsettable due to connection changes
                    details = f"Attempted to set parameter value for '{node_name}.{request.parameter_name}'. Failed because this parameter has incoming connections and cannot be set as a property while connected."
                    result = SetParameterValueResultFailure(result_details=details)
                    return result

        # Call before_value_set hook (allows nodes to modify values and temporarily control settable state)
        try:
            modified_value = node.before_value_set(parameter, request.value)
            if modified_value is not None:
                request.value = modified_value
        except Exception as err:
            details = f"Attempted to set parameter value for '{node_name}.{request.parameter_name}'. Failed because before_value_set hook raised exception: {err}"
            result = SetParameterValueResultFailure(result_details=details)
            return result

        # Validate that parameters can be set at all (note: we want the value to be set during initial setup, but not after)
        # We skip this if it's a passthru from a connection or if we're on initial setup; those always trump settable.
        # This check comes *AFTER* before_value_set() to allow nodes to temporarily modify settable state
        if not parameter.settable and not incoming_node_set and not request.initial_setup:
            details = f"Attempted to set parameter value for '{node_name}.{request.parameter_name}'. Failed because that Parameter was flagged as not settable."
            result = SetParameterValueResultFailure(result_details=details)
            return result
        object_type = request.data_type if request.data_type else parameter.type
        # If the parameter is control type, we shouldn't check the value being set, since it's just a marker for which path to take, not a real value, and will likely be a string, which doesn't match ControlType.
        if parameter.type != ParameterTypeBuiltin.CONTROL_TYPE.value and not parameter.is_incoming_type_allowed(
            object_type
        ):
            details = f"Attempted to set parameter value for '{node_name}.{request.parameter_name}'. Failed because the value's type of '{object_type}' was not in the Parameter's list of allowed types: {parameter.input_types}."

            result = SetParameterValueResultFailure(result_details=details)
            return result

        try:
            parent_flow_name = self.get_node_parent_flow_by_name(node.name)
        except KeyError:
            details = f"Attempted to set parameter value for '{node_name}.{request.parameter_name}'. Failed because the node's parent flow does not exist. Could not unresolve future nodes."
            return SetParameterValueResultFailure(result_details=details)

        obj_mgr = GriptapeNodes.ObjectManager()
        parent_flow = obj_mgr.attempt_get_object_by_name_as_type(parent_flow_name, ControlFlow)
        if not parent_flow:
            details = f"Attempted to set parameter value for '{node_name}.{request.parameter_name}'. Failed because the node's parent flow does not exist. Could not unresolve future nodes."
            return SetParameterValueResultFailure(result_details=details)
        try:
            finalized_value, modified = self._set_and_pass_through_values(request, node)
        except Exception as err:
            details = f"Attempted to set parameter value for '{node_name}.{request.parameter_name}'. Failed because Exception: {err}"
            return SetParameterValueResultFailure(result_details=details)
        if not request.initial_setup and modified:
            try:
                GriptapeNodes.FlowManager().get_connections().unresolve_future_nodes(node)
            except Exception as err:
                details = f"Attempted to set parameter value for '{node_name}.{request.parameter_name}'. Failed because Exception: {err}"
                return SetParameterValueResultFailure(result_details=details)
        if request.initial_setup is False and not request.is_output and modified:
            # Mark node as unresolved, broadcast an event
            node.make_node_unresolved(current_states_to_trigger_change_event=set({NodeResolutionState.RESOLVED}))
            # Get the flow
            # Pass the value through to connected downstream parameters!
            # Set incoming_connection_source fields to identify this as legitimate upstream value propagation
            # (not manual property setting) so it bypasses the INPUT+PROPERTY connection blocking logic
            conn_output_nodes = parent_flow.get_connected_output_parameters(node, parameter)
            for target_node, target_parameter in conn_output_nodes:
                # Skip propagation for:
                # 1. Control Parameters as they should not receive values
                # 2. Locked nodes
                is_control_parameter = (
                    ParameterType.attempt_get_builtin(parameter.output_type) == ParameterTypeBuiltin.CONTROL_TYPE
                )
                is_dest_node_locked = target_node.lock
                if (not is_control_parameter) and (not is_dest_node_locked):
                    GriptapeNodes.handle_request(
                        SetParameterValueRequest(
                            parameter_name=target_parameter.name,
                            node_name=target_node.name,
                            value=finalized_value,
                            data_type=object_type,  # Do type instead of output type, because it hasn't been processed.
                            incoming_connection_source_node_name=node.name,
                            incoming_connection_source_parameter_name=parameter.name,
                        )
                    )

        # Cool.
        details = f"Successfully set value on Node '{node_name}' Parameter '{request.parameter_name}'."
        result = SetParameterValueResultSuccess(
            finalized_value=finalized_value, data_type=parameter.type, result_details=details
        )
        return result

    def _set_and_pass_through_values(self, request: SetParameterValueRequest, node: BaseNode) -> ModifiedReturnValue:
        """Set the parameter value on the node according to the specifications."""
        modified = False
        object_created = request.value
        # If the value should be set on the output dictionary:
        if request.is_output:
            # set it to output values
            if (
                request.parameter_name in node.parameter_output_values
                and node.parameter_output_values[request.parameter_name] != object_created
            ):
                modified = True
            node.parameter_output_values[request.parameter_name] = object_created
            return NodeManager.ModifiedReturnValue(object_created, modified)
        # Otherwise use set_parameter_value. This calls our converters and validators.
        # Skip before_value_set since we already called it earlier in the flow
        old_value = node.get_parameter_value(request.parameter_name)
        node.set_parameter_value(
            request.parameter_name, object_created, initial_setup=request.initial_setup, skip_before_value_set=True
        )
        # Get the "converted" value here.
        finalized_value = node.get_parameter_value(request.parameter_name)
        if old_value != finalized_value:
            modified = True
        # If any parameters were dependent on that value, we're calling this details request to emit the result to the editor.
        return NodeManager.ModifiedReturnValue(finalized_value, modified)

    # For C901 (too complex): Need to give customers explicit reasons for failure on each case.
    # For PLR0911 (too many return statements): don't want to do a ton of nested chains of success,
    # want to give clear reasoning for each failure.
    # For PLR0915 (too many statements): very little reusable code here, want to be explicit and
    # make debugger use friendly.
    def on_get_all_node_info_request(self, request: GetAllNodeInfoRequest) -> ResultPayload:  # noqa: C901, PLR0911
        node_name = request.node_name
        node = None

        # Get from the current context.
        if node_name is None:
            if not GriptapeNodes.ContextManager().has_current_node():
                details = "Attempted to get all info for a Node from the Current Context. Failed because the Current Context is empty."
                return GetAllNodeInfoResultFailure(result_details=details)

            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name

        # Does this node exist?
        if node is None:
            obj_mgr = GriptapeNodes.ObjectManager()
            node = obj_mgr.attempt_get_object_by_name_as_type(node_name, BaseNode)
            if node is None:
                details = f"Attempted to get all info for Node named '{node_name}', but no such Node was found."
                return GetAllNodeInfoResultFailure(result_details=details)

        get_metadata_request = GetNodeMetadataRequest(node_name=node_name)
        get_metadata_result = self.on_get_node_metadata_request(get_metadata_request)
        if not get_metadata_result.succeeded():
            details = f"Attempted to get all info for Node named '{node_name}', but failed getting the metadata."
            return GetAllNodeInfoResultFailure(result_details=details)

        get_resolution_state_request = GetNodeResolutionStateRequest(node_name=node_name)
        get_resolution_state_result = self.on_get_node_resolution_state_request(get_resolution_state_request)
        if not get_resolution_state_result.succeeded():
            details = (
                f"Attempted to get all info for Node named '{node_name}', but failed getting the resolution state."
            )
            return GetAllNodeInfoResultFailure(result_details=details)

        list_connections_request = ListConnectionsForNodeRequest(node_name=node_name)
        list_connections_result = self.on_list_connections_for_node_request(list_connections_request)
        if not list_connections_result.succeeded():
            details = (
                f"Attempted to get all info for Node named '{node_name}', but failed listing all connections for it."
            )

            return GetAllNodeInfoResultFailure(result_details=details)
        # Cast everything to get the linter off our back.
        try:
            get_metadata_success = cast("GetNodeMetadataResultSuccess", get_metadata_result)
            get_resolution_state_success = cast("GetNodeResolutionStateResultSuccess", get_resolution_state_result)
            list_connections_success = cast("ListConnectionsForNodeResultSuccess", list_connections_result)
        except Exception as err:
            details = f"Attempted to get all info for Node named '{node_name}'. Failed due to error: {err}."

            return GetAllNodeInfoResultFailure(result_details=details)
        get_node_elements_request = GetNodeElementDetailsRequest(node_name=node_name)
        get_node_elements_result = self.on_get_node_element_details_request(get_node_elements_request)
        if not get_node_elements_result.succeeded():
            details = (
                f"Attempted to get all info for Node named '{node_name}', but failed getting details for elements."
            )
            return GetAllNodeInfoResultFailure(result_details=details)
        try:
            get_element_details_success = cast("GetNodeElementDetailsResultSuccess", get_node_elements_result)
        except Exception as err:
            details = f"Attempted to get all info for Node named '{node_name}'. Failed due to error: {err}."
            return GetAllNodeInfoResultFailure(result_details=details)

        # this will return the node element and the value
        element_details = get_element_details_success.element_details
        if "element_id_to_value" in element_details:
            element_id_to_value = element_details["element_id_to_value"].copy()
            del element_details["element_id_to_value"]
        else:
            element_id_to_value = {}
        details = f"Successfully got all node info for node '{node_name}'."
        result = GetAllNodeInfoResultSuccess(
            metadata=get_metadata_success.metadata,
            node_resolution_state=get_resolution_state_success.state,
            locked=node.lock,
            connections=list_connections_success,
            element_id_to_value=element_id_to_value,
            root_node_element=element_details,
            result_details=details,
        )
        return result

    def on_get_compatible_parameters_request(self, request: GetCompatibleParametersRequest) -> ResultPayload:  # noqa: C901, PLR0911, PLR0912, PLR0915
        node_name = request.node_name
        node = None

        if node_name is None:
            if not GriptapeNodes.ContextManager().has_current_node():
                details = "Attempted to get compatible parameters for node, but no current node was found."
                return GetCompatibleParametersResultFailure(result_details=details)
            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name

        # Vet the node
        if node is None:
            obj_mgr = GriptapeNodes.ObjectManager()
            node = obj_mgr.attempt_get_object_by_name_as_type(node_name, BaseNode)
            if node is None:
                details = (
                    f"Attempted to get compatible parameters for node '{node_name}', but that node does not exist."
                )
                return GetCompatibleParametersResultFailure(result_details=details)

        # Vet the parameter.
        request_param = node.get_parameter_by_name(request.parameter_name)
        if request_param is None:
            details = f"Attempted to get compatible parameters for '{node_name}.{request.parameter_name}', but that no Parameter with that name could not be found."
            return GetCompatibleParametersResultFailure(result_details=details)

        # Figure out the mode we're going for, and if this parameter supports the mode.
        request_mode = ParameterMode.OUTPUT if request.is_output else ParameterMode.INPUT
        # Does this parameter support that?
        if request_mode not in request_param.allowed_modes:
            details = f"Attempted to get compatible parameters for '{node_name}.{request.parameter_name}' as '{request_mode}', but the Parameter didn't support that type of input/output."
            return GetCompatibleParametersResultFailure(result_details=details)

        # Get the parent flows.
        try:
            flow_name = self.get_node_parent_flow_by_name(node_name)
        except KeyError as err:
            details = f"Attempted to get compatible parameters for '{node_name}.{request.parameter_name}', but the node's parent flow could not be found: {err}"
            return GetCompatibleParametersResultFailure(result_details=details)

        # Iterate through all nodes in this Flow (yes, this restriction still sucks)
        list_nodes_in_flow_request = ListNodesInFlowRequest(flow_name=flow_name)
        list_nodes_in_flow_result = GriptapeNodes.FlowManager().on_list_nodes_in_flow_request(
            list_nodes_in_flow_request
        )
        if not list_nodes_in_flow_result.succeeded():
            details = f"Attempted to get compatible parameters for '{node_name}.{request.parameter_name}'. Failed due to inability to list nodes in parent flow '{flow_name}'."
            return GetCompatibleParametersResultFailure(result_details=details)

        try:
            list_nodes_in_flow_success = cast("ListNodesInFlowResultSuccess", list_nodes_in_flow_result)
        except Exception as err:
            details = f"Attempted to get compatible parameters for '{node_name}.{request.parameter_name}'. Failed due to {err}"
            return GetCompatibleParametersResultFailure(result_details=details)

        # Walk through all nodes that are NOT us to find compatible Parameters.
        valid_parameters_by_node = {}
        for test_node_name in list_nodes_in_flow_success.node_names:
            if test_node_name != request.node_name:
                # Get node by name
                try:
                    test_node = self.get_node_by_name(test_node_name)
                except ValueError as err:
                    details = f"Attempted to get compatible parameters for node '{node_name}', and sought to test against {test_node_name}, but that node does not exist. Error: {err}."
                    return GetCompatibleParametersResultFailure(result_details=details)

                # Get Parameters from Node
                for test_param in test_node.parameters:
                    # Are we compatible from an input/output perspective?
                    fits_mode = False
                    if request_mode == ParameterMode.INPUT:
                        fits_mode = ParameterMode.OUTPUT in test_param.allowed_modes
                    else:
                        fits_mode = ParameterMode.INPUT in test_param.allowed_modes

                    if fits_mode:
                        # Compare types for compatibility
                        types_compatible = False
                        if request_mode == ParameterMode.INPUT:
                            # See if THEIR inputs would accept MY output
                            types_compatible = test_param.is_incoming_type_allowed(request_param.output_type)
                        else:
                            # See if MY inputs would accept THEIR output
                            types_compatible = request_param.is_incoming_type_allowed(test_param.output_type)

                        if types_compatible:
                            param_and_mode = ParameterAndMode(
                                parameter_name=test_param.name, is_output=not request.is_output
                            )
                            # Add the test param to our dictionary.
                            if test_node_name in valid_parameters_by_node:
                                # Append this parameter to the list
                                compatible_list = valid_parameters_by_node[test_node_name]
                                compatible_list.append(param_and_mode)
                            else:
                                # Create new
                                compatible_list = [param_and_mode]
                                valid_parameters_by_node[test_node_name] = compatible_list

        details = f"Successfully got compatible parameters for '{node_name}.{request.parameter_name}'."
        return GetCompatibleParametersResultSuccess(
            valid_parameters_by_node=valid_parameters_by_node, result_details=details
        )

    def get_node_by_name(self, name: str) -> BaseNode:
        obj_mgr = GriptapeNodes.ObjectManager()

        node = obj_mgr.attempt_get_object_by_name_as_type(name, BaseNode)
        if node is None:
            msg = f"Node '{name}' not found."
            raise ValueError(msg)

        return node

    def get_node_parent_flow_by_name(self, node_name: str) -> str:
        if node_name not in self._name_to_parent_flow_name:
            msg = f"Node '{node_name}' could not be found."
            raise KeyError(msg)
        return self._name_to_parent_flow_name[node_name]

    async def on_resolve_from_node_request(self, request: ResolveNodeRequest) -> ResultPayload:  # noqa: C901, PLR0911, PLR0912
        node_name = request.node_name
        debug_mode = request.debug_mode

        if node_name is None:
            details = "No Node name was provided. Failed to resolve node."

            return ResolveNodeResultFailure(validation_exceptions=[], result_details=details)
        try:
            node = self.get_node_by_name(node_name)
        except ValueError as e:
            details = f'Resolve failure. "{node_name}" does not exist. {e}'

            return ResolveNodeResultFailure(validation_exceptions=[e], result_details=details)
        # try to get the flow parent of this node
        try:
            flow_name = self._name_to_parent_flow_name[node_name]
        except KeyError as e:
            details = f'Failed to fetch parent flow for "{node_name}": {e}'

            return ResolveNodeResultFailure(validation_exceptions=[e], result_details=details)
        try:
            obj_mgr = GriptapeNodes.ObjectManager()
            flow = obj_mgr.attempt_get_object_by_name_as_type(flow_name, ControlFlow)
        except KeyError as e:
            details = f'Failed to fetch parent flow for "{node_name}": {e}'

            return ResolveNodeResultFailure(validation_exceptions=[e], result_details=details)

        if flow is None:
            details = f'Failed to fetch parent flow for "{node_name}"'
            return ResolveNodeResultFailure(validation_exceptions=[], result_details=details)

        # Check for existing running flow
        flow_mgr = GriptapeNodes.FlowManager()
        if flow_mgr.check_for_existing_running_flow():
            # Behavior should stay the same for sequential flows.
            if flow_mgr._global_control_flow_machine and isinstance(
                flow_mgr._global_control_flow_machine.resolution_machine, SequentialResolutionMachine
            ):
                errormsg = f"This workflow is already in progress. Please wait for the current process to finish before starting {node.name} again."
                return ResolveNodeResultFailure(validation_exceptions=[RuntimeError(errormsg)], result_details=errormsg)
            # Behavior should also match if the flow running is a Control Flow, and not a singular node resolution.
            if not flow_mgr._global_single_node_resolution:
                errormsg = f"This workflow is already in progress. Please wait for the current control process to finish before starting {node.name} again."
                return ResolveNodeResultFailure(validation_exceptions=[RuntimeError(errormsg)], result_details=errormsg)

        # Check if the node is already in the DAG - if so, skip this resolution. It's already queued or has been resolved.
        if node.name in flow_mgr._global_dag_builder.node_to_reference:
            logger.error("Node %s is already executing. Cannot start execution.", node.name)
            return ResolveNodeResultFailure(
                validation_exceptions=[],
                result_details=f"Node {node.name} is already executing. Cannot start execution.",
            )
        try:
            GriptapeNodes.FlowManager().get_connections().unresolve_future_nodes(node)
        except Exception as e:
            details = f'Failed to mark future nodes dirty. Unable to kick off flow from "{node_name}": {e}'
            return ResolveNodeResultFailure(validation_exceptions=[e], result_details=details)
        # Validate here.
        result = self.on_validate_node_dependencies_request(ValidateNodeDependenciesRequest(node_name=node_name))
        try:
            if not result.succeeded():
                details = f"Failed to resolve node '{node_name}'. Flow Validation Failed"
                return StartFlowResultFailure(validation_exceptions=[], result_details=details)
            result = cast("ValidateNodeDependenciesResultSuccess", result)

            if not result.validation_succeeded:
                details = f"Failed to resolve node '{node_name}'. Flow Validation Failed."
                if len(result.exceptions) > 0:
                    for exception in result.exceptions:
                        details = f"{details}\n\t{exception}"
                return StartFlowResultFailure(validation_exceptions=result.exceptions, result_details=details)
        except Exception as e:
            details = f"Failed to resolve node '{node_name}'. Flow Validation Failed. Error: {e}"
            return StartFlowResultFailure(validation_exceptions=[e], result_details=details)
        try:
            await GriptapeNodes.FlowManager().resolve_singular_node(flow, node, debug_mode=debug_mode)
        except Exception as e:
            details = f'Failed to resolve "{node_name}".  Error: {e}'
            return ResolveNodeResultFailure(validation_exceptions=[e], result_details=details)
        details = f'Starting to resolve "{node_name}" in "{flow_name}"'
        return ResolveNodeResultSuccess(result_details=details)

    def on_validate_node_dependencies_request(self, request: ValidateNodeDependenciesRequest) -> ResultPayload:
        node_name = request.node_name
        obj_manager = GriptapeNodes.ObjectManager()
        node = obj_manager.attempt_get_object_by_name_as_type(node_name, BaseNode)
        if node is None:
            details = f'Failed to validate node dependencies. Node with "{node_name}" does not exist.'
            return ValidateNodeDependenciesResultFailure(result_details=details)
        try:
            flow_name = self.get_node_parent_flow_by_name(node_name)
        except Exception as e:
            details = f'Failed to validate node dependencies. Node with "{node_name}" has no parent flow. Error: {e}'
            return ValidateNodeDependenciesResultFailure(result_details=details)
        flow = GriptapeNodes.ObjectManager().attempt_get_object_by_name_as_type(flow_name, ControlFlow)
        if not flow:
            details = f'Failed to validate node dependencies. Flow with "{flow_name}" does not exist.'
            return ValidateNodeDependenciesResultFailure(result_details=details)
        # Gets all dependent nodes
        nodes = flow.get_node_dependencies(node)
        all_exceptions = []
        for dependent_node in nodes:
            exceptions = dependent_node.validate_before_workflow_run()
            if exceptions:
                all_exceptions = all_exceptions + exceptions
        return ValidateNodeDependenciesResultSuccess(
            validation_succeeded=(len(all_exceptions) == 0),
            exceptions=all_exceptions,
            result_details=f"Successfully validated dependencies for node '{node_name}'. Found {len(all_exceptions)} validation issues.",
        )

    def on_serialize_node_to_commands(self, request: SerializeNodeToCommandsRequest) -> ResultPayload:  # noqa: C901, PLR0912, PLR0915
        node_name = request.node_name
        node = None

        if node_name is None:
            if not GriptapeNodes.ContextManager().has_current_node():
                details = "Attempted to serialize a Node to commands from the Current Context. Failed because the Current Context is empty."
                return SerializeNodeToCommandsResultFailure(result_details=details)
            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name

        # Does this node exist?
        if node is None:
            obj_mgr = GriptapeNodes.ObjectManager()
            node = obj_mgr.attempt_get_object_by_name_as_type(node_name, BaseNode)
            if node is None:
                details = f"Attempted to serialize Node '{node_name}' to commands. Failed because no Node with that name could be found."
                return SerializeNodeToCommandsResultFailure(result_details=details)

        # This is our current dude.
        with GriptapeNodes.ContextManager().node(node=node):
            # Get the library and version details.
            library_used = node.metadata["library"]
            # Get the library metadata so we can get the version.
            library_metadata_request = GetLibraryMetadataRequest(library=library_used)
            # Call LibraryManager directly to avoid error toasts when library is unavailable (expected for ErrorProxyNode)
            # Per https://github.com/griptape-ai/griptape-nodes/issues/1940
            library_metadata_result = GriptapeNodes.LibraryManager().get_library_metadata_request(
                library_metadata_request
            )

            if not isinstance(library_metadata_result, GetLibraryMetadataResultSuccess):
                if isinstance(node, ErrorProxyNode):
                    # For ErrorProxyNode, use descriptive message when original library unavailable
                    library_version = "<version unavailable; workflow was saved when library was unable to be loaded>"
                    library_details = LibraryNameAndVersion(library_name=library_used, library_version=library_version)
                    details = f"Serializing Node '{node_name}' (original type: {node.original_node_type}) with unavailable library '{library_used}'. Saving as ErrorProxy with placeholder version. Fix the missing library and reload the workflow to restore the original node."
                    logger.warning(details)
                else:
                    # For regular nodes, this is still an error
                    details = f"Attempted to serialize Node '{node_name}' to commands. Failed to get metadata for library '{library_used}'."
                    return SerializeNodeToCommandsResultFailure(result_details=details)
            else:
                library_version = library_metadata_result.metadata.library_version
                library_details = LibraryNameAndVersion(library_name=library_used, library_version=library_version)

            # Handle ErrorProxyNode serialization - serialize as original node type

            if isinstance(node, ErrorProxyNode):
                serialized_node_type = node.original_node_type
                serialized_library_name = node.original_library_name
            else:
                serialized_node_type = node.__class__.__name__
                serialized_library_name = library_details.library_name

            # Get the creation details.
            create_node_request = CreateNodeRequest(
                node_type=serialized_node_type,
                node_name=node_name,
                specific_library_name=serialized_library_name,
                metadata=copy.deepcopy(node.metadata),
                # If it is actively resolving, mark as unresolved.
                resolution=node.state.value,
                initial_setup=True,
            )

            # We're going to compare this node instance vs. a canonical one. Rez that one up.
            # For ErrorProxyNode, we can't create a reference node, so skip comparison
            if isinstance(node, ErrorProxyNode):
                reference_node = None
            else:
                reference_node = type(node)(name="REFERENCE NODE")

            # Now creation or alteration of all of the elements.
            element_modification_commands = []
            for parameter in node.parameters:
                # Create the parameter, or alter it on the existing node
                if parameter.user_defined:
                    # Always serialize user-defined parameters regardless of node type
                    param_dict = parameter.to_dict()
                    param_dict["initial_setup"] = True
                    add_param_request = AddParameterToNodeRequest.create(**param_dict)
                    element_modification_commands.append(add_param_request)
                elif isinstance(node, ErrorProxyNode):
                    # For ErrorProxyNode, replay all recorded initialization requests for this parameter
                    recorded_requests = node.get_recorded_initialization_requests()
                    matching_requests = [
                        recorded_request
                        for recorded_request in recorded_requests
                        if (
                            hasattr(recorded_request, "parameter_name")
                            and getattr(recorded_request, "parameter_name", None) == parameter.name
                        )
                    ]
                    element_modification_commands.extend(matching_requests)
                elif reference_node is None:
                    # Normal node with no reference - treat all parameters as needing serialization
                    param_dict = parameter.to_dict()
                    param_dict["initial_setup"] = True
                    add_param_request = AddParameterToNodeRequest.create(**param_dict)
                    element_modification_commands.append(add_param_request)
                else:
                    # Normal node - compare against reference node
                    diff = NodeManager._manage_alter_details(parameter, reference_node)
                    relevant = False
                    for key in diff:
                        if key in AlterParameterDetailsRequest.relevant_parameters():
                            relevant = True
                            break
                    if relevant:
                        diff["parameter_name"] = parameter.name
                        diff["initial_setup"] = True
                        alter_param_request = AlterParameterDetailsRequest.create(**diff)
                        element_modification_commands.append(alter_param_request)

            # Now assignment of values to all of the parameters.
            set_value_commands = []

            # ErrorProxyNode uses normal parameter serialization now since we create real parameters
            # Only AlterParameterDetailsRequest commands are recorded and replayed
            # Normal node - use current parameter values
            for parameter in node.parameters:
                # SetParameterValueRequest event
                set_param_value_requests = NodeManager.handle_parameter_value_saving(
                    parameter=parameter,
                    node=node,
                    unique_parameter_uuid_to_values=request.unique_parameter_uuid_to_values,
                    serialized_parameter_value_tracker=request.serialized_parameter_value_tracker,
                    create_node_request=create_node_request,
                )
                if set_param_value_requests is not None:
                    set_value_commands.extend(set_param_value_requests)
        # now check if locked
        if node.lock:
            lock_command = SetLockNodeStateRequest(node_name=None, lock=True)
        else:
            lock_command = None

        # Collect node dependencies
        node_dependencies = node.get_node_dependencies()
        if node_dependencies is None:
            # Ensure we always have a NodeDependencies object, even if empty
            node_dependencies = NodeDependencies()

        # Add the library dependency to the node dependencies
        node_dependencies.libraries.add(library_details)

        # Hooray
        serialized_node_commands = SerializedNodeCommands(
            create_node_command=create_node_request,
            element_modification_commands=element_modification_commands,
            node_dependencies=node_dependencies,
            lock_node_command=lock_command,
        )
        details = f"Successfully serialized node '{node_name}' into commands."
        result = SerializeNodeToCommandsResultSuccess(
            serialized_node_commands=serialized_node_commands,  # How to serialize this node
            set_parameter_value_commands=set_value_commands,  # The commands to serialize it with
            result_details=details,
        )
        return result

    def check_response(self, response: object, class_to_check: type, attribute_to_retrieve: Any) -> Any:
        """Helper function for remake_duplicates to check whether response is of a particular type before getting an attribute.

        Args:
            response (object): The response object to retrieve the attribute from.
            class_to_check (type): The class the response needs to be part of in order to retrieve the attribute.
            attribute_to_retrieve (Any): The attribute the function will retrieve if it matches the type.

        Returns:
            attribute (Any): The attribute retrieved by the function, none if no attributes are retrieved.
        """
        attribute = None
        if isinstance(response, class_to_check):
            attribute = getattr(response, attribute_to_retrieve)
        return attribute

    def parameter_type(self, source_parameter_name: str, source_node_name: str) -> str:
        """Helper function to get type of a parameter in remake_duplicates.

        Args:
            source_parameter_name (str): The name of the parameter to get info from.
            source_node_name (str): The name of the node the parameter is part of.

        Returns:
            The type of the parameter is returned, or None if the request fails.

        """
        connection_info_request = GetParameterDetailsRequest(source_parameter_name, source_node_name)
        connection_info_response = GriptapeNodes.handle_request(connection_info_request)
        # only get value if it succeeds
        connection_type = NodeManager.check_response(
            self, connection_info_response, GetParameterDetailsResultSuccess, "type"
        )
        return connection_type

    def remake_connections(self, old_node_names: list[str], new_node_names: list[str]) -> None:
        """Remakes the incoming data connections and outgoing control connections.

        for a list of new_node_names, using the connections from the corresponding old_node_names.

        Args:
            old_node_names (list[str]): The old node names the connections are taken from.
            new_node_names (list[str]): The new node names the duplicate connections will be added to.

        Returns:
            None

        """
        # Since it is a duplicate, it makes sense to remake all the old incoming connections the original had
        for old_node_name, new_node_name in zip(old_node_names, new_node_names, strict=True):
            # List the old incoming connections
            list_connections_for_node_request = ListConnectionsForNodeRequest(old_node_name)
            list_connections_for_node_response = GriptapeNodes.handle_request(list_connections_for_node_request)

            # Only get incoming/outgoing connections if it returns the proper type
            incoming_connections = NodeManager.check_response(
                self, list_connections_for_node_response, ListConnectionsForNodeResultSuccess, "incoming_connections"
            )
            outgoing_connections = NodeManager.check_response(
                self, list_connections_for_node_response, ListConnectionsForNodeResultSuccess, "outgoing_connections"
            )

            # Check if none to prevent an error in the for loops
            if incoming_connections is None:
                incoming_connections = []
            if outgoing_connections is None:
                outgoing_connections = []

            # If there are any incoming connections, loop over them
            for incoming_connection in incoming_connections:
                # Define some variables to reduce verbosity
                source_parameter_name = incoming_connection.source_parameter_name
                source_node_name = incoming_connection.source_node_name
                target_parameter_name = incoming_connection.target_parameter_name

                # Get info about parameter
                connection_type = NodeManager.parameter_type(self, source_parameter_name, source_node_name)

                # Skip control connections when it's incoming
                if connection_type != ParameterTypeBuiltin.CONTROL_TYPE:
                    create_old_incoming_connections_request = CreateConnectionRequest(
                        source_node_name=source_node_name,
                        source_parameter_name=source_parameter_name,
                        target_node_name=new_node_name,
                        target_parameter_name=target_parameter_name,
                    )
                    GriptapeNodes.handle_request(create_old_incoming_connections_request)

            # If there are any outgoing connections, loop over them
            for outgoing_connection in outgoing_connections:
                # Define some variables to reduce verbosity
                source_parameter_name = outgoing_connection.source_parameter_name
                target_node_name = outgoing_connection.target_node_name
                target_parameter_name = outgoing_connection.target_parameter_name

                # Get info about parameter
                connection_type = NodeManager.parameter_type(self, source_parameter_name, new_node_name)

                # Only remake control connections when its outgoing
                if connection_type == ParameterTypeBuiltin.CONTROL_TYPE:
                    create_old_outgoing_connections_request = CreateConnectionRequest(
                        source_node_name=new_node_name,
                        source_parameter_name=outgoing_connection.source_parameter_name,
                        target_node_name=target_node_name,
                        target_parameter_name=outgoing_connection.target_parameter_name,
                    )
                    GriptapeNodes.handle_request(create_old_outgoing_connections_request)

    def on_deserialize_node_from_commands(self, request: DeserializeNodeFromCommandsRequest) -> ResultPayload:
        # Issue the creation command first.
        create_node_request = request.serialized_node_commands.create_node_command
        create_node_result = GriptapeNodes().handle_request(create_node_request)
        if not isinstance(create_node_result, CreateNodeResultSuccess):
            details = f"Attempted to deserialize a serialized set of Node Creation commands. Failed to create node '{create_node_request.node_name}'."
            return DeserializeNodeFromCommandsResultFailure(result_details=details)

        # Adopt the newly-created node as our current context.
        node_name = create_node_result.node_name
        node = GriptapeNodes.ObjectManager().attempt_get_object_by_name_as_type(node_name, BaseNode)
        if node is None:
            details = f"Attempted to deserialize a serialized set of Node Creation commands. Failed to get node '{node_name}'."
            return DeserializeNodeFromCommandsResultFailure(result_details=details)
        with GriptapeNodes.ContextManager().node(node=node):
            for element_command in request.serialized_node_commands.element_modification_commands:
                if isinstance(
                    element_command, (AlterParameterDetailsRequest, AddParameterToNodeRequest)
                ):  # are there more types of requests we could encounter here?
                    element_command.node_name = node_name
                element_result = GriptapeNodes().handle_request(element_command)
                if element_result.failed():
                    details = f"Attempted to deserialize a serialized set of Node Creation commands. Failed to execute an element command for node '{node_name}'."
                    return DeserializeNodeFromCommandsResultFailure(result_details=details)
        details = f"Successfully deserialized a serialized set of Node Creation commands for node '{node_name}'."
        return DeserializeNodeFromCommandsResultSuccess(node_name=node_name, result_details=details)

    def on_serialize_selected_nodes_to_commands(
        self, request: SerializeSelectedNodesToCommandsRequest
    ) -> ResultPayload:
        """This will take the selected nodes in the Object manager and serialize them into commands."""
        # These have already been sorted by the time they were selected.
        nodes_to_serialize = request.nodes_to_serialize
        # This is node_uuid to the serialization command.
        node_commands = {}
        # Node Name to UUID
        node_name_to_uuid = {}
        connections_to_serialize = []
        # This is also node_uuid to the parameter serialization command.
        parameter_commands = {}
        # This is node_uuid to lock commands.
        lock_commands = {}
        # I need to store node names and parameter names to UUID
        unique_uuid_to_values = {}
        # And track how values map into that map.
        serialized_parameter_value_tracker = SerializedParameterValueTracker()
        selected_node_names = [values[0] for values in nodes_to_serialize]
        for node_name, _ in nodes_to_serialize:
            result = self.on_serialize_node_to_commands(
                SerializeNodeToCommandsRequest(
                    node_name=node_name,
                    unique_parameter_uuid_to_values=unique_uuid_to_values,
                    serialized_parameter_value_tracker=serialized_parameter_value_tracker,
                )
            )
            if not isinstance(result, SerializeNodeToCommandsResultSuccess):
                details = f"Attempted to serialize a selection of Nodes. Failed to serialize {node_name}."
                return SerializeNodeToCommandsResultFailure(result_details=details)
            node_commands[node_name] = result.serialized_node_commands
            node_name_to_uuid[node_name] = result.serialized_node_commands.node_uuid
            parameter_commands[result.serialized_node_commands.node_uuid] = result.set_parameter_value_commands
            lock_commands[result.serialized_node_commands.node_uuid] = result.serialized_node_commands.lock_node_command
            try:
                flow_name = self.get_node_parent_flow_by_name(node_name)
                GriptapeNodes.FlowManager().get_flow_by_name(flow_name)
            except Exception:
                details = f"Attempted to serialize a selection of Nodes. Failed to get the flow of node {node_name}. Cannot serialize connections for this node."
                logger.warning(details)
                continue
            connections = GriptapeNodes.FlowManager().get_connections()
            if node_name in connections.outgoing_index:
                node_connections = [
                    connections.connections[connection_id]
                    for category_dict in connections.outgoing_index[node_name].values()
                    for connection_id in category_dict
                ]
                for connection in node_connections:
                    if connection.target_node.name not in selected_node_names:
                        continue
                    connections_to_serialize.append(connection)
        serialized_connections = []
        for connection in connections_to_serialize:
            source_node_uuid = node_name_to_uuid[connection.source_node.name]
            target_node_uuid = node_name_to_uuid[connection.target_node.name]
            serialized_connections.append(
                SerializedSelectedNodesCommands.IndirectConnectionSerialization(
                    source_node_uuid=source_node_uuid,
                    source_parameter_name=connection.source_parameter.name,
                    target_node_uuid=target_node_uuid,
                    target_parameter_name=connection.target_parameter.name,
                )
            )
        # Final result for serialized node commands
        final_result = SerializedSelectedNodesCommands(
            serialized_node_commands=list(node_commands.values()),
            serialized_connection_commands=serialized_connections,
            set_parameter_value_commands=parameter_commands,
            set_lock_commands_per_node=lock_commands,
        )
        # Set everything in the clipboard if requested
        if request.copy_to_clipboard:
            GriptapeNodes.ContextManager()._clipboard.node_commands = final_result
            GriptapeNodes.ContextManager()._clipboard.parameter_uuid_to_values = unique_uuid_to_values
        return SerializeSelectedNodesToCommandsResultSuccess(
            final_result,
            result_details=f"Successfully serialized {len(request.nodes_to_serialize)} selected nodes to commands.",
        )

    def on_deserialize_selected_nodes_from_commands(  # noqa: C901, PLR0912
        self,
        request: DeserializeSelectedNodesFromCommandsRequest,
    ) -> ResultPayload:
        commands = GriptapeNodes.ContextManager()._clipboard.node_commands
        if commands is None:
            return DeserializeSelectedNodesFromCommandsResultFailure(result_details="No Node Commands Found")
        connections = commands.serialized_connection_commands
        node_uuid_to_name = {}
        # Enumerate because positions is in the same order as the node commands.
        for i, node_command in enumerate(commands.serialized_node_commands):
            # Create a deepcopy of the metadata so the nodes don't all share the same position.
            node_command.create_node_command.metadata = copy.deepcopy(node_command.create_node_command.metadata)
            if request.positions is not None and len(request.positions) > i:
                if node_command.create_node_command.metadata is None:
                    node_command.create_node_command.metadata = {
                        "position": {"x": request.positions[i][0], "y": request.positions[i][1]}
                    }
                else:
                    node_command.create_node_command.metadata["position"] = {
                        "x": request.positions[i][0],
                        "y": request.positions[i][1],
                    }
            result = self.on_deserialize_node_from_commands(
                DeserializeNodeFromCommandsRequest(serialized_node_commands=node_command)
            )
            if not isinstance(result, DeserializeNodeFromCommandsResultSuccess):
                details = "Attempted to deserialize node but ran into an error on node serialization."
                return DeserializeSelectedNodesFromCommandsResultFailure(result_details=details)
            node_uuid_to_name[node_command.node_uuid] = result.node_name
            node = GriptapeNodes.ObjectManager().attempt_get_object_by_name_as_type(result.node_name, BaseNode)
            if node is None:
                details = "Attempted to deserialize node but ran into an error on node serialization."
                return DeserializeSelectedNodesFromCommandsResultFailure(result_details=details)
            with GriptapeNodes.ContextManager().node(node=node):
                parameter_commands = commands.set_parameter_value_commands[node_command.node_uuid]
                for parameter_command in parameter_commands:
                    param_request = parameter_command.set_parameter_value_command
                    # Set the Node name
                    param_request.node_name = result.node_name
                    # Set the new value
                    table = GriptapeNodes.ContextManager()._clipboard.parameter_uuid_to_values
                    if table and parameter_command.unique_value_uuid in table:
                        value = table[parameter_command.unique_value_uuid]
                        # Using try-except-pass instead of contextlib.suppress because it's clearer.
                        try:  # noqa: SIM105
                            # If we're pasting multiple times - we need to create a new copy for each paste so they don't all have the same reference.
                            value = copy.deepcopy(value)
                        except Exception:  # noqa: S110
                            pass
                        param_request.value = value
                        set_parameter_result = GriptapeNodes.handle_request(
                            parameter_command.set_parameter_value_command
                        )
                        if not set_parameter_result.succeeded():
                            details = f"Failed to set parameter value for {param_request.parameter_name} on node {param_request.node_name}"
                            logger.warning(details)
                lock_command = commands.set_lock_commands_per_node[node_command.node_uuid]
                if lock_command is not None:
                    lock_node_result = GriptapeNodes.handle_request(lock_command)
                    if not lock_node_result.succeeded():
                        details = f"Failed to lock node {lock_command.node_name}"
                        logger.warning(details)
        # create Connections
        for connection_command in connections:
            connection_request = CreateConnectionRequest(
                source_node_name=node_uuid_to_name[connection_command.source_node_uuid],
                source_parameter_name=connection_command.source_parameter_name,
                target_node_name=node_uuid_to_name[connection_command.target_node_uuid],
                target_parameter_name=connection_command.target_parameter_name,
            )
            result = GriptapeNodes.handle_request(connection_request)
            if not result.succeeded():
                details = f"Failed to create a connection between {connection_request.source_node_name} and {connection_request.target_node_name}"
                logger.warning(details)
        return DeserializeSelectedNodesFromCommandsResultSuccess(
            node_names=list(node_uuid_to_name.values()),
            result_details=f"Successfully deserialized {len(node_uuid_to_name)} nodes from commands.",
        )

    def on_duplicate_selected_nodes(self, request: DuplicateSelectedNodesRequest) -> ResultPayload:
        result = GriptapeNodes.handle_request(
            SerializeSelectedNodesToCommandsRequest(nodes_to_serialize=request.nodes_to_duplicate)
        )
        if not result.succeeded():
            details = "Failed to serialized selected nodes."
            return DuplicateSelectedNodesResultFailure(result_details=details)
        result = GriptapeNodes.handle_request(DeserializeSelectedNodesFromCommandsRequest(positions=request.positions))
        if not isinstance(result, DeserializeSelectedNodesFromCommandsResultSuccess):
            details = "Failed to deserialize selected nodes."
            return DuplicateSelectedNodesResultFailure(result_details=details)

        # Remake duplicate connections of node
        # request.nodes_to_duplicate is in this format: ['nodes_to_duplicate1', 'time'], ['nodes_to_duplicate2', 'time']
        # This list comprehension gets the first element in each sublist in order to generate the old_node_names
        initial_nodes = [sublist[0] for sublist in request.nodes_to_duplicate]

        NodeManager.remake_connections(self, new_node_names=result.node_names, old_node_names=initial_nodes)
        return DuplicateSelectedNodesResultSuccess(
            result.node_names, result_details=f"Successfully duplicated {len(initial_nodes)} nodes."
        )

    @staticmethod
    def _manage_alter_details(parameter: Parameter, base_node_obj: BaseNode) -> dict:
        base_param = base_node_obj.get_parameter_by_name(parameter.name)
        if base_param:
            diff = base_param.equals(parameter)
        else:
            return vars(parameter)
        return diff

    @staticmethod
    def _handle_value_hashing(  # noqa: PLR0913
        value: Any,
        serialized_parameter_value_tracker: SerializedParameterValueTracker,
        unique_parameter_uuid_to_values: dict,
        parameter: Parameter,
        parameter_name: str,
        node_name: str,
        *,
        is_output: bool,
    ) -> SerializedNodeCommands.IndirectSetParameterValueCommand | None:
        try:
            hash(value)
            value_id = (type(value), value)
        except TypeError:
            # Couldn't get a hash. Use the object's ID
            value_id = id(value)

        tracker_status = serialized_parameter_value_tracker.get_tracker_state(value_id)
        match tracker_status:
            case SerializedParameterValueTracker.TrackerState.SERIALIZABLE:
                # We have a match on this value. We're all good.
                unique_uuid = serialized_parameter_value_tracker.get_uuid_for_value_hash(value_id)
            case SerializedParameterValueTracker.TrackerState.NOT_SERIALIZABLE:
                # This value is not serializable. Bail.
                return None
            case SerializedParameterValueTracker.TrackerState.NOT_IN_TRACKER:
                # This value is new for us.

                # Check if parameter is marked as non-serializable (e.g., ImageDrivers, PromptDrivers, file handles)
                if not parameter.serializable:
                    serialized_parameter_value_tracker.add_as_not_serializable(value_id)
                    return None

                # Check if we can serialize it.
                try:
                    pickle.dumps(value)
                except Exception:
                    # Not serializable; don't waste time on future attempts.
                    serialized_parameter_value_tracker.add_as_not_serializable(value_id)
                    # Bail.
                    return None
                # The value should be serialized. Add it to the map of uniques.
                unique_uuid = SerializedNodeCommands.UniqueParameterValueUUID(str(uuid4()))
                try:
                    unique_parameter_uuid_to_values[unique_uuid] = copy.deepcopy(value)
                except Exception:
                    details = f"Attempted to serialize parameter '{parameter_name}` on node '{node_name}'. The parameter value could not be copied. It will be serialized by value. If problems arise from this, ensure the type '{type(value)}' works with copy.deepcopy()."
                    logger.warning(details)
                    unique_parameter_uuid_to_values[unique_uuid] = value
                serialized_parameter_value_tracker.add_as_serializable(value_id, unique_uuid)

        # Serialize it
        set_value_command = SetParameterValueRequest(
            parameter_name=parameter_name,
            value=None,  # <- this will get overridden when instantiated
            is_output=is_output,
            initial_setup=True,
        )
        indirect_set_value_command = SerializedNodeCommands.IndirectSetParameterValueCommand(
            set_parameter_value_command=set_value_command,
            unique_value_uuid=unique_uuid,
        )
        return indirect_set_value_command

    @staticmethod
    def handle_parameter_value_saving(
        parameter: Parameter,
        node: BaseNode,
        unique_parameter_uuid_to_values: dict[SerializedNodeCommands.UniqueParameterValueUUID, Any],
        serialized_parameter_value_tracker: SerializedParameterValueTracker,
        create_node_request: CreateNodeRequest,
    ) -> list[SerializedNodeCommands.IndirectSetParameterValueCommand] | None:
        """Generates code to save a parameter value for a node in a Griptape workflow.

        This function handles the process of creating commands that will reconstruct and set
        parameter values for nodes. It performs the following steps:
        1. Retrieves the parameter value from the node's parameter values or output values
        2. Checks if the value has already been created in our map of unique values
        3. If so, it records the unique value UUID for later correlation.
        4. If not, confirm that the value will serialize reliably. If so,it adds the value to the uniques map and records the new UUID.
        5. Creates a SetParameterValueRequest to reconstruct this for the node

        Args:
            parameter (Parameter): The parameter object containing metadata
            node (BaseNode): The node object that contains the parameter
            unique_parameter_uuid_to_values (dict[SerializedNodeCommands.UniqueParameterValueUUID, Any]): Dictionary mapping unique value UUIDs to values
            serialized_parameter_value_tracker (SerializedParameterValueTracker): Object mapping maintaining value hashes to unique value UUIDs, and non-serializable values
            create_node_request (CreateNodeRequest): The node creation request that will be modified if serialization fails

        Returns:
            None (if no value to be serialized) or an IndirectSetParameterValueCommand linking the value to the unique value map

        Notes:
            - Parameter output values take precedence over regular parameter values
            - For values that can be hashed, the value itself is used as the key in values_created
            - For unhashable values, the object's id is used as the key
            - The function will reuse already created values to avoid duplication
        """
        output_value = None
        internal_value = None
        if parameter.name in node.parameter_output_values:
            # Output values are more important.
            output_value = node.parameter_output_values[parameter.name]
        if parameter.name in node.parameter_values:
            # Check the internal parameter values
            internal_value = node.get_parameter_value(parameter.name)
        # We have a value. Attempt to get a hash for it to see if it matches one
        # we've already indexed.
        commands = []
        if internal_value is not None:
            internal_command = NodeManager._handle_value_hashing(
                value=internal_value,
                serialized_parameter_value_tracker=serialized_parameter_value_tracker,
                unique_parameter_uuid_to_values=unique_parameter_uuid_to_values,
                parameter=parameter,
                is_output=False,
                parameter_name=parameter.name,
                node_name=node.name,
            )
            if internal_command is None:
                details = f"Attempted to serialize set value for parameter '{parameter.name}' on node '{node.name}'. The set value will not be restored in anything that attempts to deserialize or save this node. The value for this parameter was not serialized because it did not match Griptape Nodes' criteria for serializability. To remedy, either update the value's type to support serializability or mark the parameter as not serializable by setting serializable=False when creating the parameter."
                logger.warning(details)
                # Set node to unresolved when serialization fails
                create_node_request.resolution = NodeResolutionState.UNRESOLVED.value
            else:
                commands.append(internal_command)
        if output_value is not None:
            output_command = NodeManager._handle_value_hashing(
                value=output_value,
                serialized_parameter_value_tracker=serialized_parameter_value_tracker,
                unique_parameter_uuid_to_values=unique_parameter_uuid_to_values,
                parameter=parameter,
                is_output=True,
                parameter_name=parameter.name,
                node_name=node.name,
            )
            if output_command is None:
                details = f"Attempted to serialize output value for parameter '{parameter.name}' on node '{node.name}'. The output value will not be restored in anything that attempts to deserialize or save this node. The value for this parameter was not serialized because it did not match Griptape Nodes' criteria for serializability. To remedy, either update the value's type to support serializability or mark the parameter as not serializable by setting serializable=False when creating the parameter."
                logger.warning(details)
                # Set node to unresolved when serialization fails
                create_node_request.resolution = NodeResolutionState.UNRESOLVED.value
            else:
                commands.append(output_command)
        return commands if commands else None

    @staticmethod
    def serialize_parameter_output_values(node: BaseNode, *, use_pickling: bool = False) -> SerializedParameterValues:
        """Serialize parameter output values with optional pickling for complex objects.

        Args:
            node: The node whose parameter output values should be serialized
            use_pickling: If True, use pickle-based serialization; if False, use TypeValidator.safe_serialize

        Returns:
            SerializedParameterValues containing:
            - parameter_output_values: Either raw values or UUID references if pickling was used
            - unique_parameter_uuid_to_values: Dictionary of pickled values (None if no pickling needed)
        """
        if not node.parameters:
            return SerializedParameterValues({}, None)

        if not use_pickling:
            return NodeManager._serialize_without_pickling(node)

        return NodeManager._serialize_with_pickling(node)

    @staticmethod
    def _serialize_without_pickling(node: BaseNode) -> SerializedParameterValues:
        """Serialize parameter values using simple TypeValidator serialization.

        Args:
            node: The node whose parameter values should be serialized

        Returns:
            SerializedParameterValues with no pickling
        """
        param_values = {}
        for param in node.parameters:
            if param.name in node.parameter_output_values:
                param_values[param.name] = node.parameter_output_values[param.name]
            else:
                param_values[param.name] = node.get_parameter_value(param.name)
        simple_values = TypeValidator.safe_serialize(param_values)
        return SerializedParameterValues(simple_values, None)

    @staticmethod
    def _serialize_with_pickling(
        node: BaseNode,
    ) -> SerializedParameterValues:
        """Serialize parameter values using pickle-based serialization with UUID references.

        Args:
            node: The node whose parameter values should be serialized

        Returns:
            SerializedParameterValues with pickled values
        """
        unique_parameter_uuid_to_values = {}
        serialized_parameter_value_tracker = SerializedParameterValueTracker()
        uuid_referenced_values = {}

        for parameter in node.parameters:
            param_name = parameter.name
            param_value = NodeManager._get_parameter_value_for_serialization(node, param_name)

            unique_uuid = NodeManager._process_parameter_for_pickling(
                param_value,
                param_name,
                serialized_parameter_value_tracker,
                unique_parameter_uuid_to_values,
                uuid_referenced_values,
            )

            uuid_referenced_values[param_name] = unique_uuid

        return SerializedParameterValues(
            uuid_referenced_values, unique_parameter_uuid_to_values if unique_parameter_uuid_to_values else None
        )

    @staticmethod
    def _get_parameter_value_for_serialization(node: BaseNode, param_name: str) -> Any:
        """Get parameter value for serialization, checking output values first.

        Args:
            node: The node to get the parameter value from
            param_name: The parameter name

        Returns:
            The parameter value
        """
        if param_name in node.parameter_output_values:
            return node.parameter_output_values[param_name]
        return node.get_parameter_value(param_name)

    @staticmethod
    def _process_parameter_for_pickling(
        param_value: Any,
        param_name: str,
        tracker: SerializedParameterValueTracker,
        unique_parameter_uuid_to_values: dict,
        uuid_referenced_values: dict,
    ) -> SerializedNodeCommands.UniqueParameterValueUUID | None:
        """Process a parameter value for pickle-based serialization.

        Args:
            param_value: The value to serialize
            param_name: Parameter name for tracking
            tracker: Tracker for managing serialization state
            unique_parameter_uuid_to_values: Dictionary to store pickled values
            uuid_referenced_values: Dictionary to store UUID references

        Returns:
            UUID reference for the value, or None if not serializable
        """
        try:
            hash(param_value)
            value_id = param_value
        except TypeError:
            value_id = id(param_value)

        tracker_status = tracker.get_tracker_state(value_id)

        match tracker_status:
            case SerializedParameterValueTracker.TrackerState.SERIALIZABLE:
                return tracker.get_uuid_for_value_hash(value_id)
            case SerializedParameterValueTracker.TrackerState.NOT_SERIALIZABLE:
                uuid_referenced_values[param_name] = None
                return None
            case SerializedParameterValueTracker.TrackerState.NOT_IN_TRACKER:
                return NodeManager._handle_new_value_for_pickling(
                    param_value, param_name, tracker, unique_parameter_uuid_to_values, uuid_referenced_values
                )

    @staticmethod
    def _handle_new_value_for_pickling(
        param_value: Any,
        param_name: str,
        tracker: SerializedParameterValueTracker,
        unique_parameter_uuid_to_values: dict,
        uuid_referenced_values: dict,
    ) -> SerializedNodeCommands.UniqueParameterValueUUID | None:
        """Handle a new value that hasn't been seen before in pickling serialization.

        Args:
            param_value: The value to pickle
            param_name: Parameter name for tracking
            tracker: Tracker for managing serialization state
            unique_parameter_uuid_to_values: Dictionary to store pickled values
            uuid_referenced_values: Dictionary to store UUID references

        Returns:
            UUID reference for the value, or None if not serializable
        """
        try:
            hash(param_value)
            value_id = param_value
        except TypeError:
            value_id = id(param_value)

        try:
            workflow_manager = GriptapeNodes.WorkflowManager()
            pickled_bytes = workflow_manager._patch_and_pickle_object(param_value)
        except Exception:
            tracker.add_as_not_serializable(value_id)
            uuid_referenced_values[param_name] = None
            return None

        unique_uuid = SerializedNodeCommands.UniqueParameterValueUUID(str(uuid4()))
        unique_parameter_uuid_to_values[unique_uuid] = pickled_bytes
        tracker.add_as_serializable(value_id, unique_uuid)
        return unique_uuid

    def on_rename_parameter_request(self, request: RenameParameterRequest) -> ResultPayload:  # noqa: C901, PLR0911, PLR0912
        """Handle renaming a parameter on a node.

        Args:
            request: The rename parameter request containing the old and new parameter names

        Returns:
            ResultPayload: Success or failure result
        """
        # Get the node
        node_name = request.node_name
        if node_name is None:
            if not GriptapeNodes.ContextManager().has_current_node():
                details = "Attempted to rename Parameter in the Current Context. Failed because the Current Context was empty."
                return RenameParameterResultFailure(result_details=details)
            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name
        else:
            try:
                node = self.get_node_by_name(node_name)
            except KeyError as err:
                details = f"Attempted to rename Parameter '{request.parameter_name}' on Node '{node_name}'. Failed because the Node could not be found. Error: {err}"
                return RenameParameterResultFailure(result_details=details)

        # Is the node locked?
        if node.lock:
            details = f"Attempted to rename Parameter '{request.parameter_name}' on Node '{node_name}'. Failed because the Node is locked."
            return RenameParameterResultFailure(result_details=details)

        # Get the parameter
        parameter = node.get_parameter_by_name(request.parameter_name)
        if parameter is None:
            details = f"Attempted to rename Parameter '{request.parameter_name}' on Node '{node_name}'. Failed because the Parameter could not be found."
            return RenameParameterResultFailure(result_details=details)

        # Only allow parameter rename for user-defined params
        if not parameter.user_defined:
            details = f"Attempted to rename Parameter '{request.parameter_name}' on Node '{node_name}'. Failed because the Parameter is not user-defined."
            return RenameParameterResultFailure(result_details=details)

        # Validate the new parameter name
        if any(char.isspace() for char in request.new_parameter_name):
            details = f"Failed to rename Parameter '{request.parameter_name}' to '{request.new_parameter_name}'. Parameter names cannot contain any whitespace characters."
            return RenameParameterResultFailure(result_details=details)

        # Check for duplicate names
        if node.does_name_exist(request.new_parameter_name):
            details = f"Failed to rename Parameter '{request.parameter_name}' to '{request.new_parameter_name}'. A Parameter with that name already exists."
            return RenameParameterResultFailure(result_details=details)

        # Get all connections for this node
        flow_name = self.get_node_parent_flow_by_name(node_name)
        GriptapeNodes.FlowManager().get_flow_by_name(flow_name)
        connections = GriptapeNodes.FlowManager().get_connections()

        # Update connections that reference this parameter
        if node_name in connections.incoming_index:
            incoming_connections = connections.incoming_index[node_name]
            for connection_ids in incoming_connections.values():
                for connection_id in connection_ids:
                    connection = connections.connections[connection_id]
                    if connection.target_parameter.name == request.parameter_name:
                        connection.target_parameter.name = request.new_parameter_name

        if node_name in connections.outgoing_index:
            outgoing_connections = connections.outgoing_index[node_name]
            for connection_ids in outgoing_connections.values():
                for connection_id in connection_ids:
                    connection = connections.connections[connection_id]
                    if connection.source_parameter.name == request.parameter_name:
                        connection.source_parameter.name = request.new_parameter_name

        # Update parameter name
        old_name = parameter.name
        parameter.name = request.new_parameter_name

        # Update parameter values if they exist
        if old_name in node.parameter_values:
            node.parameter_values[request.new_parameter_name] = node.parameter_values.pop(old_name)
        if old_name in node.parameter_output_values:
            node.parameter_output_values[request.new_parameter_name] = node.parameter_output_values.pop(old_name)

        return RenameParameterResultSuccess(
            old_parameter_name=old_name,
            new_parameter_name=request.new_parameter_name,
            node_name=node_name,
            result_details=f"Successfully renamed parameter '{old_name}' to '{request.new_parameter_name}' on node '{node_name}'.",
        )

    def on_toggle_lock_node_request(self, request: SetLockNodeStateRequest) -> ResultPayload:
        node_name = request.node_name
        if node_name is None:
            if not GriptapeNodes.ContextManager().has_current_node():
                details = "Attempted to lock node in the Current Context. Failed because the Current Context was empty."
                return SetLockNodeStateResultFailure(result_details=details)
            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name
        else:
            try:
                node = self.get_node_by_name(node_name)
            except ValueError as err:
                details = f"Attempted to lock node '{request.node_name}'. Failed because the Node could not be found. Error: {err}"
                return SetLockNodeStateResultFailure(result_details=details)
        node.lock = request.lock
        return SetLockNodeStateResultSuccess(
            node_name=node_name,
            locked=node.lock,
            result_details=f"Successfully set lock state to {node.lock} for node '{node_name}'.",
        )

    def on_send_node_message_request(self, request: SendNodeMessageRequest) -> ResultPayload:
        """Handle a SendNodeMessageRequest by calling the node's message callback.

        Args:
            request: The SendNodeMessageRequest containing message details

        Returns:
            ResultPayload: Success or failure result with callback response
        """
        node_name = request.node_name
        node = None

        if node_name is None:
            # Get from the current context
            if not GriptapeNodes.ContextManager().has_current_node():
                details = "Attempted to send message to Node from Current Context. Failed because the Current Context is empty."
                return SendNodeMessageResultFailure(result_details=details)

            node = GriptapeNodes.ContextManager().get_current_node()
            node_name = node.name

        if node is None:
            # Find the node by name
            obj_mgr = GriptapeNodes.ObjectManager()
            node = obj_mgr.attempt_get_object_by_name_as_type(node_name, BaseNode)
            if node is None:
                details = f"Attempted to send message to Node '{node_name}', but no such Node was found."
                return SendNodeMessageResultFailure(result_details=details)

        # Validate optional_element_name if specified
        if request.optional_element_name is not None:
            element = node.root_ui_element.find_element_by_name(request.optional_element_name)
            if element is None:
                details = f"Attempted to send message to Node '{node_name}' with element '{request.optional_element_name}', but no such element was found."
                return SendNodeMessageResultFailure(result_details=details, altered_workflow_state=False)

        # Call the node's message callback
        callback_result = node.on_node_message_received(
            optional_element_name=request.optional_element_name,
            message_type=request.message_type,
            message=request.message,
        )

        if not callback_result.success:
            details = f"Failed to handle message for Node '{node_name}': {callback_result.details}"
            return SendNodeMessageResultFailure(
                result_details=callback_result.details,
                response=callback_result.response,
                altered_workflow_state=callback_result.altered_workflow_state,
            )

        details = f"Successfully sent message to Node '{node_name}': {callback_result.details}"
        return SendNodeMessageResultSuccess(
            result_details=callback_result.details,
            response=callback_result.response,
            altered_workflow_state=callback_result.altered_workflow_state,
        )

    def on_get_flow_for_node_request(self, request: GetFlowForNodeRequest) -> ResultPayload:
        """Get the flow name that contains a specific node."""
        try:
            flow_name = self.get_node_parent_flow_by_name(request.node_name)
            return GetFlowForNodeResultSuccess(
                flow_name=flow_name,
                result_details=f"Successfully retrieved flow '{flow_name}' for node '{request.node_name}'.",
            )
        except KeyError:
            return GetFlowForNodeResultFailure(
                result_details=f"Node '{request.node_name}' not found or not assigned to any flow.",
            )

    def on_migrate_parameter_request(
        self, request: MigrateParameterRequest
    ) -> MigrateParameterResultFailure | MigrateParameterResultSuccess:
        """Handle parameter migration requests."""
        # Validate nodes exist - get_node_by_name can raise ValueError
        try:
            source_node = self.get_node_by_name(request.source_node_name)
            target_node = self.get_node_by_name(request.target_node_name)
            logger.debug(
                "Successfully validated nodes exist for parameter migration: %s -> %s",
                source_node.name,
                target_node.name,
            )
        except ValueError as e:
            return MigrateParameterResultFailure(result_details=f"Node validation failed: {e}")

        # Get connections for the source parameter
        connections_result = self.on_get_connections_for_parameter_request(
            GetConnectionsForParameterRequest(
                parameter_name=request.source_parameter_name, node_name=request.source_node_name
            )
        )

        if not isinstance(connections_result, GetConnectionsForParameterResultSuccess):
            return MigrateParameterResultFailure(
                result_details=f"Failed to get connections for parameter '{request.source_parameter_name}' on node '{request.source_node_name}'."
            )

        # Break original connections if requested (do this FIRST before creating new connections)
        if request.break_connections:
            self._break_parameter_connections(
                connections_result, request.source_node_name, request.source_parameter_name
            )

        # Handle incoming connections
        if connections_result.has_incoming_connections():
            result = self._migrate_incoming_connections(request, connections_result)
            if isinstance(result, MigrateParameterResultFailure):
                return result

        # Handle outgoing connections
        if connections_result.has_outgoing_connections():
            result = self._migrate_outgoing_connections(request, connections_result)
            if isinstance(result, MigrateParameterResultFailure):
                return result

        # Handle value migration (no incoming connections)
        if not connections_result.has_incoming_connections():
            result = self._migrate_parameter_value(request)
            if isinstance(result, MigrateParameterResultFailure):
                return result

        return MigrateParameterResultSuccess(
            result_details=f"Successfully migrated parameter '{request.source_parameter_name}' from '{request.source_node_name}' to '{request.target_parameter_name}' on '{request.target_node_name}'."
        )

    def _break_parameter_connections(
        self,
        connections_result: GetConnectionsForParameterResultSuccess,
        source_node_name: str,
        source_parameter_name: str,
    ) -> None:
        """Break all incoming and outgoing connections for a parameter."""
        # Break incoming connections
        for incoming_connection in connections_result.incoming_connections:
            delete_result = GriptapeNodes.handle_request(
                DeleteConnectionRequest(
                    source_node_name=incoming_connection.source_node_name,
                    source_parameter_name=incoming_connection.source_parameter_name,
                    target_node_name=source_node_name,
                    target_parameter_name=source_parameter_name,
                )
            )
            if not isinstance(delete_result, DeleteConnectionResultSuccess):
                logger.warning(
                    "Failed to break incoming connection from %s.%s: %s",
                    incoming_connection.source_node_name,
                    incoming_connection.source_parameter_name,
                    delete_result,
                )

        # Break outgoing connections
        for outgoing_connection in connections_result.outgoing_connections:
            delete_result = GriptapeNodes.handle_request(
                DeleteConnectionRequest(
                    source_node_name=source_node_name,
                    source_parameter_name=source_parameter_name,
                    target_node_name=outgoing_connection.target_node_name,
                    target_parameter_name=outgoing_connection.target_parameter_name,
                )
            )
            if not isinstance(delete_result, DeleteConnectionResultSuccess):
                logger.warning(
                    "Failed to break outgoing connection to %s.%s: %s",
                    outgoing_connection.target_node_name,
                    outgoing_connection.target_parameter_name,
                    delete_result,
                )

    def _migrate_incoming_connections(
        self, request: MigrateParameterRequest, connections_result: GetConnectionsForParameterResultSuccess
    ) -> MigrateParameterResultFailure | None:
        """Handle migrating incoming connections with or without conversion."""
        if request.input_conversion:
            return self._create_input_conversion_node(request, connections_result)
        return self._create_direct_incoming_connections(request, connections_result)

    def _migrate_outgoing_connections(
        self, request: MigrateParameterRequest, connections_result: GetConnectionsForParameterResultSuccess
    ) -> MigrateParameterResultFailure | None:
        """Handle migrating outgoing connections with or without conversion."""
        if request.output_conversion:
            return self._create_output_conversion_node(request, connections_result)
        return self._create_direct_outgoing_connections(request, connections_result)

    def _migrate_parameter_value(self, request: MigrateParameterRequest) -> MigrateParameterResultFailure | None:
        """Handle migrating parameter value when no incoming connections exist."""
        # Get the current value from source
        get_value_result = GriptapeNodes.handle_request(
            GetParameterValueRequest(node_name=request.source_node_name, parameter_name=request.source_parameter_name)
        )

        if not isinstance(get_value_result, GetParameterValueResultSuccess):
            return MigrateParameterResultFailure(
                result_details=f"Failed to get value for parameter '{request.source_parameter_name}' on node '{request.source_node_name}'."
            )

        # Apply transformation if provided - this is user code that can raise exceptions
        value = get_value_result.value
        if request.value_transform:
            try:
                value = request.value_transform(value)
            except Exception as e:
                return MigrateParameterResultFailure(result_details=f"Failed to apply value transformation: {e!s}")

        # Set the value on target
        set_value_result = GriptapeNodes.handle_request(
            SetParameterValueRequest(
                node_name=request.target_node_name, parameter_name=request.target_parameter_name, value=value
            )
        )

        if not isinstance(set_value_result, SetParameterValueResultSuccess):
            return MigrateParameterResultFailure(
                result_details=f"Failed to set value for parameter '{request.target_parameter_name}' on node '{request.target_node_name}'."
            )

        return None

    def _create_input_conversion_node(
        self, request: MigrateParameterRequest, connections_result: GetConnectionsForParameterResultSuccess
    ) -> MigrateParameterResultFailure | None:
        """Create intermediate node for input conversion."""
        intermediate_node_name = f"{request.target_node_name}_{request.source_parameter_name}_input_converter"
        input_conversion = request.input_conversion
        if input_conversion is None:
            return MigrateParameterResultFailure(result_details="Input conversion configuration is required")

        # Create the intermediate node
        offset_side = input_conversion.offset_side or "left"
        create_node_result = RetainedMode.create_node_relative_to(
            reference_node_name=request.target_node_name,
            new_node_type=input_conversion.node_type,
            new_node_name=intermediate_node_name,
            specific_library_name=input_conversion.library,
            offset_side=offset_side,  # type: ignore[arg-type]
            offset_x=input_conversion.offset_x,
            offset_y=input_conversion.offset_y,
        )

        if not isinstance(create_node_result, str):
            return MigrateParameterResultFailure(
                result_details=f"Failed to create intermediate node '{intermediate_node_name}': {create_node_result}"
            )

        # Set additional parameters
        if input_conversion.additional_parameters:
            for param_name, param_value in input_conversion.additional_parameters.items():
                set_value_result = GriptapeNodes.handle_request(
                    SetParameterValueRequest(
                        node_name=intermediate_node_name, parameter_name=param_name, value=param_value
                    )
                )
                if not isinstance(set_value_result, SetParameterValueResultSuccess):
                    return MigrateParameterResultFailure(
                        result_details=f"Failed to set parameter '{param_name}' on intermediate node '{intermediate_node_name}': {set_value_result}"
                    )

        # Connect all sources to intermediate node
        for incoming_connection in connections_result.incoming_connections:
            connection_result = GriptapeNodes.handle_request(
                CreateConnectionRequest(
                    source_node_name=incoming_connection.source_node_name,
                    source_parameter_name=incoming_connection.source_parameter_name,
                    target_node_name=intermediate_node_name,
                    target_parameter_name=input_conversion.input_parameter,
                )
            )

            if not isinstance(connection_result, CreateConnectionResultSuccess):
                return MigrateParameterResultFailure(
                    result_details=f"Failed to connect source '{incoming_connection.source_node_name}.{incoming_connection.source_parameter_name}' to intermediate node: {connection_result}"
                )

        # Connect intermediate node to target
        connection_result = GriptapeNodes.handle_request(
            CreateConnectionRequest(
                source_node_name=intermediate_node_name,
                source_parameter_name=input_conversion.output_parameter,
                target_node_name=request.target_node_name,
                target_parameter_name=request.target_parameter_name,
            )
        )

        if not isinstance(connection_result, CreateConnectionResultSuccess):
            return MigrateParameterResultFailure(
                result_details=f"Failed to connect intermediate node to target: {connection_result}"
            )

        return None

    def _create_direct_incoming_connections(
        self, request: MigrateParameterRequest, connections_result: GetConnectionsForParameterResultSuccess
    ) -> MigrateParameterResultFailure | None:
        """Create direct incoming connections without conversion."""
        for incoming_connection in connections_result.incoming_connections:
            connection_result = GriptapeNodes.handle_request(
                CreateConnectionRequest(
                    source_node_name=incoming_connection.source_node_name,
                    source_parameter_name=incoming_connection.source_parameter_name,
                    target_node_name=request.target_node_name,
                    target_parameter_name=request.target_parameter_name,
                )
            )

            if not isinstance(connection_result, CreateConnectionResultSuccess):
                return MigrateParameterResultFailure(
                    result_details=f"Failed to create direct connection from '{incoming_connection.source_node_name}.{incoming_connection.source_parameter_name}': {connection_result}"
                )

        return None

    def _create_output_conversion_node(
        self, request: MigrateParameterRequest, connections_result: GetConnectionsForParameterResultSuccess
    ) -> MigrateParameterResultFailure | None:
        """Create intermediate node for output conversion."""
        intermediate_node_name = f"{request.target_node_name}_{request.source_parameter_name}_output_converter"
        output_conversion = request.output_conversion
        if output_conversion is None:
            return MigrateParameterResultFailure(result_details="Output conversion configuration is required")

        # Create the intermediate node
        offset_side = output_conversion.offset_side or "right"
        create_node_result = RetainedMode.create_node_relative_to(
            reference_node_name=request.target_node_name,
            new_node_type=output_conversion.node_type,
            new_node_name=intermediate_node_name,
            specific_library_name=output_conversion.library,
            offset_side=offset_side,  # type: ignore[arg-type]
            offset_x=output_conversion.offset_x,
            offset_y=output_conversion.offset_y,
        )

        if not isinstance(create_node_result, str):
            return MigrateParameterResultFailure(
                result_details=f"Failed to create intermediate node '{intermediate_node_name}': {create_node_result}"
            )

        # Set additional parameters
        if output_conversion.additional_parameters:
            for param_name, param_value in output_conversion.additional_parameters.items():
                set_value_result = GriptapeNodes.handle_request(
                    SetParameterValueRequest(
                        node_name=intermediate_node_name, parameter_name=param_name, value=param_value
                    )
                )
                if not isinstance(set_value_result, SetParameterValueResultSuccess):
                    return MigrateParameterResultFailure(
                        result_details=f"Failed to set parameter '{param_name}' on intermediate node '{intermediate_node_name}': {set_value_result}"
                    )

        # Connect target to intermediate node
        connection_result = GriptapeNodes.handle_request(
            CreateConnectionRequest(
                source_node_name=request.target_node_name,
                source_parameter_name=request.target_parameter_name,
                target_node_name=intermediate_node_name,
                target_parameter_name=output_conversion.input_parameter,
            )
        )

        if not isinstance(connection_result, CreateConnectionResultSuccess):
            return MigrateParameterResultFailure(
                result_details=f"Failed to connect target to intermediate node: {connection_result}"
            )

        # Connect intermediate node to all destinations
        for outgoing_connection in connections_result.outgoing_connections:
            connection_result = GriptapeNodes.handle_request(
                CreateConnectionRequest(
                    source_node_name=intermediate_node_name,
                    source_parameter_name=output_conversion.output_parameter,
                    target_node_name=outgoing_connection.target_node_name,
                    target_parameter_name=outgoing_connection.target_parameter_name,
                )
            )

            if not isinstance(connection_result, CreateConnectionResultSuccess):
                return MigrateParameterResultFailure(
                    result_details=f"Failed to connect intermediate node to destination '{outgoing_connection.target_node_name}.{outgoing_connection.target_parameter_name}': {connection_result}"
                )

        return None

    def _create_direct_outgoing_connections(
        self, request: MigrateParameterRequest, connections_result: GetConnectionsForParameterResultSuccess
    ) -> MigrateParameterResultFailure | None:
        """Create direct outgoing connections without conversion."""
        for outgoing_connection in connections_result.outgoing_connections:
            connection_result = GriptapeNodes.handle_request(
                CreateConnectionRequest(
                    source_node_name=request.target_node_name,
                    source_parameter_name=request.target_parameter_name,
                    target_node_name=outgoing_connection.target_node_name,
                    target_parameter_name=outgoing_connection.target_parameter_name,
                )
            )

            if not isinstance(connection_result, CreateConnectionResultSuccess):
                return MigrateParameterResultFailure(
                    result_details=f"Failed to create direct connection to '{outgoing_connection.target_node_name}.{outgoing_connection.target_parameter_name}': {connection_result}"
                )

        return None
