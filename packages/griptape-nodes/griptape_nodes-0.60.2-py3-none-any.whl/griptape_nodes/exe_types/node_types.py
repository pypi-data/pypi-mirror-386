from __future__ import annotations

import logging
import threading
import warnings
from abc import ABC, abstractmethod
from collections.abc import Callable, Generator, Iterable
from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Any, NamedTuple, TypeVar

from griptape_nodes.exe_types.core_types import (
    BaseNodeElement,
    ControlParameterInput,
    ControlParameterOutput,
    NodeMessageResult,
    Parameter,
    ParameterContainer,
    ParameterDictionary,
    ParameterGroup,
    ParameterList,
    ParameterMessage,
    ParameterMode,
    ParameterTypeBuiltin,
)
from griptape_nodes.exe_types.param_components.execution_status_component import ExecutionStatusComponent
from griptape_nodes.exe_types.type_validator import TypeValidator
from griptape_nodes.retained_mode.events.base_events import (
    ExecutionEvent,
    ExecutionGriptapeNodeEvent,
    ProgressEvent,
    RequestPayload,
)
from griptape_nodes.retained_mode.events.parameter_events import (
    AddParameterToNodeRequest,
    RemoveElementEvent,
    RemoveParameterFromNodeRequest,
)
from griptape_nodes.traits.options import Options
from griptape_nodes.utils import async_utils

if TYPE_CHECKING:
    from griptape_nodes.exe_types.connections import Connections
    from griptape_nodes.exe_types.core_types import NodeMessagePayload
    from griptape_nodes.node_library.library_registry import LibraryNameAndVersion

logger = logging.getLogger("griptape_nodes")

T = TypeVar("T")

AsyncResult = Generator[Callable[[], T], T]

LOCAL_EXECUTION = "Local Execution"
PRIVATE_EXECUTION = "Private Execution"
CONTROL_INPUT_PARAMETER = "Control Input Selection"


class ImportDependency(NamedTuple):
    """Import dependency specification for a node.

    Attributes:
        module: The module name to import
        class_name: Optional class name to import from the module. If None, imports the entire module.
    """

    module: str
    class_name: str | None = None


@dataclass
class NodeDependencies:
    """Dependencies that a node has on external resources.

    This class provides a way for nodes to declare their dependencies on workflows,
    static files, Python imports, and libraries. This information can be used by the system
    for workflow packaging, dependency resolution, and deployment planning.

    Attributes:
        referenced_workflows: Set of workflow names that this node references
        static_files: Set of static file names that this node depends on
        imports: Set of Python imports that this node requires
        libraries: Set of library names and versions that this node uses
    """

    referenced_workflows: set[str] = field(default_factory=set)
    static_files: set[str] = field(default_factory=set)
    imports: set[ImportDependency] = field(default_factory=set)
    libraries: set[LibraryNameAndVersion] = field(default_factory=set)

    def aggregate_from(self, other: NodeDependencies) -> None:
        """Aggregate dependencies from another NodeDependencies object into this one.

        Args:
            other: The NodeDependencies object to aggregate from
        """
        # Aggregate all dependency types - no None checks needed since we use default_factory=set
        self.referenced_workflows.update(other.referenced_workflows)
        self.static_files.update(other.static_files)
        self.imports.update(other.imports)
        self.libraries.update(other.libraries)


class NodeResolutionState(StrEnum):
    """Possible states for a node during resolution."""

    UNRESOLVED = auto()
    RESOLVING = auto()
    RESOLVED = auto()


def get_library_names_with_publish_handlers() -> list[str]:
    """Get names of all registered libraries that have PublishWorkflowRequest handlers."""
    from griptape_nodes.retained_mode.events.workflow_events import PublishWorkflowRequest
    from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

    library_manager = GriptapeNodes.LibraryManager()
    event_handlers = library_manager.get_registered_event_handlers(PublishWorkflowRequest)

    # Always include "local" and "private" as the first options
    library_names = [LOCAL_EXECUTION, PRIVATE_EXECUTION]

    # Add all registered library names that can handle PublishWorkflowRequest
    library_names.extend(sorted(event_handlers.keys()))

    return library_names


