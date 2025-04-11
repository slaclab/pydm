import pytest

from qtpy.QtGui import QColor
from qtpy.QtCore import Qt
from pydm.widgets.byte import PyDMMultiStateIndicator


@pytest.mark.parametrize(
    "value, expectedColor",
    [
        (0, QColor(Qt.black)),
        (4, QColor(Qt.red)),
        (7, QColor(Qt.darkGreen)),
        (15, QColor(Qt.yellow)),
    ],
)
def test_state_change(qtbot, signals, value, expectedColor):
    """
    Test the widget's handling of the value changed event.

    Expectations:
    1. Widget state is update to reflect incoming signal value
    2. Widgets color after state-update is the correct color set for the new state

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    signals : fixture
        The signals fixture, which provides access signals to be bound to the appropriate slots
    expected : int
        Expected resulting color after state-update
    """
    pydm_multistate = PyDMMultiStateIndicator()
    qtbot.addWidget(pydm_multistate)
    pydm_multistate.show()

    pydm_multistate.state4Color = QColor(Qt.red)
    pydm_multistate.state7Color = QColor(Qt.darkGreen)
    pydm_multistate.state15Color = QColor(Qt.yellow)

    pydm_multistate._connected = True

    signals.new_value_signal[type(value)].connect(pydm_multistate.channelValueChanged)
    signals.new_value_signal[type(value)].emit(value)

    assert pydm_multistate._curr_state == value
    assert pydm_multistate._curr_color == expectedColor
