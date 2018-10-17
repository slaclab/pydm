import os

import pydm.data_plugins
from pydm.data_plugins import (plugin_modules, load_plugins_from_path,
                               plugin_for_address)
from pydm import config

def test_data_plugin_add(qapp, test_plugin):
    # Check that adding this after import will be reflected in PyDMApp
    assert isinstance(plugin_modules['tst'], test_plugin)
    assert isinstance(qapp.plugins['tst'], test_plugin)


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


def test_plugin_for_address(test_plugin):
    # Get by protocol
    assert isinstance(plugin_for_address('tst://tst:this'),
                      test_plugin)
    assert plugin_for_address('tst:this') is None
    # Default protocol
    config.DEFAULT_PROTOCOL = 'tst'
    assert isinstance(plugin_for_address('tst:this'),
                      test_plugin)


fake_file = """\
from pydm.data_plugins import PyDMPlugin


class TestPlugin1(PyDMPlugin):
    protocol = 'tst1'


class TestPlugin2(PyDMPlugin):
    protocol = 'tst2'
"""