class BaseNode(ABC):
    # Owned by a flow
    name: str
    metadata: dict[Any, Any]

    # Node Context Fields
    current_spotlight_parameter: Parameter | None = None
    parameter_values: dict[str, Any]
    parameter_output_values: TrackedParameterOutputValues
    stop_flow: bool = False
    root_ui_element: BaseNodeElement
    _state: NodeResolutionState
    _tracked_parameters: list[BaseNodeElement]
    _entry_control_parameter: Parameter | None = (
        None  # The control input parameter used to enter this node during execution
    )
    lock: bool = False  # When lock is true, the node is locked and can't be modified. When lock is false, the node is unlocked and can be modified.
    _cancellation_requested: threading.Event  # Event indicating if cancellation has been requested for this node

    @property
    def parameters(self) -> list[Parameter]:
        return self.root_ui_element.find_elements_by_type(Parameter)

    def __hash__(self) -> int:
        return hash(self.name)

    def __init__(
        self,
        name: str,
        metadata: dict[Any, Any] | None = None,
        state: NodeResolutionState = NodeResolutionState.UNRESOLVED,
    ) -> None:
        self.name = name
        self._state = state
        if metadata is None:
            self.metadata = {}
        else:
            self.metadata = metadata
        self.parameter_values = {}
        self.parameter_output_values = TrackedParameterOutputValues(self)
        self.root_ui_element = BaseNodeElement()
        # Set the node context for the root element
        self.root_ui_element._node_context = self
        self.process_generator = None
        self._tracked_parameters = []
        self._cancellation_requested = threading.Event()
        self.set_entry_control_parameter(None)
        self.execution_environment = Parameter(
            name="execution_environment",
            tooltip="Environment that the node should execute in",
            type=ParameterTypeBuiltin.STR,
            allowed_modes={ParameterMode.PROPERTY},
            default_value=LOCAL_EXECUTION,
            traits={Options(choices=get_library_names_with_publish_handlers())},
            ui_options={"hide": True},
        )
        self.add_parameter(self.execution_environment)
        self.node_group = Parameter(
            name="job_group",
            tooltip="Groupings of multiple nodes to send up as a Deadline Cloud job.",
            type=ParameterTypeBuiltin.STR,
            allowed_modes={ParameterMode.PROPERTY},
            default_value="",
            ui_options={"hide": True},
        )
        self.add_parameter(self.node_group)

    @property
    def state(self) -> NodeResolutionState:
        """Get the current resolution state of the node.

        Existence as @property facilitates subclasses overriding the getter for dynamic/computed state.
        """
        return self._state

    @state.setter
    def state(self, new_state: NodeResolutionState) -> None:
        self._state = new_state

    # This is gross and we need to have a universal pass on resolution state changes and emission of events. That's what this ticket does!
    # https://github.com/griptape-ai/griptape-nodes/issues/994
    def make_node_unresolved(self, current_states_to_trigger_change_event: set[NodeResolutionState] | None) -> None:
        from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

        # See if the current state is in the set of states to trigger a change event.
        if current_states_to_trigger_change_event is not None and self.state in current_states_to_trigger_change_event:
            # Trigger the change event.
            # Send an event to the GUI so it knows this node has changed resolution state.
            from griptape_nodes.retained_mode.events.execution_events import NodeUnresolvedEvent

            GriptapeNodes.EventManager().put_event(
                ExecutionGriptapeNodeEvent(
                    wrapped_event=ExecutionEvent(payload=NodeUnresolvedEvent(node_name=self.name))
                )
            )
        self.state = NodeResolutionState.UNRESOLVED
        # NOTE: _entry_control_parameter is NOT cleared here as it represents execution context
        # that should persist through the resolve/unresolve cycle during a single execution

    def set_entry_control_parameter(self, parameter: Parameter | None) -> None:
        """Set the control parameter that was used to enter this node.

        This should only be called by the ControlFlowContext during execution.

        Args:
            parameter: The control input parameter that triggered this node's execution, or None to clear
        """
        self._entry_control_parameter = parameter

    @property
    def is_cancellation_requested(self) -> bool:
        """Check if cancellation has been requested for this node.

        Returns:
            True if cancellation has been requested, False otherwise
        """
        return self._cancellation_requested.is_set()

    def request_cancellation(self) -> None:
        """Request cancellation of this node's execution.

        Sets a flag that the node can check during long-running operations
        to cooperatively cancel execution.
        """
        self._cancellation_requested.set()

    def clear_cancellation(self) -> None:
        """Clear the cancellation request flag."""
        self._cancellation_requested.clear()

    def emit_parameter_changes(self) -> None:
        if self._tracked_parameters:
            for parameter in self._tracked_parameters:
                parameter._emit_alter_element_event_if_possible()
            self._tracked_parameters.clear()

    def allow_incoming_connection(
        self,
        source_node: BaseNode,  # noqa: ARG002
        source_parameter: Parameter,  # noqa: ARG002
        target_parameter: Parameter,  # noqa: ARG002
    ) -> bool:
        """Callback to confirm allowing a Connection coming TO this Node."""
        return True

    def allow_outgoing_connection(
        self,
        source_parameter: Parameter,  # noqa: ARG002
        target_node: BaseNode,  # noqa: ARG002
        target_parameter: Parameter,  # noqa: ARG002,
    ) -> bool:
        """Callback to confirm allowing a Connection going OUT of this Node."""
        return True

    def before_incoming_connection(
        self,
        source_node: BaseNode,  # noqa: ARG002
        source_parameter_name: str,  # noqa: ARG002
        target_parameter_name: str,  # noqa: ARG002
    ) -> None:
        """Callback before validating a Connection coming TO this Node."""
        return

    def after_incoming_connection(
        self,
        source_node: BaseNode,  # noqa: ARG002
        source_parameter: Parameter,  # noqa: ARG002
        target_parameter: Parameter,  # noqa: ARG002
    ) -> None:
        """Callback after a Connection has been established TO this Node."""
        return

    def before_outgoing_connection(
        self,
        source_parameter_name: str,  # noqa: ARG002
        target_node: BaseNode,  # noqa: ARG002
        target_parameter_name: str,  # noqa: ARG002
    ) -> None:
        """Callback before validating a Connection going OUT of this Node."""
        return

    def after_outgoing_connection(
        self,
        source_parameter: Parameter,  # noqa: ARG002
        target_node: BaseNode,  # noqa: ARG002
        target_parameter: Parameter,  # noqa: ARG002
    ) -> None:
        """Callback after a Connection has been established OUT of this Node."""
        return

    def after_incoming_connection_removed(
        self,
        source_node: BaseNode,  # noqa: ARG002
        source_parameter: Parameter,  # noqa: ARG002
        target_parameter: Parameter,  # noqa: ARG002
    ) -> None:
        """Callback after a Connection TO this Node was REMOVED."""
        return

    def after_outgoing_connection_removed(
        self,
        source_parameter: Parameter,  # noqa: ARG002
        target_node: BaseNode,  # noqa: ARG002
        target_parameter: Parameter,  # noqa: ARG002
    ) -> None:
        """Callback after a Connection OUT of this Node was REMOVED."""
        return

    def before_value_set(
        self,
        parameter: Parameter,  # noqa: ARG002
        value: Any,
    ) -> Any:
        """Callback when a Parameter's value is ABOUT to be set.

        Custom nodes may elect to override the default behavior by implementing this function in their node code.

        This gives the node an opportunity to perform custom logic before a parameter is set. This may result in:
          * Further mutating the value that would be assigned to the Parameter
          * Mutating other Parameters or state within the Node

        If other Parameters are changed, the engine needs a list of which
        ones have changed to cascade unresolved state.

        Args:
            parameter: the Parameter on this node that is about to be changed
            value: the value intended to be set (this has already gone through any converters and validators on the Parameter)

        Returns:
            The final value to set for the Parameter. This gives the Node logic one last opportunity to mutate the value
            before it is assigned.
        """
        # Default behavior is to do nothing to the supplied value, and indicate no other modified Parameters.
        return value

    def after_value_set(
        self,
        parameter: Parameter,  # noqa: ARG002
        value: Any,  # noqa: ARG002
    ) -> None:
        """Callback AFTER a Parameter's value was set.

        Custom nodes may elect to override the default behavior by implementing this function in their node code.

        This gives the node an opportunity to perform custom logic after a parameter is set. This may result in
        changing other Parameters on the node. If other Parameters are changed, the engine needs a list of which
        ones have changed to cascade unresolved state.

        NOTE: Subclasses can override this method with either signature:
        - def after_value_set(self, parameter, value) -> None:  (most common)
        - def after_value_set(self, parameter, value, **kwargs) -> None:  (advanced)
        The base implementation uses **kwargs for compatibility with both patterns.
        The engine will try calling with 2 arguments first, then fall back to 3 if needed.
        Pyright may show false positive "incompatible override" warnings for the 2-argument
        version - this is expected and the code will work correctly at runtime.

        Args:
            parameter: the Parameter on this node that was just changed
            value: the value that was set (already converted, validated, and possibly mutated by the node code)

        Returns:
            Nothing
        """
        # Default behavior is to do nothing, and indicate no other modified Parameters.
        return None  # noqa: RET501

    def after_settings_changed(self, **kwargs: Any) -> None:  # noqa: ARG002
        """Callback for when the settings of this Node are changed."""
        # Waiting for https://github.com/griptape-ai/griptape-nodes/issues/1309
        return

    def on_node_message_received(
        self,
        optional_element_name: str | None,
        message_type: str,
        message: NodeMessagePayload | None,
    ) -> NodeMessageResult:
        """Callback for when a message is sent directly to this node.

        Custom nodes may elect to override this method to handle specific message types
        and implement custom communication patterns with external systems.

        If optional_element_name is provided, this method will attempt to find the
        element and delegate the message handling to that element's on_message_received method.

        Args:
            optional_element_name: Optional element name this message relates to
            message_type: String indicating the message type for parsing
            message: Message payload of any type

        Returns:
            NodeMessageResult: Result containing success status, details, and optional response
        """
        # If optional_element_name is provided, delegate to the specific element
        if optional_element_name is not None:
            element = self.root_ui_element.find_element_by_name(optional_element_name)
            if element is None:
                return NodeMessageResult(
                    success=False,
                    details=f"Node '{self.name}' received message for element '{optional_element_name}' but no element with that name was found",
                    response=None,
                )
            # Delegate to the element's message handler
            result = element.on_message_received(message_type, message)
            if result is None:
                return NodeMessageResult(
                    success=False,
                    details=f"Element '{optional_element_name}' received message type '{message_type}' but no handler was available",
                    response=None,
                )
            return result

        # If no element name specified, fall back to node-level handling
        return NodeMessageResult(
            success=False,
            details=f"Node '{self.name}' was sent a message of type '{message_type}'. Failed because no message handler was specified for this node. Implement the on_node_message_received method in this node class in order for it to receive messages.",
            response=None,
        )

    def does_name_exist(self, param_name: str) -> bool:
        for parameter in self.parameters:
            if parameter.name == param_name:
                return True
        return False

    def add_parameter(self, param: Parameter) -> None:
        """Adds a Parameter to the Node. Control and Data Parameters are all treated equally."""
        if any(char.isspace() for char in param.name):
            msg = f"Failed to add Parameter `{param.name}`. Parameter names cannot currently any whitespace characters. Please see https://github.com/griptape-ai/griptape-nodes/issues/714 to check the status on a remedy for this issue."
            raise ValueError(msg)
        if self.does_name_exist(param.name):
            msg = f"Cannot have duplicate names on parameters. Encountered two instances of '{param.name}'."
            raise ValueError(msg)
        parameter_group = (
            self.get_group_by_name_or_element_id(param.parent_element_name) if param.parent_element_name else None
        )
        if parameter_group is not None:
            parameter_group.add_child(param)
        else:
            self.add_node_element(param)
        self._emit_parameter_lifecycle_event(param)

    def remove_parameter_element_by_name(self, element_name: str) -> None:
        element = self.root_ui_element.find_element_by_name(element_name)
        if element is not None:
            self.remove_parameter_element(element)

    def remove_parameter_element(self, param: BaseNodeElement) -> None:
        # Emit event before removal if it's a Parameter
        if isinstance(param, Parameter):
            self._emit_parameter_lifecycle_event(param)
        for child in param.find_elements_by_type(BaseNodeElement):
            self.remove_node_element(child)
        self.remove_node_element(param)

    def get_group_by_name_or_element_id(self, group: str) -> ParameterGroup | None:
        group_items = self.root_ui_element.find_elements_by_type(ParameterGroup)
        for group_item in group_items:
            if group in (group_item.name, group_item.element_id):
                return group_item
        return None

    def add_node_element(self, ui_element: BaseNodeElement) -> None:
        # Set the node context before adding to ensure proper propagation
        ui_element._node_context = self
        self.root_ui_element.add_child(ui_element)

    def remove_node_element(self, ui_element: BaseNodeElement) -> None:
        self.root_ui_element.remove_child(ui_element)

    def get_current_parameter(self) -> Parameter | None:
        return self.current_spotlight_parameter

    def _set_parameter_visibility(self, names: str | list[str], *, visible: bool) -> None:
        """Sets the visibility of one or more parameters.

        Args:
            names (str or list of str): The parameter name(s) to update.
            visible (bool): Whether to show (True) or hide (False) the parameters.
        """
        if isinstance(names, str):
            names = [names]

        for name in names:
            parameter = self.get_parameter_by_name(name)
            if parameter is not None:
                parameter.ui_options = {**parameter.ui_options, "hide": not visible}

    def get_message_by_name_or_element_id(self, element: str) -> ParameterMessage | None:
        element_items = self.root_ui_element.find_elements_by_type(ParameterMessage)
        for element_item in element_items:
            if element in (element_item.name, element_item.element_id):
                return element_item
        return None

    def _set_message_visibility(self, names: str | list[str], *, visible: bool) -> None:
        """Sets the visibility of one or more messages.

        Args:
            names (str or list of str): The message name(s) to update.
            visible (bool): Whether to show (True) or hide (False) the messages.
        """
        if isinstance(names, str):
            names = [names]

        for name in names:
            message = self.get_message_by_name_or_element_id(name)
            if message is not None:
                message.ui_options = {**message.ui_options, "hide": not visible}

    def hide_message_by_name(self, names: str | list[str]) -> None:
        self._set_message_visibility(names, visible=False)

    def show_message_by_name(self, names: str | list[str]) -> None:
        self._set_message_visibility(names, visible=True)

    def hide_parameter_by_name(self, names: str | list[str]) -> None:
        """Hides one or more parameters by name."""
        self._set_parameter_visibility(names, visible=False)

    def show_parameter_by_name(self, names: str | list[str]) -> None:
        """Shows one or more parameters by name."""
        self._set_parameter_visibility(names, visible=True)

    def _update_option_choices(self, param: str, choices: list[str], default: str) -> None:
        """Updates the model selection parameter with a new set of choices.

        This method is intended to be called by subclasses to set the available
        models for the driver. It modifies the 'model' parameter's `Options` trait
        to reflect the provided choices.

        Args:
            param: The name of the parameter representing the model selection or the Parameter object itself.
            choices: A list of model names to be set as choices.
            default: The default model name to be set. It must be one of the provided choices.
        """
        parameter = self.get_parameter_by_name(param)
        if parameter is not None:
            # Find the Options trait by type since element_id is a UUID
            traits = parameter.find_elements_by_type(Options)
            if traits:
                trait = traits[0]  # Take the first Options trait
                trait.choices = choices
                # Update the manually set UI options to include the new simple_dropdown
                if hasattr(parameter, "_ui_options") and parameter._ui_options:
                    parameter._ui_options["simple_dropdown"] = choices

                if default in choices:
                    parameter.default_value = default
                    self.set_parameter_value(param, default)
                else:
                    msg = f"Default model '{default}' is not in the provided choices."
                    raise ValueError(msg)

            else:
                msg = f"No Options trait found for parameter '{param}'."
                raise ValueError(msg)
        else:
            msg = f"Parameter '{param}' not found for updating model choices."
            raise ValueError(msg)

    def _remove_options_trait(self, param: str) -> None:
        """Removes the options trait from the specified parameter.

        This method is intended to be called by subclasses to remove the
        `Options` trait from a parameter, if it exists.

        Args:
            param: The name of the parameter from which to remove the `Options` trait.
        """
        parameter = self.get_parameter_by_name(param)
        if parameter is not None:
            # Find the Options trait by type since element_id is a UUID
            traits = parameter.find_elements_by_type(Options)
            if traits:
                trait = traits[0]  # Take the first Options trait
                parameter.remove_trait(trait)
            else:
                msg = f"No Options trait found for parameter '{param}'."
                raise ValueError(msg)
        else:
            msg = f"Parameter '{param}' not found for removing options trait."
            raise ValueError(msg)

    def _replace_param_by_name(  # noqa: PLR0913
        self,
        param_name: str,
        new_param_name: str,
        new_output_type: str | None = None,
        tooltip: str | list[dict] | None = None,
        default_value: Any = None,
        ui_options: dict | None = None,
    ) -> None:
        """Replaces a parameter in the node configuration.

        This method is used to replace a parameter with a new name and
        optionally update its tooltip and default value.

        Args:
            param_name (str): The name of the parameter to replace.
            new_param_name (str): The new name for the parameter.
            new_output_type (str, optional): The new output type for the parameter.
            tooltip (str, list[dict], optional): The new tooltip for the parameter.
            default_value (Any, optional): The new default value for the parameter.
            ui_options (dict, optional): UI options for the parameter.
        """
        param = self.get_parameter_by_name(param_name)
        if param is not None:
            param.name = new_param_name
            if tooltip is not None:
                param.tooltip = tooltip
            if default_value is not None:
                param.default_value = default_value
            if new_output_type is not None:
                param.output_type = new_output_type
            if ui_options is not None:
                param.ui_options = ui_options
        else:
            msg = f"Parameter '{param_name}' not found in node configuration."
            raise ValueError(msg)

    def initialize_spotlight(self) -> None:
        # Create a linked list of parameters for spotlight navigation.
        curr_param = None
        prev_param = None
        for parameter in self.parameters:
            if (
                ParameterMode.INPUT in parameter.get_mode()
                and ParameterTypeBuiltin.CONTROL_TYPE.value not in parameter.input_types
            ):
                if not self.current_spotlight_parameter or prev_param is None:
                    # Use the original parameter and assign it to current spotlight
                    self.current_spotlight_parameter = parameter
                    prev_param = parameter
                    # go on to the next one because prev and next don't need to be set yet.
                    continue
                # prev_param will have been initialized at this point
                curr_param = parameter
                prev_param.next = curr_param
                curr_param.prev = prev_param
                prev_param = curr_param

    # Advance the current index to the next index
    def advance_parameter(self) -> bool:
        if self.current_spotlight_parameter is not None and self.current_spotlight_parameter.next is not None:
            self.current_spotlight_parameter = self.current_spotlight_parameter.next
            return True
        self.current_spotlight_parameter = None
        return False

    def get_parameter_by_element_id(self, param_element_id: str) -> Parameter | None:
        candidate = self.root_ui_element.find_element_by_id(element_id=param_element_id)
        if (candidate is not None) and (isinstance(candidate, Parameter)):
            return candidate
        return None

    def get_parameter_by_name(self, param_name: str) -> Parameter | None:
        for parameter in self.parameters:
            if param_name == parameter.name:
                return parameter
        return None

    def get_element_by_name_and_type(
        self, elem_name: str, element_type: type[BaseNodeElement] | None = None
    ) -> BaseNodeElement | None:
        find_type = element_type if element_type is not None else BaseNodeElement
        element_items = self.root_ui_element.find_elements_by_type(find_type)
        for element_item in element_items:
            if elem_name == element_item.name:
                return element_item
        return None

    def set_parameter_value(
        self,
        param_name: str,
        value: Any,
        *,
        initial_setup: bool = False,
        emit_change: bool = True,
        skip_before_value_set: bool = False,
    ) -> None:
        """Attempt to set a Parameter's value.

        The Node may choose to store a different value (or type) than what was passed in.
        Conversion callbacks on the Parameter may raise Exceptions, which will cancel
        the value assignment. Similarly, validator callbacks may reject the value and
        raise an Exception.

        Exceptions should be handled by the caller; this may result in canceling
        a running Flow or forcing an upstream object to alter its assumptions.

        Changing a Parameter may trigger other Parameters within the Node
        to be changed. If other Parameters are changed, the engine needs a list of which
        ones have changed to cascade unresolved state.

        Args:
            param_name: the name of the Parameter on this node that is about to be changed
            value: the value intended to be set
            emit_change: whether to emit a parameter lifecycle event, defaults to True
            initial_setup: Whether this value is being set as the initial setup on the node, defaults to False. When True, the value is not given to any before/after hooks.
            skip_before_value_set: Whether to skip the before_value_set hook, defaults to False. Used when before_value_set has already been called earlier in the flow.

        Returns:
            A set of parameter names within this node that were modified as a result
            of this assignment. The Parameter this was called on does NOT need to be
            part of the return.
        """
        parameter = self.get_parameter_by_name(param_name)
        if parameter is None:
            err = f"Attempted to set value for Parameter '{param_name}' but no such Parameter could be found."
            raise KeyError(err)
        # Perform any conversions to the value based on how the Parameter is configured.
        # THESE MAY RAISE EXCEPTIONS. These can cause a running Flow to be canceled, or
        # cause a calling object to alter its assumptions/behavior. The value requested
        # to be assigned will NOT be set.
        candidate_value = value
        for converter in parameter.converters:
            candidate_value = converter(candidate_value)

        # Validate the values next, based on how the Parameter is configured.
        # THESE MAY RAISE EXCEPTIONS. These can cause a running Flow to be canceled, or
        # cause a calling object to alter its assumptions/behavior. The value requested
        # to be assigned will NOT be set.
        for validator in parameter.validators:
            validator(parameter, candidate_value)

        # Allow custom node logic to prepare and possibly mutate the value before it is actually set.
        # Record any parameters modified for cascading.
        if not initial_setup:
            if skip_before_value_set:
                final_value = candidate_value
            else:
                final_value = self.before_value_set(parameter=parameter, value=candidate_value)
            # ACTUALLY SET THE NEW VALUE
            self.parameter_values[param_name] = final_value

            # If a parameter value has been set at the top level of a container, wipe all children.
            # Allow custom node logic to respond after it's been set. Record any modified parameters for cascading.
            self.after_value_set(parameter=parameter, value=final_value)
            if emit_change:
                self._emit_parameter_lifecycle_event(parameter)
        else:
            self.parameter_values[param_name] = candidate_value
        # handle with container parameters
        if parameter.parent_container_name is not None:
            # Does it have a parent container
            parent_parameter = self.get_parameter_by_name(parameter.parent_container_name)
            # Does the parent container exist
            if parent_parameter is not None:
                # Get it's new value dependent on it's children
                new_parent_value = handle_container_parameter(self, parent_parameter)
                if new_parent_value is not None:
                    # set that new value if it exists.
                    self.set_parameter_value(
                        parameter.parent_container_name,
                        new_parent_value,
                        initial_setup=initial_setup,
                        emit_change=False,
                    )

    def kill_parameter_children(self, parameter: Parameter) -> None:
        from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

        for child in parameter.find_elements_by_type(Parameter):
            GriptapeNodes.handle_request(RemoveParameterFromNodeRequest(parameter_name=child.name, node_name=self.name))

    def get_parameter_value(self, param_name: str) -> Any:
        param = self.get_parameter_by_name(param_name)
        if param and isinstance(param, ParameterContainer):
            value = handle_container_parameter(self, param)
            if value is not None:
                return value
        if param_name in self.parameter_values:
            return self.parameter_values[param_name]
        return param.default_value if param else None

    def get_parameter_list_value(self, param: str) -> list:
        """Flattens the given param from self.params into a single list.

        Args:
            param (str): Name of the param key in self.params.

        Returns:
            list: Flattened list of items from the param.
        """

        def _flatten(items: Iterable[Any]) -> Generator[Any, None, None]:
            for item in items:
                if isinstance(item, Iterable) and not isinstance(item, (str, bytes, dict)):
                    yield from _flatten(item)
                elif item:
                    yield item

        raw = self.get_parameter_value(param) or []  # ← Fallback for None
        return list(_flatten(raw))

    def remove_parameter_value(self, param_name: str) -> None:
        parameter = self.get_parameter_by_name(param_name)
        if parameter is None:
            err = f"Attempted to remove value for Parameter '{param_name}' but parameter doesn't exist."
            raise KeyError(err)
        if param_name in self.parameter_values:
            del self.parameter_values[param_name]
            # special handling if it's in a container.
            if parameter.parent_container_name and parameter.parent_container_name in self.parameter_values:
                del self.parameter_values[parameter.parent_container_name]
                new_val = self.get_parameter_value(parameter.parent_container_name)
                if new_val is not None:
                    self.set_parameter_value(parameter.parent_container_name, new_val)
        else:
            err = f"Attempted to remove value for Parameter '{param_name}' but no value was set."
            raise KeyError(err)

    def get_next_control_output(self) -> Parameter | None:
        # The default behavior for nodes is to find the first control output found.
        # Advanced nodes can override this behavior (e.g., nodes that have multiple possible
        # control paths).
        for param in self.parameters:
            if (
                ParameterTypeBuiltin.CONTROL_TYPE.value == param.output_type
                and ParameterMode.OUTPUT in param.allowed_modes
            ):
                return param
        return None

    # Must save the values of the output parameters in NodeContext.
    def process(self) -> AsyncResult | None:
        raise NotImplementedError

    async def aprocess(self) -> None:
        """Async version of process().

        Default implementation wraps the existing process() method to maintain backwards compatibility.
        Subclasses can override this method to provide direct async implementation.
        """
        result = self.process()

        if result is None:
            # Simple synchronous node - nothing to do
            return

        if isinstance(result, Generator):
            try:
                # Start the generator
                func = next(result)

                while True:
                    # Send result back and get next callable
                    func_result = await async_utils.to_thread(func)
                    func = result.send(func_result)

            except StopIteration:
                # Generator is done
                return
        else:
            # Some other return type - log warning but continue
            logger.warning("Node %s process() returned unexpected type: %s", self.name, type(result))

    # if not implemented, it will return no issues.
    def validate_before_workflow_run(self) -> list[Exception] | None:
        """Runs before the entire workflow is run."""
        return None

    def validate_before_node_run(self) -> list[Exception] | None:
        """Runs before this node is run."""
        return None

    # It could be quite common to want to validate whether or not a parameter is empty.
    # this helper function can be used within the `validate_before_workflow_run` method along with other validations
    #
    # Example:
    """
    def validate_before_workflow_run(self) -> list[Exception] | None:
        exceptions = []
        prompt_error = self.validate_empty_parameter(param="prompt", additional_msg="Please provide a prompt to generate an image.")
        if prompt_error:
            exceptions.append(prompt_error)
        return exceptions if exceptions else None
    """

    def validate_empty_parameter(self, param: str, additional_msg: str = "") -> Exception | None:
        param_value = self.parameter_values.get(param, None)
        node_name = self.name
        if not param_value or param_value.isspace():
            msg = str(f"Parameter \"{param}\" was left blank for node '{node_name}'. {additional_msg}").strip()
            return ValueError(msg)
        return None

    def get_config_value(self, service: str, value: str) -> str:
        from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

        warnings.warn(
            "get_config_value() is deprecated. Use GriptapeNodes.SecretsManager().get_secret() for secrets/API keys "
            "or GriptapeNodes.ConfigManager().get_config_value() for other config values.",
            UserWarning,
            stacklevel=2,
        )

        config_value = GriptapeNodes.ConfigManager().get_config_value(f"nodes.{service}.{value}")
        return config_value

    def set_config_value(self, service: str, value: str, new_value: str) -> None:
        from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

        warnings.warn(
            "set_config_value() is deprecated. Use GriptapeNodes.SecretsManager().set_secret() for secrets/API keys "
            "or GriptapeNodes.ConfigManager().set_config_value() for other config values.",
            UserWarning,
            stacklevel=2,
        )

        GriptapeNodes.ConfigManager().set_config_value(f"nodes.{service}.{value}", new_value)

    def clear_node(self) -> None:
        # set state to unresolved
        self.state = NodeResolutionState.UNRESOLVED
        # delete all output values potentially generated
        self.parameter_output_values.clear()
        # Clear cancellation flag
        self.clear_cancellation()
        # Clear the spotlight linked list
        # First, clear all next/prev pointers to break the linked list
        current = self.current_spotlight_parameter
        while current is not None:
            next_param = current.next
            current.next = None
            current.prev = None
            current = next_param
        # Then clear the reference to the first spotlight parameter
        self.current_spotlight_parameter = None

    def get_node_dependencies(self) -> NodeDependencies | None:
        """Return the dependencies that this node has on external resources.

        This method should be overridden by nodes that have dependencies on:
        - Referenced workflows: Other workflows that this node calls or references
        - Static files: Files that this node reads from or requires for operation
        - Python imports: Modules or classes that this node imports beyond standard dependencies

        This information can be used by the system for workflow packaging, dependency
        resolution, deployment planning, and ensuring all required resources are available.

        Returns:
            NodeDependencies object containing the node's dependencies, or None if the node
            has no external dependencies beyond the standard framework dependencies.

        Example:
            def get_node_dependencies(self) -> NodeDependencies | None:
                return NodeDependencies(
                    referenced_workflows={"image_processing_workflow", "validation_workflow"},
                    static_files={"config.json", "model_weights.pkl"},
                    imports={
                        ImportDependency("numpy"),
                        ImportDependency("sklearn.linear_model", "LinearRegression"),
                        ImportDependency("custom_module", "SpecialProcessor")
                    }
                )
        """
        return None

    def append_value_to_parameter(self, parameter_name: str, value: Any) -> None:
        from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

        # Add the value to the node
        if parameter_name in self.parameter_output_values:
            try:
                self.parameter_output_values[parameter_name] = self.parameter_output_values[parameter_name] + value
            except TypeError:
                try:
                    self.parameter_output_values[parameter_name].append(value)
                except Exception as e:
                    msg = f"Value is not appendable to parameter '{parameter_name}' on {self.name}"
                    raise RuntimeError(msg) from e
        else:
            self.parameter_output_values[parameter_name] = value
        # Publish the event up!

        GriptapeNodes.EventManager().put_event(
            ProgressEvent(value=value, node_name=self.name, parameter_name=parameter_name)
        )

    def publish_update_to_parameter(self, parameter_name: str, value: Any) -> None:
        from griptape_nodes.retained_mode.events.execution_events import ParameterValueUpdateEvent
        from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

        parameter = self.get_parameter_by_name(parameter_name)
        if parameter:
            data_type = parameter.type
            self.parameter_output_values[parameter_name] = value
            payload = ParameterValueUpdateEvent(
                node_name=self.name,
                parameter_name=parameter_name,
                data_type=data_type,
                value=TypeValidator.safe_serialize(value),
            )

            GriptapeNodes.EventManager().put_event(
                ExecutionGriptapeNodeEvent(wrapped_event=ExecutionEvent(payload=payload))
            )
        else:
            msg = f"Parameter '{parameter_name} doesn't exist on {self.name}'"
            raise RuntimeError(msg)

    def reorder_elements(self, element_order: list[str] | list[int] | list[str | int]) -> None:
        """Reorder the elements of this node.

        Args:
            element_order: A list of element names or indices in the desired order.
                         Can mix names and indices. Names take precedence over indices.

        Example:
            # Reorder by names
            node.reorder_elements(["element1", "element2", "element3"])

            # Reorder by indices
            node.reorder_elements([0, 2, 1])

            # Mix names and indices
            node.reorder_elements(["element1", 2, "element3"])
        """
        # Get current elements
        current_elements = self.root_ui_element._children

        # Create a new ordered list of elements
        ordered_elements = []
        for item in element_order:
            if isinstance(item, str):
                # Find element by name
                element = self.root_ui_element.find_element_by_name(item)
                if element is None:
                    msg = f"Element '{item}' not found"
                    raise ValueError(msg)
                ordered_elements.append(element)
            elif isinstance(item, int):
                # Get element by index
                if item < 0 or item >= len(current_elements):
                    msg = f"Element index {item} out of range"
                    raise ValueError(msg)
                ordered_elements.append(current_elements[item])
            else:
                msg = "Element order must contain strings (names) or integers (indices)"
                raise TypeError(msg)

        # Verify we have all elements
        if len(ordered_elements) != len(current_elements):
            ordered_names = {e.name for e in ordered_elements}
            current_names = {e.name for e in current_elements}
            diff = current_names - ordered_names
            msg = f"Element order must include all elements exactly once. Missing from new order: {diff}"
            raise ValueError(msg)

        # Remove all elements from root_ui_element
        for element in current_elements:
            self.root_ui_element.remove_child(element)

        # Add elements back in the new order
        for element in ordered_elements:
            self.root_ui_element.add_child(element)

    def move_element_to_position(self, element: str | int, position: str | int) -> None:
        """Move a single element to a specific position in the element list.

        Args:
            element: The element to move, specified by name or index
            position: The target position, which can be:
                     - "first" to move to the beginning
                     - "last" to move to the end
                     - An integer index (0-based) for a specific position

        Example:
            # Move element to first position by name
            node.move_element_to_position("element1", "first")

            # Move element to last position by index
            node.move_element_to_position(0, "last")

            # Move element to specific position
            node.move_element_to_position("element1", 2)
        """
        # Get list of all element names
        element_names = [child.name for child in self.root_ui_element._children]

        # Convert element index to name if needed
        element = self._get_element_name(element, element_names)

        # Create new order with moved element
        new_order = element_names.copy()
        idx = new_order.index(element)

        # Handle special position values
        if position == "first":
            target_pos = 0
        elif position == "last":
            target_pos = len(new_order) - 1
        elif isinstance(position, int):
            if position < 0 or position >= len(new_order):
                msg = f"Target position {position} out of range"
                raise ValueError(msg)
            target_pos = position
        else:
            msg = "Position must be 'first', 'last', or an integer index"
            raise TypeError(msg)

        # Remove element from current position and insert at target position
        new_order.pop(idx)
        new_order.insert(target_pos, element)

        # Use reorder_elements to apply the move
        self.reorder_elements(list(new_order))

    def _emit_parameter_lifecycle_event(self, parameter: BaseNodeElement, *, remove: bool = False) -> None:
        """Emit an AlterElementEvent for parameter add/remove operations."""
        from griptape_nodes.retained_mode.events.base_events import ExecutionEvent, ExecutionGriptapeNodeEvent
        from griptape_nodes.retained_mode.events.parameter_events import AlterElementEvent
        from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

        # Create event data using the parameter's to_event method
        if remove:
            # Import logger here to avoid circular dependency
            event = ExecutionGriptapeNodeEvent(
                wrapped_event=ExecutionEvent(payload=RemoveElementEvent(element_id=parameter.element_id))
            )
        else:
            event_data = parameter.to_event(self)
            # Publish the event
            event = ExecutionGriptapeNodeEvent(
                wrapped_event=ExecutionEvent(payload=AlterElementEvent(element_details=event_data))
            )

        GriptapeNodes.EventManager().put_event(event)

    def _get_element_name(self, element: str | int, element_names: list[str]) -> str:
        """Convert an element identifier (name or index) to its name.

        Args:
            element: Element identifier, either a name (str) or index (int)
            element_names: List of all element names

        Returns:
            The element name

        Raises:
            ValueError: If index is out of range
        """
        if isinstance(element, int):
            if element < 0 or element >= len(element_names):
                msg = f"Element index {element} out of range"
                raise ValueError(msg)
            return element_names[element]
        return element

    def swap_elements(self, elem1: str | int, elem2: str | int) -> None:
        """Swap the positions of two elements.

        Args:
            elem1: First element to swap, specified by name or index
            elem2: Second element to swap, specified by name or index

        Example:
            # Swap by names
            node.swap_elements("element1", "element2")

            # Swap by indices
            node.swap_elements(0, 2)

            # Mix names and indices
            node.swap_elements("element1", 2)
        """
        # Get list of all element names
        element_names = [child.name for child in self.root_ui_element._children]

        # Convert indices to names if needed
        elem1 = self._get_element_name(elem1, element_names)
        elem2 = self._get_element_name(elem2, element_names)

        # Create new order with swapped elements
        new_order = element_names.copy()
        idx1 = new_order.index(elem1)
        idx2 = new_order.index(elem2)
        new_order[idx1], new_order[idx2] = new_order[idx2], new_order[idx1]

        # Use reorder_elements to apply the swap
        self.reorder_elements(list(new_order))

    def move_element_up_down(self, element: str | int, *, up: bool = True) -> None:
        """Move an element up or down one position in the element list.

        Args:
            element: The element to move, specified by name or index
            up: If True, move element up one position. If False, move down one position.

        Example:
            # Move element up by name
            node.move_element_up_down("element1", up=True)

            # Move element down by index
            node.move_element_up_down(0, up=False)
        """
        # Get list of all element names
        element_names = [child.name for child in self.root_ui_element._children]

        # Convert index to name if needed
        element = self._get_element_name(element, element_names)

        # Create new order with moved element
        new_order = element_names.copy()
        idx = new_order.index(element)

        if up:
            if idx == 0:
                msg = "Element is already at the top"
                raise ValueError(msg)
            new_order[idx], new_order[idx - 1] = new_order[idx - 1], new_order[idx]
        else:
            if idx == len(new_order) - 1:
                msg = "Element is already at the bottom"
                raise ValueError(msg)
            new_order[idx], new_order[idx + 1] = new_order[idx + 1], new_order[idx]

        # Use reorder_elements to apply the move
        self.reorder_elements(list(new_order))

    def get_element_index(self, element: str | BaseNodeElement, root: BaseNodeElement | None = None) -> int:
        """Get the current index of an element in the element list.

        Args:
            element: The element to get the index for, specified by name or element object
            root: The root element to search within. If None, uses root_ui_element

        Returns:
            The current index of the element (0-based)

        Raises:
            ValueError: If element is not found

        Example:
            # Get index by name in root container
            index = node.get_element_index("element1")

            # Get index within a specific parameter group
            group = node.get_element_by_name_and_type("my_group", ParameterGroup)
            index = node.get_element_index("parameter1", root=group)

            # Get index of a parameter to position another element relative to it
            reference_index = node.get_element_index("some_parameter")
            node.move_element_to_position("new_parameter", reference_index + 1)
        """
        # Use root_ui_element if no root specified
        if root is None:
            root = self.root_ui_element

        # Get list of all element names in the root
        element_names = [child.name for child in root._children]

        # Get element name
        if isinstance(element, str):
            element_name = element
        else:
            element_name = element.name

        # Find the index of the element
        return element_names.index(element_name)


