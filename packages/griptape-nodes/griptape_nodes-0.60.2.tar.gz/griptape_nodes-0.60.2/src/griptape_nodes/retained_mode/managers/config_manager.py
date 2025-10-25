import copy
import json
import logging
import os
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError
from xdg_base_dirs import xdg_config_home

from griptape_nodes.node_library.library_registry import LibraryRegistry
from griptape_nodes.retained_mode.events.base_events import ResultPayload
from griptape_nodes.retained_mode.events.config_events import (
    GetConfigCategoryRequest,
    GetConfigCategoryResultFailure,
    GetConfigCategoryResultSuccess,
    GetConfigPathRequest,
    GetConfigPathResultSuccess,
    GetConfigSchemaRequest,
    GetConfigSchemaResultFailure,
    GetConfigSchemaResultSuccess,
    GetConfigValueRequest,
    GetConfigValueResultFailure,
    GetConfigValueResultSuccess,
    ResetConfigRequest,
    ResetConfigResultFailure,
    ResetConfigResultSuccess,
    SetConfigCategoryRequest,
    SetConfigCategoryResultFailure,
    SetConfigCategoryResultSuccess,
    SetConfigValueRequest,
    SetConfigValueResultFailure,
    SetConfigValueResultSuccess,
)
from griptape_nodes.retained_mode.managers.event_manager import EventManager
from griptape_nodes.retained_mode.managers.settings import Settings
from griptape_nodes.utils.dict_utils import get_dot_value, merge_dicts, set_dot_value

logger = logging.getLogger("griptape_nodes")

USER_CONFIG_PATH = xdg_config_home() / "griptape_nodes" / "griptape_nodes_config.json"


