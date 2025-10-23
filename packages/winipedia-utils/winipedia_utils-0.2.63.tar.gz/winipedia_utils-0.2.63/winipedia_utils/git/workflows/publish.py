"""Contains the publish workflow.

This workflow is used to publish the package to PyPI with poetry.
"""

from pathlib import Path
from typing import Any

import yaml

from winipedia_utils.git.workflows.base.base import _get_poetry_setup_steps
from winipedia_utils.git.workflows.release import WORKFLOW_NAME

PUBLISH_WORKFLOW_PATH = Path(".github/workflows/publish.yaml")


def load_publish_workflow() -> dict[str, Any]:
    """Load the publish workflow."""
    path = PUBLISH_WORKFLOW_PATH
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    return yaml.safe_load(path.read_text()) or {}


def dump_publish_workflow(config: dict[str, Any]) -> None:
    """Dump the publish workflow."""
    path = PUBLISH_WORKFLOW_PATH
    with path.open("w") as f:
        yaml.safe_dump(config, f, sort_keys=False)


def _get_publish_config() -> dict[str, Any]:
    """Dict that represents the publish workflow yaml."""
    return {
        "name": "Publish to PyPI",
        "on": {
            "workflow_run": {
                "workflows": [WORKFLOW_NAME],
                "types": ["completed"],
            },
        },
        "jobs": {
            "publish": {
                "runs-on": "ubuntu-latest",
                "if": "${{ github.event.workflow_run.conclusion == 'success' }}",
                "steps": [
                    *(
                        _get_poetry_setup_steps(
                            configure_pipy_token=True,
                        )
                    ),
                    {
                        "name": "Build and publish to PyPI",
                        "run": "poetry publish --build",
                    },
                ],
            }
        },
    }


def _publish_config_is_correct() -> bool:
    """Check if the publish workflow is correct."""
    config = load_publish_workflow()
    return bool(config == _get_publish_config())


def _add_publish_workflow() -> None:
    """Add the publish workflow.

    If you delete the .github/workflows/publish.yaml file, then the tests will not fail.
    Not all projects need publishing to pypi. It is added on setup, but if you remove
    the file, then the tests will not fail and the tests will assume you don't want it.
    """
    if _publish_config_is_correct():
        return
    config = _get_publish_config()
    dump_publish_workflow(config)