class TrackedParameterOutputValues(dict[str, Any]):
    """A dictionary that tracks modifications and emits AlterElementEvent when parameter output values change."""

    def __init__(self, node: BaseNode) -> None:
        super().__init__()
        self._node = node

    def __setitem__(self, key: str, value: Any) -> None:
        old_value = self.get(key)
        super().__setitem__(key, value)

        # Only emit event if value actually changed
        if old_value != value:
            self._emit_parameter_change_event(key, value)

    def __delitem__(self, key: str) -> None:
        if key in self:
            super().__delitem__(key)
            self._emit_parameter_change_event(key, None, deleted=True)

    def clear(self) -> None:
        if self:  # Only emit events if there were values to clear
            keys_to_clear = list(self.keys())
            super().clear()
            for key in keys_to_clear:
                # Some nodes still have values set, even if their output values are cleared
                # Here, we are emitting an event with those set values, to not misrepresent the values of the parameters in the UI.
                value = self._node.get_parameter_value(key)
                self._emit_parameter_change_event(key, value, deleted=True)

    def silent_clear(self) -> None:
        """Clear all values without emitting parameter change events."""
        super().clear()

    def update(self, *args, **kwargs) -> None:
        # Handle both dict.update(other) and dict.update(**kwargs) patterns
        if args:
            other = args[0]
            if hasattr(other, "items"):
                for key, value in other.items():
                    self[key] = value  # Use __setitem__ to trigger events
            else:
                for key, value in other:
                    self[key] = value

        for key, value in kwargs.items():
            self[key] = value

    def _emit_parameter_change_event(self, parameter_name: str, value: Any, *, deleted: bool = False) -> None:
        """Emit an AlterElementEvent for parameter output value changes."""
        parameter = self._node.get_parameter_by_name(parameter_name)
        if parameter is not None:
            from griptape_nodes.retained_mode.events.base_events import ExecutionEvent, ExecutionGriptapeNodeEvent
            from griptape_nodes.retained_mode.events.parameter_events import AlterElementEvent
            from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

            # Create event data using the parameter's to_event method
            event_data = parameter.to_event(self._node)
            event_data["value"] = value

            # Add modification metadata
            event_data["modification_type"] = "deleted" if deleted else "set"

            # Publish the event
            event = ExecutionGriptapeNodeEvent(
                wrapped_event=ExecutionEvent(payload=AlterElementEvent(element_details=event_data))
            )

            GriptapeNodes.EventManager().put_event(event)


