import os

from pydm.data_plugins import (add_plugin, PyDMPlugin, plugin_modules,
                               load_plugins_from_path)


def test_data_plugin_add(qapp):
    # Create test PyDMPlugin with mock protocol
    test_plug = PyDMPlugin
    test_plug.protocol = 'tst'
    # Check that adding this after import will be reflected in PyDMApp
    add_plugin(test_plug)
    assert isinstance(plugin_modules['tst'], test_plug)
    assert isinstance(qapp.plugins['tst'], test_plug)


def test_plugin_directory_loading(qapp):
    # Create a fake file
    cur_dir = os.getcwd()
    with open(os.path.join(cur_dir, 'plugin_foo.py'), 'w+') as handle:
        handle.write(fake_file)
        handle.flush()
    # Load plugins
    load_plugins_from_path([cur_dir], 'foo.py')
    assert 'tst1' in plugin_modules
    assert 'tst2' in plugin_modules
    os.remove(os.path.join(cur_dir, 'plugin_foo.py'))


fake_file = """\
from pydm.data_plugins import PyDMPlugin


class TestPlugin1(PyDMPlugin):
    protocol = 'tst1'


class TestPlugin2(PyDMPlugin):
    protocol = 'tst2'
"""
