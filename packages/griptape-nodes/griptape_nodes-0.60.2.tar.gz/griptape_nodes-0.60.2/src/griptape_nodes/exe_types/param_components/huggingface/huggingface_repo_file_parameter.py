import logging

from griptape_nodes.exe_types.node_types import BaseNode
from griptape_nodes.exe_types.param_components.huggingface.huggingface_model_parameter import HuggingFaceModelParameter
from griptape_nodes.exe_types.param_components.huggingface.huggingface_utils import (
    list_repo_revisions_with_file_in_cache,
)

logger = logging.getLogger("griptape_nodes")


class HuggingFaceRepoFileParameter(HuggingFaceModelParameter):
    def __init__(self, node: BaseNode, repo_files: list[tuple[str, str]], parameter_name: str = "model"):
        super().__init__(node, parameter_name)
        self._repo_files = repo_files
        self.refresh_parameters()

    def fetch_repo_revisions(self) -> list[tuple[str, str]]:
        return [
            repo_revision
            for (repo, file) in self._repo_files
            for repo_revision in list_repo_revisions_with_file_in_cache(repo, file)
        ]

    def get_download_commands(self) -> list[str]:
        return [f'huggingface-cli download "{repo}" "{file}"' for (repo, file) in self._repo_files]

    def get_download_models(self) -> list[str]:
        """Returns a list of model names that should be downloaded."""
        return [repo for (repo, file) in self._repo_files]

    def get_repo_filename(self) -> str:
        repo_id, _ = self.get_repo_revision()
        for repo, file in self._repo_files:
            if repo == repo_id:
                return file
        msg = f"File not found for repository {repo_id}"
        raise ValueError(msg)
