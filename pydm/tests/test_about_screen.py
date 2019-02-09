from pydm.about_pydm import AboutWindow
def test_about_window_launches(qtbot):
    """Make sure the About window doesn't crash."""
    a = AboutWindow(parent=None)
    qtbot.addWidget(a)
    a.show()