# Unit Tests for the PyDMCheckbox Widget

import pytest
from qtpy.QtCore import Qt
from pydm.widgets.checkbox import PyDMCheckbox


@pytest.mark.parametrize("value, expected",
                         [(None, Qt.Unchecked),
                          (0, Qt.Unchecked),
                          (-1, Qt.Unchecked),
                          (1, Qt.Checked),
                          (False, Qt.Unchecked),
                          (True, Qt.Checked)
                          ])
def test_value_changed(qtbot, value, expected):
    widget = PyDMCheckbox()
    qtbot.addWidget(widget)

    assert widget.checkState() == Qt.Unchecked

    widget.value_changed(value)
    assert widget.checkState() == expected


@pytest.mark.parametrize("checked", [False, True])
def test_send_value(qtbot, checked):
    widget = PyDMCheckbox()
    qtbot.addWidget(widget)

    def foo(val):
        widget.test_write = val
    widget.write_to_channel = foo

    assert widget.checkState() == Qt.Unchecked
    widget.send_value(checked)
    if checked:
        assert widget.test_write == 1
    else:
        assert widget.test_write == 0
