# Unit Tests for the Window Widget

from ...widgets.window import PyDMWindow


# --------------------
# POSITIVE TEST CASES
# --------------------


def test_construct(qtbot):
    """
    Test the construction of the widget.

    Expectations:
    The correct default values are assigned to the widget's attributes.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    """
    pydm_window = PyDMWindow()
    qtbot.addWidget(pydm_window)

    assert pydm_window._hide_menu_bar is False
    assert pydm_window._hide_nav_bar is False
    assert pydm_window._hide_status_bar is False
