from pydm.show_macros import MacroWindow


def test_macro_window_launches(qtbot):
    """Make sure the Macro window doesn't crash."""
    a = MacroWindow(parent=None)
    qtbot.addWidget(a)
    a.show()