class ControlNode(BaseNode):
    # Control Nodes may have one Control Input Port and at least one Control Output Port
    def __init__(
        self,
        name: str,
        metadata: dict[Any, Any] | None = None,
        input_control_name: str | None = None,
        output_control_name: str | None = None,
    ) -> None:
        super().__init__(name, metadata=metadata)
        self.control_parameter_in = ControlParameterInput(
            display_name=input_control_name if input_control_name is not None else "Flow In"
        )
        self.control_parameter_out = ControlParameterOutput(
            display_name=output_control_name if output_control_name is not None else "Flow Out"
        )

        self.add_parameter(self.control_parameter_in)
        self.add_parameter(self.control_parameter_out)


class DataNode(BaseNode):
    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        super().__init__(name, metadata=metadata)

        # Create control parameters like ControlNode, but initialize them as hidden
        # This allows the user to turn a DataNode "into" a Control Node; useful when
        # in situations like within a For Loop.
        self.control_parameter_in = ControlParameterInput()
        self.control_parameter_out = ControlParameterOutput()

        # Hide the control parameters by default
        self.control_parameter_in.ui_options["hide"] = True
        self.control_parameter_out.ui_options["hide"] = True

        self.add_parameter(self.control_parameter_in)
        self.add_parameter(self.control_parameter_out)


