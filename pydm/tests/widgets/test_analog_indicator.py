import pytest
from pydm.widgets.analog_indicator import PyDMAnalogIndicator
from qtpy.QtWidgets import QWidget


@pytest.mark.parametrize(
    "init_channel",
    [
        "CA://MTEST",
        "",
        None,
    ],
)
def test_construct(qtbot, init_channel):
    """
    Test that creating a PyDMAnalogIndicator with an initial channel works as expected

    Parameters
    ----------
     qtbot : fixture
        Window for widget testing
    init_channel : str
        The channel for the indicator
    """
    parent = QWidget()
    qtbot.addWidget(parent)

    pydm_analog_indicator = PyDMAnalogIndicator(parent=parent, init_channel=init_channel)
    qtbot.addWidget(pydm_analog_indicator)

    if init_channel:
        assert pydm_analog_indicator.channel == str(init_channel)
    else:
        assert pydm_analog_indicator.channel is None

    # This prevents pyside6 from deleting the internal c++ object
    # ("Internal C++ object (PyDMDateTimeLabel) already deleted")
    parent.deleteLater()
    pydm_analog_indicator.deleteLater()
