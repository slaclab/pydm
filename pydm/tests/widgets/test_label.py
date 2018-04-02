import os
import pytest

from ...PyQt.QtCore import QObject, Qt, pyqtSignal, pyqtSlot
from ...utilities import is_pydm_app
from ...widgets.label import PyDMLabel
from ...application import PyDMApplication

current_dir = os.path.abspath(os.path.dirname(__file__))


def test_construct(qtbot):
    """
    Test the basic instantiation of the widget
    :param qtbot: pytest-qt window for widget testing
    :type: qtbot
    """
    #from ...widgets.label import PyDMLabel

    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)

    display_format_type = pydm_label.displayFormat
    assert (display_format_type == pydm_label.DisplayFormat.Default)
    assert(pydm_label._string_encoding == pydm_label.app.get_string_encoding()
           if is_pydm_app() else "utf_8")


class SignalTrigger(QObject):
    value_change_signal = pyqtSignal([int])

    def __init__(self, signal_handler):
        super().__init__()
        self.value_change_signal.connect(signal_handler)

    def emit(self, value):
        self.value_change_signal.emit(value)


def test_value_changed(qtbot):
    pydm_label = PyDMLabel()
    qtbot.addWidget(pydm_label)
    display_format = pydm_label.displayFormat
    assert(display_format == pydm_label.DisplayFormat.Default)

    trigger = SignalTrigger(pydm_label.channelValueChanged)
    trigger.emit(0b100)

    pydm_label.displayFormat = pydm_label.DisplayFormat.Binary
    display_format = pydm_label.displayFormat
    assert (display_format == pydm_label.DisplayFormat.Binary)

