"""
External tool tests
"""

import pathlib
from typing import Any, Set

import pytest

from pydm import tools
from pydm.application import PyDMApplication

EXAMPLE_PATH = pathlib.Path(__file__).parents[2] / "examples"
EXAMPLE_EXT_TOOL_PATH = EXAMPLE_PATH / "external_tool"

examples_required = pytest.mark.skipif(
    not EXAMPLE_PATH.exists(), reason="Not a source checkout - no examples available"
)


class ValidTool(tools.ExternalTool): ...


class InvalidTool: ...


@pytest.mark.parametrize(
    "cls, valid",
    [
        pytest.param(ValidTool, True, id="valid"),
        pytest.param(InvalidTool, False, id="invalid"),
        pytest.param(None, False, id="invalid-none"),
    ],
)
def test_valid_external_tool(cls: Any, valid: bool):
    assert tools._is_valid_external_tool_class(cls) is valid


@examples_required
@pytest.mark.parametrize(
    "source_file, expected_tools",
    [
        pytest.param(
            EXAMPLE_EXT_TOOL_PATH / "dummy_tool.py",
            {"DummyTool", "DummyTool3"},
            id="dummy_tool",
        ),
        pytest.param(
            EXAMPLE_EXT_TOOL_PATH / "lookup_path" / "new_tool.py",
            {"DummyTool2"},
            id="new_tool",
        ),
        pytest.param(
            EXAMPLE_EXT_TOOL_PATH / "lookup_path" / "root_tool.py",
            {"RootTool"},
            id="root_tool",
        ),
    ],
)
def test_tools_from_source(source_file: pathlib.Path, expected_tools: Set[str], qapp: PyDMApplication):
    assert source_file.exists()
    loaded_tools = [tool.__class__.__name__ for tool in tools._get_tools_from_source(str(source_file))]
    assert set(loaded_tools) == expected_tools


def test_smoke_get_entrypoint_tools(qapp):
    list(tools.get_entrypoint_tools())


def test_smoke_get_tools_from_path(qapp):
    list(tools.get_tools_from_path())


def test_smoke_load_external_tools(qapp):
    tools.load_external_tools()