class ConfigManager:
    """A class to manage application configuration and file pathing.

    This class handles loading and saving configuration from multiple sources with the following precedence:
    1. Default configuration from Settings model (lowest priority)
    2. User global configuration from ~/.config/griptape_nodes/griptape_nodes_config.json
    3. Workspace-specific configuration from <workspace>/griptape_nodes_config.json
    4. Environment variables with GTN_CONFIG_ prefix (highest priority)

    Environment variables starting with GTN_CONFIG_ are converted to config keys by removing the prefix
    and converting to lowercase (e.g., GTN_CONFIG_FOO=bar becomes {"foo": "bar"}).

    Supports categorized configuration using dot notation (e.g., 'category.subcategory.key')
    to organize related configuration items.

    Attributes:
        default_config (dict): The default configuration loaded from the Settings model.
        user_config (dict): The user configuration loaded from the config file.
        workspace_config (dict): The workspace configuration loaded from the workspace config file.
        env_config (dict): The configuration loaded from GTN_CONFIG_ environment variables.
        merged_config (dict): The merged configuration, combining all sources in precedence order.
    """

    def __init__(self, event_manager: EventManager | None = None) -> None:
        """Initialize the ConfigManager.

        Args:
            event_manager: The EventManager instance to use for event handling.
        """
        self.load_configs()

        self._set_log_level(self.merged_config.get("log_level", logging.INFO))

        if event_manager is not None:
            # Register all our listeners.
            event_manager.assign_manager_to_request_type(
                GetConfigCategoryRequest, self.on_handle_get_config_category_request
            )
            event_manager.assign_manager_to_request_type(
                SetConfigCategoryRequest, self.on_handle_set_config_category_request
            )
            event_manager.assign_manager_to_request_type(GetConfigValueRequest, self.on_handle_get_config_value_request)
            event_manager.assign_manager_to_request_type(SetConfigValueRequest, self.on_handle_set_config_value_request)
            event_manager.assign_manager_to_request_type(GetConfigPathRequest, self.on_handle_get_config_path_request)
            event_manager.assign_manager_to_request_type(
                GetConfigSchemaRequest, self.on_handle_get_config_schema_request
            )
            event_manager.assign_manager_to_request_type(ResetConfigRequest, self.on_handle_reset_config_request)

    @property
    def workspace_path(self) -> Path:
        """Get the base file path from the configuration.

        Returns:
            Path object representing the base file path.
        """
        return Path(self._workspace_path).resolve()

    @workspace_path.setter
    def workspace_path(self, path: str | Path) -> None:
        """Set the base file path in the configuration.

        Args:
            path: The path to set as the base file path.
        """
        self._workspace_path = str(Path(path).resolve())

    @property
    def workspace_config_path(self) -> Path:
        """Get the path to the workspace config file.

        Returns:
            Path object representing the user config file.
        """
        return self.workspace_path / "griptape_nodes_config.json"

    @property
    def config_files(self) -> list[Path]:
        """Get a list of config files in ascending order of priority.

        The last file shown has the highest priority and overrides
        any settings found in earlier files.

        Returns:
            List of Path objects representing the config files.
        """
        possible_config_files = [
            USER_CONFIG_PATH,
            self.workspace_config_path,
        ]

        return [config_file for config_file in possible_config_files if config_file.exists()]

    def _load_config_from_env_vars(self) -> dict[str, Any]:
        """Load configuration values from GTN_CONFIG_ environment variables.

        Environment variables starting with GTN_CONFIG_ are converted to config keys.
        GTN_CONFIG_FOO=bar becomes {"foo": "bar"}
        GTN_CONFIG_STORAGE_BACKEND=gtc becomes {"storage_backend": "gtc"}

        Returns:
            Dictionary containing config values from environment variables
        """
        env_config = {}
        for key, value in os.environ.items():
            if key.startswith("GTN_CONFIG_"):
                # Remove GTN_CONFIG_ prefix and convert to lowercase
                config_key = key[11:].lower()  # len("GTN_CONFIG_") = 11
                env_config[config_key] = value
                logger.debug("Loaded config from env var: %s -> %s", key, config_key)

        return env_config

    def load_configs(self) -> None:
        """Load configs from the user config file and the workspace config file.

        Sets the default_config, user_config, workspace_config, and merged_config attributes.
        """
        # We need to load the user config file first so we can get the workspace directory which may contain a workspace config file.
        # Load the user config file to get the workspace directory.
        self.default_config = Settings().model_dump()
        merged_config = self.default_config
        if USER_CONFIG_PATH.exists():
            try:
                self.user_config = json.loads(USER_CONFIG_PATH.read_text())
                merged_config = merge_dicts(self.default_config, self.user_config)
            except json.JSONDecodeError as e:
                logger.error("Error parsing user config file: %s", e)
                self.user_config = {}
        else:
            self.user_config = {}
            logger.debug("User config file not found")

        # Merge in any settings from the workspace directory.
        self.workspace_path = merged_config["workspace_directory"]
        if self.workspace_config_path.exists():
            try:
                self.workspace_config = json.loads(self.workspace_config_path.read_text())
                merged_config = merge_dicts(merged_config, self.workspace_config)
            except json.JSONDecodeError as e:
                logger.error("Error parsing workspace config file: %s", e)
                self.workspace_config = {}
        else:
            self.workspace_config = {}
            logger.debug("Workspace config file not found")

        # Merge in configuration from GTN_CONFIG_ environment variables (highest priority)
        self.env_config = self._load_config_from_env_vars()
        if self.env_config:
            merged_config = merge_dicts(merged_config, self.env_config)
            logger.debug("Merged config from environment variables: %s", list(self.env_config.keys()))

        # Re-assign workspace path in case env var overrides it
        self.workspace_path = merged_config["workspace_directory"]

        # Validate the full config against the Settings model.
        try:
            Settings.model_validate(merged_config)
            self.merged_config = merged_config
        except ValidationError as e:
            logger.error("Error validating config file: %s", e)
            self.merged_config = self.default_config

    def reset_user_config(self) -> None:
        """Reset the user configuration to the default values.

        An exception is made for `workflows_to_register` since resetting it gives the appearance of the user losing their workflows.
        """
        # TODO: https://github.com/griptape-ai/griptape-nodes/issues/1241 need a better way to annotate fields to ignore.
        workflows_to_register = self.get_config_value("app_events.on_app_initialization_complete.workflows_to_register")
        USER_CONFIG_PATH.write_text(
            json.dumps(
                {
                    "app_events": {
                        "on_app_initialization_complete": {
                            "workflows_to_register": workflows_to_register,
                        }
                    }
                },
                indent=2,
            )
        )
        self.load_configs()

    def save_user_workflow_json(self, workflow_file_name: str) -> None:
        config_loc = "app_events.on_app_initialization_complete.workflows_to_register"
        existing_workflows = self.get_config_value(config_loc)
        if not existing_workflows:
            existing_workflows = []
        existing_workflows.append(workflow_file_name) if workflow_file_name not in existing_workflows else None
        self.set_config_value(config_loc, existing_workflows)

    def delete_user_workflow(self, workflow_file_name: str) -> None:
        default_workflows = self.get_config_value("app_events.on_app_initialization_complete.workflows_to_register")
        if default_workflows:
            default_workflows = [
                saved_workflow
                for saved_workflow in default_workflows
                if (saved_workflow.lower() != workflow_file_name.lower())
            ]
            self.set_config_value("app_events.on_app_initialization_complete.workflows_to_register", default_workflows)

    def get_full_path(self, relative_path: str) -> Path:
        """Get a full path by combining the base path with a relative path.

        Args:
            relative_path: A path relative to the base path.

        Returns:
            Path object representing the full path.
        """
        workspace_path = self.workspace_path
        return workspace_path / relative_path

    def get_config_value(
        self,
        key: str,
        *,
        should_load_env_var_if_detected: bool = True,
        config_source: Literal["user_config", "workspace_config", "default_config", "merged_config"] = "merged_config",
        default: Any | None = None,
    ) -> Any:
        """Get a value from the configuration.

        If `should_load_env_var_if_detected` is True (default), and the value starts with a $, it will be pulled from the environment variables.

        Args:
            key: The configuration key to get. Can use dot notation for nested keys (e.g., 'category.subcategory.key').
                 If the key refers to a category (dictionary), returns the entire category.
            should_load_env_var_if_detected: If True, and the value starts with a $, it will be pulled from the environment variables.
            config_source: The source of the configuration to use. Can be 'user_config', 'workspace_config', 'default_config', or 'merged_config'.
            default: The default value to return if the key is not found in the configuration.

        Returns:
            The value associated with the key, or the entire category if key points to a dict.
        """
        config_source_map = {
            "user_config": self.user_config,
            "workspace_config": self.workspace_config,
            "merged_config": self.merged_config,
            "default_config": self.default_config,
        }
        config = config_source_map.get(config_source, self.merged_config)
        value = get_dot_value(config, key, default)

        if value is None:
            msg = f"Config key '{key}' not found in config file."
            logger.warning(msg)
            return None

        if should_load_env_var_if_detected and isinstance(value, str) and value.startswith("$"):
            from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

            value = GriptapeNodes.SecretsManager().get_secret(value[1:])

        return value

    def set_config_value(self, key: str, value: Any, *, should_set_env_var_if_detected: bool = True) -> None:
        """Set a value in the configuration.

        Args:
            key: The configuration key to set. Can use dot notation for nested keys (e.g., 'category.subcategory.key').
            value: The value to associate with the key.
            should_set_env_var_if_detected: If True, and the value starts with a $, it will be set in the environment variables.
        """
        delta = set_dot_value({}, key, value)
        if key == "log_level":
            self._set_log_level(value)
        elif key == "workspace_directory":
            self.workspace_path = value
        self.user_config = merge_dicts(self.merged_config, delta)
        self._write_user_config_delta(delta)

        if should_set_env_var_if_detected and isinstance(value, str) and value.startswith("$"):
            from griptape_nodes.retained_mode.griptape_nodes import GriptapeNodes

            value = GriptapeNodes.SecretsManager().set_secret(value[1:], "")

        # We need to fully reload the user config because we need to regenerate the merged config.
        # Also eventually need to reload registered workflows.
        # TODO: https://github.com/griptape-ai/griptape-nodes/issues/437
        self.load_configs()
        logger.debug("Config value '%s' set to '%s'", key, value)

    def on_handle_get_config_category_request(self, request: GetConfigCategoryRequest) -> ResultPayload:
        if request.category is None or request.category == "":
            # Return the whole shebang. Start with the defaults and then layer on the user config.
            contents = self.merged_config
            result_details = "Successfully returned the entire config dictionary."
            return GetConfigCategoryResultSuccess(contents=contents, result_details=result_details)

        # See if we got something valid.
        find_results = self.get_config_value(request.category)
        if find_results is None:
            result_details = f"Attempted to get config details for category '{request.category}'. Failed because no such category could be found."
            return GetConfigCategoryResultFailure(result_details=result_details)

        if not isinstance(find_results, dict):
            result_details = f"Attempted to get config details for category '{request.category}'. Failed because this was was not a dictionary."
            return GetConfigCategoryResultFailure(result_details=result_details)

        result_details = f"Successfully returned the config dictionary for section '{request.category}'."
        return GetConfigCategoryResultSuccess(contents=find_results, result_details=result_details)

    def on_handle_set_config_category_request(self, request: SetConfigCategoryRequest) -> ResultPayload:
        # Validate the value is a dict
        if not isinstance(request.contents, dict):
            result_details = f"Attempted to set config details for category '{request.category}'. Failed because the contents provided were not a dictionary."
            return SetConfigCategoryResultFailure(result_details=result_details)

        if request.category is None or request.category == "":
            # Assign the whole shebang.
            self._write_user_config_delta(request.contents)
            result_details = "Successfully assigned the entire config dictionary."
            return SetConfigCategoryResultSuccess(result_details=result_details)

        self.set_config_value(key=request.category, value=request.contents)

        result_details = f"Successfully assigned the config dictionary for section '{request.category}'."
        return SetConfigCategoryResultSuccess(result_details=result_details)

    def on_handle_get_config_value_request(self, request: GetConfigValueRequest) -> ResultPayload:
        if request.category_and_key == "":
            result_details = "Attempted to get config value but no category or key was specified."
            return GetConfigValueResultFailure(result_details=result_details)

        # See if we got something valid.
        find_results = self.get_config_value(request.category_and_key)
        if find_results is None:
            result_details = f"Attempted to get config value for category.key '{request.category_and_key}'. Failed because no such category.key could be found."
            return GetConfigValueResultFailure(result_details=result_details)

        result_details = f"Successfully returned the config value for section '{request.category_and_key}'."
        return GetConfigValueResultSuccess(value=find_results, result_details=result_details)

    def on_handle_get_config_path_request(self, request: GetConfigPathRequest) -> ResultPayload:  # noqa: ARG002
        result_details = "Successfully returned the config path."
        return GetConfigPathResultSuccess(config_path=str(USER_CONFIG_PATH), result_details=result_details)

    def on_handle_get_config_schema_request(self, request: GetConfigSchemaRequest) -> ResultPayload:  # noqa: ARG002
        """Handle request to get the configuration schema with current values and library settings.

        This method returns a clean structure with three main components:
        1. base_schema: Core settings schema from Pydantic Settings model with categories
        2. library_schemas: Library-specific schemas from definition files (preserves enums)
        3. current_values: All current configuration values from merged config

        The approach separates concerns for frontend flexibility and simplicity.
        Library settings with explicit schemas (including enums) are preserved, while
        libraries without schemas get simple object types.
        """
        try:
            # Get base settings schema and current values
            base_schema = Settings.model_json_schema()
            current_values = self.merged_config.copy()

            # Get library schemas
            library_schemas = LibraryRegistry.get_all_library_schemas()

            # Return clean structure
            schema_with_defaults = {
                "base_schema": base_schema,
                "library_schemas": library_schemas,
                "current_values": current_values,
            }

            result_details = "Successfully returned the configuration schema with default values and library settings."
            return GetConfigSchemaResultSuccess(schema=schema_with_defaults, result_details=result_details)
        except Exception as e:
            result_details = f"Failed to generate configuration schema: {e}"
            return GetConfigSchemaResultFailure(result_details=result_details)

    def on_handle_reset_config_request(self, request: ResetConfigRequest) -> ResultPayload:  # noqa: ARG002
        try:
            self.reset_user_config()
            self._set_log_level(str(self.merged_config["log_level"]))
            self.workspace_path = Path(self.merged_config["workspace_directory"])

            result_details = "Successfully reset user configuration."
            return ResetConfigResultSuccess(result_details=result_details)
        except Exception as e:
            result_details = f"Attempted to reset user configuration but failed: {e}."
            return ResetConfigResultFailure(result_details=result_details)

    def _get_diff(self, old_value: Any, new_value: Any) -> dict[Any, Any]:
        """Generate a diff between the old and new values."""
        if isinstance(old_value, dict) and isinstance(new_value, dict):
            diff = {
                key: (old_value.get(key), new_value.get(key))
                for key in new_value
                if old_value.get(key) != new_value.get(key)
            }
        elif isinstance(old_value, list) and isinstance(new_value, list):
            diff = {
                str(i): (old, new) for i, (old, new) in enumerate(zip(old_value, new_value, strict=False)) if old != new
            }

            # Handle added or removed elements
            if len(old_value) > len(new_value):
                for i in range(len(new_value), len(old_value)):
                    diff[str(i)] = (old_value[i], None)
            elif len(new_value) > len(old_value):
                for i in range(len(old_value), len(new_value)):
                    diff[str(i)] = (None, new_value[i])
        else:
            diff = {"old": old_value, "new": new_value}
        return diff

    def _format_diff(self, diff: dict[Any, Any]) -> str:
        """Format the diff dictionary into a readable string."""
        formatted_lines = []
        for key, (old, new) in diff.items():
            if old is None:
                formatted_lines.append(f"[{key}]: ADDED: '{new}'")
            elif new is None:
                formatted_lines.append(f"[{key}]: REMOVED: '{old}'")
            else:
                formatted_lines.append(f"[{key}]:\n\tFROM: '{old}'\n\t  TO: '{new}'")
        return "\n".join(formatted_lines)

    def on_handle_set_config_value_request(self, request: SetConfigValueRequest) -> ResultPayload:
        if request.category_and_key == "":
            result_details = "Attempted to set config value but no category or key was specified."
            return SetConfigValueResultFailure(result_details=result_details)

        # Fetch the existing value (don't go to the env vars directly; we want the key)
        old_value = self.get_config_value(request.category_and_key, should_load_env_var_if_detected=False)

        # Make a copy of the existing value if it is a dict or list
        if isinstance(old_value, (dict, list)):
            old_value_copy = copy.deepcopy(old_value)
        else:
            old_value_copy = old_value

        # Set the new value
        self.set_config_value(key=request.category_and_key, value=request.value)

        # For container types, indicate the change with a diff
        if isinstance(request.value, (dict, list)):
            if old_value_copy is not None:
                diff = self._get_diff(old_value_copy, request.value)
                formatted_diff = self._format_diff(diff)
                if formatted_diff:
                    result_details = f"Successfully updated {type(request.value).__name__} at '{request.category_and_key}'. Changes:\n{formatted_diff}"
                else:
                    result_details = f"Successfully updated {type(request.value).__name__} at '{request.category_and_key}'. No changes detected."
            else:
                result_details = f"Successfully updated {type(request.value).__name__} at '{request.category_and_key}'"
        else:
            result_details = f"Successfully assigned the config value for '{request.category_and_key}':\n\tFROM '{old_value_copy}'\n\tTO: '{request.value}'"

        return SetConfigValueResultSuccess(result_details=result_details)

    def _write_user_config_delta(self, user_config_delta: dict) -> None:
        """Write the user configuration to the config file.

        This method creates the config file if it doesn't exist and writes the
        current configuration to it.

        Args:
            user_config_delta: The user configuration delta to write to the file Will be merged with the existing config on disk.
            workspace_dir: The path to the config file
        """
        if not USER_CONFIG_PATH.exists():
            USER_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            USER_CONFIG_PATH.touch()
            USER_CONFIG_PATH.write_text(json.dumps({}, indent=2))
        try:
            current_config = json.loads(USER_CONFIG_PATH.read_text())
        except json.JSONDecodeError:
            backup = USER_CONFIG_PATH.rename(USER_CONFIG_PATH.with_suffix(".bak"))
            logger.error(
                "Error parsing user config file %s. Saved this to a backup %s and created a new one.",
                USER_CONFIG_PATH,
                backup,
            )
            current_config = {}
        merged_config = merge_dicts(current_config, user_config_delta)
        USER_CONFIG_PATH.write_text(json.dumps(merged_config, indent=2))

    def _set_log_level(self, level: str) -> None:
        """Set the log level for the logger.

        Args:
            level: The log level to set (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        """
        try:
            logger.setLevel(level.upper())
        except ValueError:
            logger.error("Invalid log level %s. Defaulting to INFO.", level)
            logger.setLevel(logging.INFO)
