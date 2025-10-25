"""Module-level test fixtures and utilities.

This module provides fixtures and test functions that operate at the module scope,
ensuring that all functions and classes within a module have corresponding tests.
These fixtures are automatically applied to all test modules through pytest's autouse
mechanism.
"""

import pytest

from winipedia_utils.modules.module import to_module_name
from winipedia_utils.testing.config import ZeroTestConfigFile
from winipedia_utils.testing.fixtures import autouse_module_fixture
from winipedia_utils.testing.tests.base.utils.utils import assert_no_untested_objs


@autouse_module_fixture
def assert_all_funcs_and_classes_tested(request: pytest.FixtureRequest) -> None:
    """Verify that all functions and classes in a module have corresponding tests.

    This fixture runs automatically for each test module and checks that every
    function and class defined in the corresponding source module has a test
    function or class defined in the test module.

    Args:
        request: The pytest fixture request object containing the current module

    Raises:
        AssertionError: If any function or class in the source module lacks a test

    """
    module = request.module
    if module.__name__ == to_module_name(ZeroTestConfigFile().get_path()):
        return
    assert_no_untested_objs(module)
