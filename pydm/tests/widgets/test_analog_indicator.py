import pytest
from pydm.widgets.analog_indicator import PyDMAnalogIndicator
from pydm.widgets.scale import QScale
from qtpy.QtCore import Qt
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


def test_title_default(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    indicator = PyDMAnalogIndicator(parent=parent)
    qtbot.addWidget(indicator)

    assert indicator.title == ""
    assert indicator.title_label.isHidden()

    parent.deleteLater()
    indicator.deleteLater()


def test_title_set_and_get(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    indicator = PyDMAnalogIndicator(parent=parent)
    qtbot.addWidget(indicator)

    indicator.title = "Test Title"
    assert indicator.title == "Test Title"
    assert indicator.title_label.text() == "Test Title"
    assert not indicator.title_label.isHidden()

    parent.deleteLater()
    indicator.deleteLater()


def test_title_clear_hides_label(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    indicator = PyDMAnalogIndicator(parent=parent)
    qtbot.addWidget(indicator)

    indicator.title = "Visible"
    assert not indicator.title_label.isHidden()

    indicator.title = ""
    assert indicator.title_label.isHidden()

    parent.deleteLater()
    indicator.deleteLater()


def test_title_reset(qtbot):
    parent = QWidget()
    qtbot.addWidget(parent)
    indicator = PyDMAnalogIndicator(parent=parent)
    qtbot.addWidget(indicator)

    indicator.title = "Something"
    indicator.resetTitle()
    assert indicator.title == ""
    assert indicator.title_label.isHidden()

    parent.deleteLater()
    indicator.deleteLater()


@pytest.mark.parametrize(
    "prop, value",
    [
        ("valuePosition", Qt.LeftEdge),
        ("orientation", Qt.Vertical),
        ("flipScale", True),
        ("invertedAppearance", True),
    ],
)
def test_title_survives_relayout(qtbot, prop, value):
    """Changing any layout-affecting property rebuilds the layout, ensure the title widget remains as expected."""
    parent = QWidget()
    qtbot.addWidget(parent)
    indicator = PyDMAnalogIndicator(parent=parent)
    qtbot.addWidget(indicator)
    indicator.title = "Title"

    setattr(indicator, prop, value)
    # Both calls would raise RuntimeError if the QLabel's C++ object was deleted along with the old layout
    assert indicator.title_label.text() == "Title"
    assert indicator.title == "Title"
    assert indicator.widget_layout.indexOf(indicator.title_label) != -1
    assert indicator.title_label.parent() is indicator

    parent.deleteLater()
    indicator.deleteLater()