class SuccessFailureNode(BaseNode):
    """Base class for nodes that have success/failure branching with control outputs.

    This class provides:
    - Control input parameter
    - Two control outputs: success ("exec_out") and failure ("failure")
    - Execution state tracking for control flow routing
    - Helper method to check outgoing connections
    - Helper method to create standard status output parameters
    """

    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        super().__init__(name, metadata=metadata)

        # Track execution state for control flow routing
        self._execution_succeeded: bool | None = None

        # Add control input parameter
        self.control_parameter_in = ControlParameterInput()
        self.add_parameter(self.control_parameter_in)

        # Add success control output (uses default "exec_out" name)
        self.control_parameter_out = ControlParameterOutput(
            display_name="Succeeded", tooltip="Control path when the operation succeeds"
        )
        self.add_parameter(self.control_parameter_out)

        # Add failure control output
        self.failure_output = ControlParameterOutput(
            name="failure",
            display_name="Failed",
            tooltip="Control path when the operation fails",
        )
        self.add_parameter(self.failure_output)

    def get_next_control_output(self) -> Parameter | None:
        """Determine which control output to follow based on execution result."""
        if self._execution_succeeded is None:
            # Execution hasn't completed yet
            self.stop_flow = True
            return None

        if self._execution_succeeded:
            return self.control_parameter_out
        return self.failure_output

    def _has_outgoing_connections(self, parameter: Parameter) -> bool:
        """Check if a specific parameter has outgoing connections."""
        from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

        connections = GriptapeNodes.FlowManager().get_connections()

        # Check if node has any outgoing connections
        node_connections = connections.outgoing_index.get(self.name)
        if node_connections is None:
            return False

        # Check if this specific parameter has any outgoing connections
        param_connections = node_connections.get(parameter.name, [])
        return len(param_connections) > 0

    def _create_status_parameters(
        self,
        *,
        result_details_tooltip: str = "Details about the operation result",
        result_details_placeholder: str = "Details on the operation will be presented here.",
        parameter_group_initially_collapsed: bool = True,
    ) -> None:
        """Create and add standard status output parameters in a collapsible group.

        This method creates a "Status" ParameterGroup and immediately adds it to the node.
        Nodes that use this are responsible for calling this at their desired location
        in their class constructor.

        Creates and adds:
        - was_successful: Boolean parameter indicating success/failure
        - result_details: String parameter with operation details

        Args:
            result_details_tooltip: Custom tooltip for result_details parameter
            result_details_placeholder: Custom placeholder text for result_details parameter
            parameter_group_initially_collapsed: Whether the Status group should start collapsed
        """
        # Create status component with OUTPUT modes for SuccessFailureNode
        self.status_component = ExecutionStatusComponent(
            self,
            was_successful_modes={ParameterMode.OUTPUT},
            result_details_modes={ParameterMode.OUTPUT},
            parameter_group_initially_collapsed=parameter_group_initially_collapsed,
            result_details_tooltip=result_details_tooltip,
            result_details_placeholder=result_details_placeholder,
        )

    def _clear_execution_status(self) -> None:
        """Clear execution status and reset status parameters.

        This method should be called at the start of process() to reset the node state.
        """
        self._execution_succeeded = None
        self.status_component.clear_execution_status("Beginning execution...")

    def _set_status_results(self, *, was_successful: bool, result_details: str) -> None:
        """Set status results and update execution state.

        This method should be called from the process() method to communicate success or failure.
        It sets the execution state for control flow routing and updates the status output parameters.

        Args:
            was_successful: Whether the operation succeeded
            result_details: Details about the operation result
        """
        self._execution_succeeded = was_successful
        self.status_component.set_execution_result(was_successful=was_successful, result_details=result_details)

    def _handle_failure_exception(self, exception: Exception) -> None:
        """Handle failure exceptions based on whether failure output is connected.

        If the failure output has outgoing connections, logs the error and continues execution
        to allow graceful failure handling. If no connections exist, raises the exception
        to crash the flow and provide immediate feedback.

        Args:
            exception: The exception that caused the failure
        """
        if self._has_outgoing_connections(self.failure_output):
            # User has connected something to Failed output, they want to handle errors gracefully
            logger.error(
                "Error in node '%s': %s. Continuing execution since failure output is connected for graceful handling.",
                self.name,
                exception,
            )
        else:
            # No graceful handling, raise the exception to crash the flow
            raise exception

    def validate_before_workflow_run(self) -> list[Exception] | None:
        """Clear result details before workflow runs to avoid confusion from previous sessions."""
        self._set_status_results(was_successful=False, result_details="<Results will appear when the node executes>")
        return super().validate_before_workflow_run()

    def validate_before_node_run(self) -> list[Exception] | None:
        """Clear result details before node runs to avoid confusion from previous sessions."""
        self._set_status_results(was_successful=False, result_details="<Results will appear when the node executes>")
        return super().validate_before_node_run()


