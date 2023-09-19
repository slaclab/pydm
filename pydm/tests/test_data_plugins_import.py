import os

import entrypoints

from pydm import config
from pydm.data_plugins import (
    PyDMPlugin,
    initialize_plugins_if_needed,
    load_plugins_from_entrypoints,
    load_plugins_from_path,
    plugin_for_address,
    plugin_modules,
)


def test_data_plugin_add(qapp, test_plugin):
    # Check that adding this after import will be reflected in PyDMApp
    initialize_plugins_if_needed()
    assert isinstance(plugin_modules["tst"], test_plugin)
    assert isinstance(qapp.plugins["tst"], test_plugin)


def test_plugin_directory_loading(qapp, caplog):
    # Create a fake file
    cur_dir = os.getcwd()
    with open(os.path.join(cur_dir, "plugin_foo.py"), "w+") as handle:
        handle.write(fake_file)
        handle.flush()

    try:
        # Load plugins. One of them will raise an exception during initialization. This will
        # prevent it from being added to the available plugins, but the others should still load.
        load_plugins_from_path([cur_dir], "foo.py")
        assert "tst1" in plugin_modules
        assert "tst2" in plugin_modules
        assert "fail" not in plugin_modules

        # Check for the error logged when a plugin fails to load. Confirms that the plugin that failed to load
        # was the one expected to fail, and that there was only one failure total.
        assert "FailingTestPlugin'> failed to load and will not be available for use" in caplog.text
        assert caplog.text.count("failed to load and will not be available for use") == 1
    finally:
        os.remove(os.path.join(cur_dir, "plugin_foo.py"))


def test_plugin_for_address(test_plugin, monkeypatch):
    # Get by protocol
    assert isinstance(plugin_for_address("tst://tst:this"), test_plugin)
    assert plugin_for_address("tst:this") is None
    # Default protocol
    monkeypatch.setattr(config, "DEFAULT_PROTOCOL", "tst")
    assert isinstance(plugin_for_address("tst:this"), test_plugin)


fake_file = """\
from pydm.data_plugins import PyDMPlugin


class TestPlugin1(PyDMPlugin):
    protocol = 'tst1'


class FailingTestPlugin(PyDMPlugin):
    protocol = 'fail'

    def __init__(self, *args, **kwargs):
        raise Exception  # Purposefully fail to initialize for testing purposes

class TestPlugin2(PyDMPlugin):
    protocol = 'tst2'
"""


def test_entrypoint_import(monkeypatch):
    class MyTestPlugin(PyDMPlugin):
        protocol = "__test_suite_protocol__"

    class Entrypoint:
        name = "MyTestPlugin"

        def load(self):
            return MyTestPlugin

    def get_group_all(key):
        yield Entrypoint()

    monkeypatch.setattr(entrypoints, "get_group_all", get_group_all)
    loaded = load_plugins_from_entrypoints()

    assert "__test_suite_protocol__" in loaded
    assert isinstance(loaded["__test_suite_protocol__"], MyTestPlugin)
