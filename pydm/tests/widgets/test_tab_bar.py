import pytest
from pydm.widgets.tab_bar import PyDMTabWidget
from qtpy.QtCore import QByteArray
from qtpy.QtWidgets import QWidget


def test_construct(qtbot):
    """
    Test that creating a PyDMTabWidget succeeds without errors

    Parameters
    ----------
     qtbot : fixture
        Window for widget testing
    """
    parent = QWidget()
    qtbot.addWidget(parent)

    pydm_tab_widget = PyDMTabWidget(parent=parent)
    qtbot.addWidget(pydm_tab_widget)

    parent.deleteLater()
    pydm_tab_widget.deleteLater()


@pytest.mark.parametrize(
    "new_alarm_channel",
    [
        "ca://MTEST",
        QByteArray(b"ca://MTEST"),
        b"ca://MTEST",
        "",
    ],
)
def test_set_current_alarm_channel(qtbot, monkeypatch, new_alarm_channel):
    """
    Test that setting the alarm channel with both a regular string and a QByteArray works as expected

    Parameters
    ----------
     qtbot : fixture
        Window for widget testing
     monkeypatch : fixture
        To override default behaviors
    new_alarm_channel: str or bytes
        Test value to set the alarm channel to
    """
    pydm_tab_widget = PyDMTabWidget()
    qtbot.addWidget(pydm_tab_widget)

    monkeypatch.setattr(pydm_tab_widget.tabBar(), "currentIndex", lambda: 0)

    pydm_tab_widget.currentTabAlarmChannel = new_alarm_channel
    if new_alarm_channel:
        assert pydm_tab_widget.tabBar().currentTabAlarmChannel == "ca://MTEST"
    else:
        assert pydm_tab_widget.tabBar().currentTabAlarmChannel == ""
    pydm_tab_widget.deleteLater()