class StartNode(BaseNode):
    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        super().__init__(name, metadata)
        self.add_parameter(ControlParameterOutput())


class EndNode(BaseNode):
    # TODO: https://github.com/griptape-ai/griptape-nodes/issues/854
    def __init__(self, name: str, metadata: dict[Any, Any] | None = None) -> None:
        super().__init__(name, metadata)

        # Add dual control inputs
        self.succeeded_control = ControlParameterInput(
            display_name="Succeeded", tooltip="Control path when the flow completed successfully"
        )
        self.failed_control = ControlParameterInput(
            name="failed", display_name="Failed", tooltip="Control path when the flow failed"
        )

        self.add_parameter(self.succeeded_control)
        self.add_parameter(self.failed_control)

        # Create status component with INPUT and PROPERTY modes
        self.status_component = ExecutionStatusComponent(
            self,
            was_successful_modes={ParameterMode.PROPERTY},
            result_details_modes={ParameterMode.INPUT},
            parameter_group_initially_collapsed=False,
            result_details_placeholder="Details about the completion or failure will be shown here.",
        )

    def process(self) -> None:
        # Detect which control input was used to enter this node and determine success status
        match self._entry_control_parameter:
            case self.succeeded_control:
                was_successful = True
                status_prefix = "[SUCCEEDED]"
                logger.debug("End Node '%s': Matched succeeded_control path", self.name)
            case self.failed_control:
                was_successful = False
                status_prefix = "[FAILED]"
                logger.debug("End Node '%s': Matched failed_control path", self.name)
            case _:
                # No specific success/failure connection provided, assume success
                was_successful = True
                status_prefix = "[SUCCEEDED] No connection provided for success or failure, assuming successful"
                logger.debug("End Node '%s': No specific control connection, assuming success", self.name)

        # Get result details and format the final message
        result_details_value = self.get_parameter_value("result_details")
        if result_details_value and self._entry_control_parameter in (self.succeeded_control, self.failed_control):
            details = f"{status_prefix}\n{result_details_value}"
        elif self._entry_control_parameter in (self.succeeded_control, self.failed_control):
            details = f"{status_prefix}\nNo details supplied by flow"
        else:
            details = status_prefix

        self.status_component.set_execution_result(was_successful=was_successful, result_details=details)

        # Update all values to use the output value
        for param in self.parameters:
            if param.type != ParameterTypeBuiltin.CONTROL_TYPE:
                value = self.get_parameter_value(param.name)
                self.parameter_output_values[param.name] = value
        entry_parameter = self._entry_control_parameter
        # Update which control parameter to flag as the output value.
        if entry_parameter is not None:
            self.parameter_output_values[entry_parameter.name] = CONTROL_INPUT_PARAMETER


class StartLoopNode(BaseNode):
    end_node: EndLoopNode | None = None
    """Creating class for Start Loop Node in order to implement loop functionality in execution."""

    @abstractmethod
    def is_loop_finished(self) -> bool:
        """Return True if the loop has finished executing.

        This method must be implemented by subclasses to define when
        the loop should terminate.
        """


class EndLoopNode(BaseNode):
    start_node: StartLoopNode | None = None
    """Creating class for Start Loop Node in order to implement loop functionality in execution."""


