# Unit Tests for the Channel widget class
from ...widgets.label import PyDMLabel
from ...widgets.line_edit import PyDMLineEdit
from ...widgets.channel import PyDMChannel
from pydm.data_plugins import plugin_for_address
class A():
    pass

def test_construct(qtbot):
    """
    Test the construct of the widget.

    Expectations:
    1. The widget is created with all the default values for its properties
    2. When created for a specific widget type, the Channel widget contains the default values, i.e. the appropriate
        slots, for that specific widget type
    3. Channel widgets can be compared for equality and inequality using the '==' and '!=' operators.

    Parameters
    ----------
    qtbot : fixture
        Window for widget testing
    """
    pydm_channel = PyDMChannel()

    assert pydm_channel.address is None and \
        pydm_channel.connection_slot is None and \
        pydm_channel.value_slot is None and \
        pydm_channel.severity_slot is None and \
        pydm_channel.enum_strings_slot is None and \
        pydm_channel.unit_slot is None and \
        pydm_channel.prec_slot is None and \
        pydm_channel.upper_ctrl_limit_slot is None and \
        pydm_channel.lower_ctrl_limit_slot is None and \
        pydm_channel.write_access_slot is None and \
        pydm_channel.value_signal is None

    pydm_label = PyDMLabel(init_channel='tst://this')
    qtbot.addWidget(pydm_label)

    pydm_label_channels = pydm_label.channels()[0]
    default_pydm_label_channels = PyDMChannel(address=pydm_label.channel,
                                              connection_slot=pydm_label.connectionStateChanged,
                                              value_slot=pydm_label.channelValueChanged,
                                              severity_slot=pydm_label.alarmSeverityChanged,
                                              enum_strings_slot=pydm_label.enumStringsChanged,
                                              unit_slot=pydm_label.unitChanged,
                                              prec_slot=pydm_label.precisionChanged,
                                              upper_ctrl_limit_slot=pydm_label.upperCtrlLimitChanged,
                                              lower_ctrl_limit_slot=pydm_label.lowerCtrlLimitChanged,
                                              value_signal=None,
                                              write_access_slot=None)
    assert pydm_label_channels == default_pydm_label_channels

    pydm_lineedit = PyDMLineEdit(init_channel='tst://this2')
    qtbot.addWidget(pydm_lineedit)

    # Test equal and not equal comparisons
    pydm_lineedit_channels = pydm_lineedit.channels()[0]
    assert pydm_lineedit_channels != default_pydm_label_channels

    not_same_type = A()
    equal_result = not_same_type == default_pydm_label_channels
    not_equal_result = not_same_type != default_pydm_label_channels
    assert equal_result is False and not_equal_result is True


def test_pydm_connection(test_plugin):
    # Plugin, Channel and Registry
    chan = PyDMChannel('tst://Tst:this')
    plugin = plugin_for_address(chan.address)
    plugin_no = len(plugin.connections)
    # Make a connection
    chan.connect()
    assert len(plugin.connections) == plugin_no + 1
    # Remove connections
    chan.disconnect()
    assert len(plugin.connections) == plugin_no
