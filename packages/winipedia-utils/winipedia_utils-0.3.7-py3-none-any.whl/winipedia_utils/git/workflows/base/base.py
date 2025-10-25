"""Contains base utilities for git workflows."""

from abc import abstractmethod
from typing import Any

from winipedia_utils.text.config import YamlConfigFile
from winipedia_utils.text.string import split_on_uppercase


class Workflow(YamlConfigFile):
    """Base class for workflows."""

    @abstractmethod
    def get_workflow_triggers(self) -> dict[str, Any]:
        """Get the workflow triggers."""

    @abstractmethod
    def get_permissions(self) -> dict[str, Any]:
        """Get the workflow permissions."""

    @abstractmethod
    def get_jobs(self) -> dict[str, Any]:
        """Get the workflow jobs."""

    @classmethod
    def get_workflow_name(cls) -> str:
        """Get the workflow name."""
        return " ".join(split_on_uppercase(cls.__name__))

    def get_run_name(self) -> str:
        """Get the workflow run name."""
        return self.get_workflow_name() + self.get_repo_and_ref_name_formatted()

    def get_configs(self) -> dict[str, Any]:
        """Get the workflow config."""
        return {
            "name": self.get_workflow_name(),
            "on": self.get_workflow_triggers(),
            "permissions": self.get_permissions(),
            "run-name": self.get_run_name(),
            "jobs": self.get_jobs(),
        }

    @classmethod
    def get_checkout_step(cls, fetch_depth: int | None = None) -> dict[str, Any]:
        """Get the checkout step.

        Args:
        fetch_depth: The fetch depth to use. If None, no fetch depth is specified.

        Returns:
        The checkout step.
        """
        step: dict[str, Any] = {
            "name": "Checkout repository",
            "uses": "actions/checkout@v5",
        }
        if fetch_depth is not None:
            step["with"] = {"fetch-depth": fetch_depth}
        return step

    @classmethod
    def get_poetry_setup_steps(
        cls,
        *,
        install_dependencies: bool = False,
        fetch_depth: int | None = None,
        configure_pipy_token: bool = False,
        force_main_head: bool = False,
    ) -> list[dict[str, Any]]:
        """Get the poetry steps.

        Args:
        install_dependencies: Whether to install dependencies.
        fetch_depth: The fetch depth to use. If None, no fetch depth is specified.
        configure_pipy_token: Whether to configure the pipy token.
        force_main_head: Whether to exit if the running branch or current commit is not
            equal to the most recent commit on main. This is useful for workflows that
            should only run on main.

        Returns:
        The poetry steps.
        """
        steps = [cls.get_checkout_step(fetch_depth)]
        if force_main_head:
            # exit with code 1 if the running branch is not main
            steps.append(
                {
                    "name": "Assert running on head of main",
                    "run": 'git fetch origin main --depth=1; main_sha=$(git rev-parse origin/main); if [ "$GITHUB_SHA" != "$main_sha" ]; then echo "Tag commit is not the latest commit on main."; exit 1; fi',  # noqa: E501
                }
            )
        steps.append(
            {
                "name": "Setup Python",
                "uses": "actions/setup-python@v6",
                "with": {"python-version": "3.x"},
            }
        )
        steps.append(
            {
                "name": "Install Poetry",
                "run": "curl -sSL https://install.python-poetry.org | python3 -",
            }
        )
        if configure_pipy_token:
            steps.append(
                {
                    "name": "Configure Poetry",
                    "run": "poetry config pypi-token.pypi ${{ secrets.PYPI_TOKEN }}",
                }
            )
        if install_dependencies:
            steps.append({"name": "Install Dependencies", "run": "poetry install"})
        return steps

    def get_repository_name(self) -> str:
        """Get the repository name."""
        return "${{ github.event.repository.name }}"

    def get_ref_name(self) -> str:
        """Get the ref name."""
        return "${{ github.ref_name }}"

    def get_repo_and_ref_name_formatted(self) -> str:
        """Get the repository name and ref name."""
        return f": {self.get_repository_name()}-{self.get_ref_name()}"