class ErrorProxyNode(BaseNode):
    """A proxy node that substitutes for nodes that failed to create due to missing dependencies or errors.

    This node maintains the original node type information and allows workflows to continue loading
    even when some node types are unavailable. It generates parameters dynamically as connections
    and values are assigned to maintain workflow structure.
    """

    def __init__(
        self,
        name: str,
        original_node_type: str,
        original_library_name: str,
        failure_reason: str,
        metadata: dict[Any, Any] | None = None,
    ) -> None:
        super().__init__(name, metadata)

        self.original_node_type = original_node_type
        self.original_library_name = original_library_name
        self.failure_reason = failure_reason
        # Record ALL initial_setup=True requests in order for 1:1 replay
        self._recorded_initialization_requests: list[RequestPayload] = []

        # Track if user has made connection modifications after initial setup
        self._has_connection_modifications: bool = False

        # Add error message parameter explaining the failure
        self._error_message = ParameterMessage(
            name="error_proxy_message",
            variant="error",
            value="",  # Will be set by _update_error_message
        )
        self.add_node_element(self._error_message)
        self._update_error_message()

    def _get_base_error_message(self) -> str:
        """Generate the base error message for this ErrorProxyNode."""
        return (
            f"This is a placeholder for a node of type '{self.original_node_type}'"
            f"\nfrom the '{self.original_library_name}' library."
            f"\nIt encountered a problem when loading."
            f"\nThe technical issue:\n{self.failure_reason}\n\n"
            f"Your original node will be restored once the issue above is fixed "
            f"(which may require registering the appropriate library, or getting "
            f"a code fix from the node author)."
        )

    def on_attempt_set_parameter_value(self, param_name: str) -> None:
        """Public method to attempt setting a parameter value during initial setup.

        Creates a PROPERTY mode parameter if it doesn't exist to support value setting.

        Args:
            param_name: Name of the parameter to prepare for value setting
        """
        self._ensure_parameter_exists(param_name)

    def _ensure_parameter_exists(self, param_name: str) -> None:
        """Ensures a parameter exists on this node.

        Creates a universal parameter with all modes enabled for maximum flexibility.
        Auto-generated parameters are marked as non-user-defined so they don't get serialized.

        Args:
            param_name: Name of the parameter to ensure exists
        """
        existing_param = super().get_parameter_by_name(param_name)

        if existing_param is None:
            # Create new universal parameter with all modes enabled
            from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

            request = AddParameterToNodeRequest(
                node_name=self.name,
                parameter_name=param_name,
                type=ParameterTypeBuiltin.ANY.value,  # ANY = parameter's main type for maximum flexibility
                input_types=[ParameterTypeBuiltin.ANY.value],  # ANY = accepts any single input type
                output_type=ParameterTypeBuiltin.ALL.value,  # ALL = can output any type (passthrough)
                tooltip="Parameter created for placeholder node to preserve workflow connections",
                mode_allowed_input=True,  # Enable all modes upfront
                mode_allowed_output=True,
                mode_allowed_property=True,
                is_user_defined=False,  # Don't serialize this parameter
                initial_setup=True,  # Allows setting non-settable parameters and prevents resolution cascades during workflow loading
            )
            result = GriptapeNodes.handle_request(request)

            # Check if parameter creation was successful
            from griptape_nodes.retained_mode.events.parameter_events import AddParameterToNodeResultSuccess

            if not isinstance(result, AddParameterToNodeResultSuccess):
                failure_message = f"Failed to create parameter '{param_name}': {result.result_details}"
                raise RuntimeError(failure_message)
        # If parameter already exists, nothing to do - it already has all modes

    def allow_incoming_connection(
        self,
        source_node: BaseNode,  # noqa: ARG002
        source_parameter: Parameter,  # noqa: ARG002
        target_parameter: Parameter,  # noqa: ARG002
    ) -> bool:
        """ErrorProxyNode allows connections - it's a shell for maintaining connections."""
        return True

    def allow_outgoing_connection(
        self,
        source_parameter: Parameter,  # noqa: ARG002
        target_node: BaseNode,  # noqa: ARG002
        target_parameter: Parameter,  # noqa: ARG002
    ) -> bool:
        """ErrorProxyNode allows connections - it's a shell for maintaining connections."""
        return True

    def before_incoming_connection(
        self,
        source_node: BaseNode,  # noqa: ARG002
        source_parameter_name: str,  # noqa: ARG002
        target_parameter_name: str,
    ) -> None:
        """Create target parameter before connection validation."""
        self._ensure_parameter_exists(target_parameter_name)

    def before_outgoing_connection(
        self,
        source_parameter_name: str,
        target_node: BaseNode,  # noqa: ARG002
        target_parameter_name: str,  # noqa: ARG002
    ) -> None:
        """Create source parameter before connection validation."""
        self._ensure_parameter_exists(source_parameter_name)

    def set_post_init_connections_modified(self) -> None:
        """Mark that user-initiated connections have been modified and update the warning message."""
        if not self._has_connection_modifications:
            self._has_connection_modifications = True
            self._update_error_message()

    def _update_error_message(self) -> None:
        """Update the ParameterMessage to include connection modification warning."""
        # Build the updated message with connection warning
        base_message = self._get_base_error_message()

        # Add connection modification warning if applicable
        if self._has_connection_modifications:
            connection_warning = (
                "\n\nWARNING: You have modified connections to this placeholder node."
                "\nThis may require manual fixes when the original node is restored."
            )
            final_message = base_message + connection_warning
        else:
            # Add the general note only if no modifications have been made
            general_warning = (
                "\n\nNote: Making changes to this node may require manual fixes when restored,"
                "\nas we can't predict how all node authors craft their custom nodes."
            )
            final_message = base_message + general_warning

        # Update the error message value
        self._error_message.value = final_message

    def validate_before_node_run(self) -> list[Exception] | None:
        """Prevent ErrorProxy nodes from running - validate at node level only."""
        error_msg = (
            f"Cannot run node '{self.name}': This is a placeholder node put in place to preserve your workflow until the breaking issue is fixed.\n\n"
            f"The original '{self.original_node_type}' from library '{self.original_library_name}' failed to load due to this technical issue:\n\n"
            f"{self.failure_reason}\n\n"
            f"Once you resolve the issue above, reload this workflow and the placeholder will be automatically replaced with the original node."
        )
        return [RuntimeError(error_msg)]

    def record_initialization_request(self, request: RequestPayload) -> None:
        """Record an initialization request for replay during serialization.

        This method captures requests that modify ErrorProxyNode structure during workflow loading,
        preserving information needed for restoration when the original node becomes available.

        WHAT WE RECORD:
        - AlterParameterDetailsRequest: Parameter modifications from original node definition
        - Any request with initial_setup=True that changes node structure in ways that cannot
          be reconstructed from final state alone

        WHAT WE DO NOT RECORD (and why):
        - SetParameterValueRequest: Final parameter values are serialized normally via parameter_values
        - AddParameterToNodeRequest: User-defined parameters are serialized via is_user_defined=True flag
        - CreateConnectionRequest: Connections are serialized separately and recreated during loading
        - RenameParameterRequest: Final parameter names are preserved in serialized state
        - SetNodeMetadataRequest: Final metadata state is preserved in node.metadata
        - SetLockNodeStateRequest: Final lock state is preserved in node.lock
        """
        self._recorded_initialization_requests.append(request)

    def get_recorded_initialization_requests(self, request_type: type | None = None) -> list[RequestPayload]:
        """Get recorded initialization requests for 1:1 serialization replay.

        Args:
            request_type: Optional class to filter by. If provided, only returns requests
                         of that type. If None, returns all recorded requests.

        Returns:
            List of recorded requests in the order they were received.
        """
        if request_type is None:
            return self._recorded_initialization_requests

        return [req for req in self._recorded_initialization_requests if isinstance(req, request_type)]

    def process(self) -> Any:
        """No-op process method. Error Proxy nodes do nothing during execution."""
        return None


