from pydm.data_plugins import add_plugin, PyDMPlugin, plugin_modules


def test_data_plugin_add(qapp):
    # Create test PyDMPlugin with mock protocol
    test_plug = PyDMPlugin()
    test_plug.protocol = 'tst'
    # Check that adding this after import will be reflected in PyDMApp
    add_plugin(test_plug)
    assert plugin_modules['tst'] == test_plug
    assert qapp.plugins['tst'] == test_plug


def test_default_plugin_loading(qapp):
    # Making assumption we will always have a ca plugin in standard lib
    assert 'ca' in plugin_modules
    assert 'ca' in qapp.plugins