@dataclass
class NodeGroup:
    """Represents a group of nodes that should be executed together in parallel.

    Nodes in a group are identified by having the same non-empty value in their
    node_group parameter. During DAG resolution, grouped nodes are replaced with
    a single NodeGroupProxyNode that represents them in the execution graph.

    Attributes:
        group_id: Unique identifier for this group (value from node_group parameter)
        nodes: Set of BaseNode instances that belong to this group
        internal_connections: Connections between nodes within the group
        external_incoming_connections: Connections from outside nodes into the group
        external_outgoing_connections: Connections from group nodes to outside nodes
    """

    group_id: str
    nodes: dict[str, BaseNode] = field(default_factory=dict)
    internal_connections: list[Connection] = field(default_factory=list)
    external_incoming_connections: list[Connection] = field(default_factory=list)
    external_outgoing_connections: list[Connection] = field(default_factory=list)
    # Store original node references before remapping to proxy (for cleanup)
    original_incoming_targets: dict[int, BaseNode] = field(default_factory=dict)  # conn_id -> original target
    original_outgoing_sources: dict[int, BaseNode] = field(default_factory=dict)  # conn_id -> original source

    def add_node(self, node: BaseNode) -> None:
        """Add a node to this group."""
        self.nodes[node.name] = node

    def validate_no_intermediate_nodes(self, all_connections: dict[int, Connection]) -> None:
        """Validate that no ungrouped nodes exist between grouped nodes.

        This method checks the dependency graph to ensure that all nodes that lie
        on paths between grouped nodes are also part of the group. If ungrouped
        nodes are found between grouped nodes, this indicates a logical error in
        the group definition.

        Args:
            all_connections: Dictionary mapping connection IDs to Connection objects

        Raises:
            ValueError: If ungrouped nodes are found between grouped nodes
        """
        from griptape_nodes.exe_types.connections import Connections

        # Build a Connections object for traversal
        connections = Connections()
        connections.connections = all_connections

        # Rebuild indices for efficient lookup
        for conn_id, conn in all_connections.items():
            connections.outgoing_index.setdefault(conn.source_node.name, {}).setdefault(
                conn.source_parameter.name, []
            ).append(conn_id)
            connections.incoming_index.setdefault(conn.target_node.name, {}).setdefault(
                conn.target_parameter.name, []
            ).append(conn_id)

        # Check each pair of nodes in the group
        for node_a in self.nodes.values():
            for node_b in self.nodes.values():
                if node_a == node_b:
                    continue

                # Check if there's a path from node_a to node_b
                intermediate_nodes = self._find_intermediate_nodes(node_a, node_b, connections)

                # Check if any intermediate nodes are not in the group
                ungrouped_intermediates = [n for n in intermediate_nodes if n not in self.nodes]

                if ungrouped_intermediates:
                    ungrouped_names = [n.name for n in ungrouped_intermediates]
                    msg = (
                        f"Invalid node group '{self.group_id}': Found ungrouped nodes between grouped nodes. "
                        f"Ungrouped nodes {ungrouped_names} exist on the path from '{node_a.name}' to '{node_b.name}'. "
                        f"All nodes on paths between grouped nodes must be part of the same group."
                    )
                    raise ValueError(msg)

    def _find_intermediate_nodes(  # noqa: C901
        self, start_node: BaseNode, end_node: BaseNode, connections: Connections
    ) -> set[BaseNode]:
        """Find all nodes on paths between start_node and end_node (excluding endpoints).

        Uses BFS to explore all paths from start_node to end_node and collects
        all nodes encountered (except start and end nodes themselves).

        Args:
            start_node: Starting node for path search
            end_node: Target node for path search
            connections: Connections object for graph traversal

        Returns:
            Set of nodes found on paths between start and end (excluding endpoints)
        """
        if start_node.name not in connections.outgoing_index:
            return set()

        visited = set()
        intermediate = set()
        queue = [(start_node, [start_node])]

        while queue:
            current_node, path = queue.pop(0)

            if current_node.name in visited:
                continue
            visited.add(current_node.name)

            # Process outgoing connections from current node
            if current_node.name not in connections.outgoing_index:
                continue

            for conn_ids in connections.outgoing_index[current_node.name].values():
                for conn_id in conn_ids:
                    if conn_id not in connections.connections:
                        continue

                    conn = connections.connections[conn_id]
                    next_node = conn.target_node

                    # If we reached the end node, record intermediate nodes
                    if next_node == end_node:
                        for node in path[1:]:
                            intermediate.add(node)
                        continue

                    # Continue exploring if not already visited
                    if next_node.name not in visited:
                        queue.append((next_node, [*path, next_node]))

        return intermediate


class NodeGroupProxyNode(BaseNode):
    """Proxy node that represents a group of nodes during DAG execution.

    This node acts as a single execution unit for a group of nodes that should
    be executed in parallel. When the DAG executor encounters this proxy node,
    it passes the entire NodeGroup to the NodeExecutor which handles parallel
    execution of all grouped nodes.

    The proxy node has parameters that mirror the external connections to/from
    the group, allowing it to seamlessly integrate into the DAG structure.

    Attributes:
        node_group: The NodeGroup instance this proxy represents
    """

    def __init__(
        self,
        name: str,
        node_group: NodeGroup,
        metadata: dict[Any, Any] | None = None,
    ) -> None:
        super().__init__(name, metadata)
        self.node_group_data = node_group

        # Track mapping from proxy parameter name to (original_node, original_param_name)
        self._proxy_param_to_node_param: dict[str, tuple[BaseNode, str]] = {}
        execution_type = set()
        for node in node_group.nodes.values():
            execution_type.add(node.get_parameter_value(node.execution_environment.name))
        # TODO: Set this by group in the UI, not set on the node itself. https://github.com/griptape-ai/griptape-vsl-gui/issues/1429
        if len(execution_type) > 1:
            # Hoping this check can be removed by UI updates.
            # For now, we are setting execution type individually on a parameters in all three of the nodes. we want their execution types to all be matching, or we fail.
            msg = f"Node group '{node_group.group_id}' has nodes with multiple execution types: {execution_type}"
            raise ValueError(msg)
        self.set_parameter_value(self.execution_environment.name, execution_type.pop())
        # Note: Proxy parameters are created AFTER connection remapping in control_flow.py
        # via explicit call to create_proxy_parameters()

    def create_proxy_parameters(self) -> None:
        """Create parameters on the proxy that match external connections.

        For each external incoming connection, create an input parameter with name
        format: {sanitized_node_name}__{param_name}. This allows the proxy to
        forward parameter values to the correct original node.

        For each external outgoing connection, create an output parameter.
        This allows the proxy to integrate seamlessly into the DAG.
        """
        # Track created parameters to avoid duplicates
        created_params = set()

        # Create input parameters for external incoming connections
        for conn in self.node_group_data.external_incoming_connections:
            conn_id = id(conn)
            # Get the original target node from saved mapping (before it was remapped to proxy)
            target_node = self.node_group_data.original_incoming_targets.get(conn_id)
            if target_node is None:
                # Fallback if not found (shouldn't happen)
                msg = f"Failed to find target node for incoming connection with ID: {conn_id}"
                raise ValueError(msg)
            target_param = conn.target_parameter

            # Create proxy parameter name: {sanitized_node_name}__{param_name}
            sanitized_node_name = target_node.name.replace(" ", "_")
            proxy_param_name = f"{sanitized_node_name}__{target_param.name}"

            if proxy_param_name not in created_params:
                proxy_param = Parameter(
                    name=proxy_param_name,
                    type=target_param.type,
                    input_types=target_param.input_types,
                    output_type=target_param.output_type,
                    tooltip=f"Proxy input for {target_node.name}.{target_param.name}",
                    allowed_modes={ParameterMode.INPUT},
                )
                self.add_parameter(proxy_param)
                created_params.add(proxy_param_name)

                # Track mapping from proxy param to original node/param
                self._proxy_param_to_node_param[proxy_param_name] = (target_node, target_param.name)

        # Create output parameters for external outgoing connections
        for conn in self.node_group_data.external_outgoing_connections:
            conn_id = id(conn)
            # Get the original source node from saved mapping (before it was remapped to proxy)
            source_node = self.node_group_data.original_outgoing_sources.get(conn_id)
            if source_node is None:
                # Fallback if not found (shouldn't happen)
                continue

            source_param = conn.source_parameter

            # Create proxy parameter name: {sanitized_node_name}__{param_name}
            sanitized_node_name = source_node.name.replace(" ", "_")
            proxy_param_name = f"{sanitized_node_name}__{source_param.name}"

            if proxy_param_name not in created_params:
                proxy_param = Parameter(
                    name=proxy_param_name,
                    type=source_param.type,
                    input_types=source_param.input_types,
                    output_type=source_param.output_type,
                    tooltip=f"Proxy output for {source_node.name}.{source_param.name}",
                    allowed_modes={ParameterMode.OUTPUT},
                )
                self.add_parameter(proxy_param)
                created_params.add(proxy_param_name)

                # Track mapping from proxy param to original node/param
                self._proxy_param_to_node_param[proxy_param_name] = (source_node, source_param.name)

    async def aprocess(self) -> None:
        """Execute all nodes in the group in parallel.

        This method is called by the DAG executor. It executes all nodes in the
        group concurrently using asyncio.gather and handles propagating input
        values from the proxy to the grouped nodes.
        """
        msg = "NodeGroupProxyNode should not be executed locally."
        raise NotImplementedError(msg)

    def process(self) -> Any:
        """Synchronous process method - not used for proxy nodes."""
        msg = "NodeGroupProxyNode should use aprocess() for async execution."
        raise NotImplementedError(msg)


class Connection:
    source_node: BaseNode
    target_node: BaseNode
    source_parameter: Parameter
    target_parameter: Parameter

    def __init__(
        self,
        source_node: BaseNode,
        source_parameter: Parameter,
        target_node: BaseNode,
        target_parameter: Parameter,
    ) -> None:
        self.source_node = source_node
        self.target_node = target_node
        self.source_parameter = source_parameter
        self.target_parameter = target_parameter

    def get_target_node(self) -> BaseNode:
        return self.target_node

    def get_source_node(self) -> BaseNode:
        return self.source_node


def handle_container_parameter(current_node: BaseNode, parameter: Parameter) -> Any:
    """Process container parameters and build appropriate data structures.

    This function handles ParameterContainer objects by collecting values from their child
    parameters and constructing either a list or dictionary based on the container type.

    Args:
        current_node: The node containing parameter values
        parameter: The parameter to process, which may be a container

    Returns:
        A list of parameter values if parameter is a ParameterContainer,
        or None if the parameter is not a container
    """
    # if it's a container and it's value isn't already set.
    if isinstance(parameter, ParameterContainer):
        children = parameter.find_elements_by_type(Parameter, find_recursively=False)
        if isinstance(parameter, ParameterList):
            build_parameter_value = []
        elif isinstance(parameter, ParameterDictionary):
            build_parameter_value = {}
        build_parameter_value = []
        for child in children:
            value = current_node.get_parameter_value(child.name)
            if value is not None:
                build_parameter_value.append(value)
        return build_parameter_value
    return None
