from ...widgets.eventplot import PyDMEventPlot


def test_add_channel(qtbot):
    """A quick check to ensure adding a channel to an event plot works as expected"""
    event_plot = PyDMEventPlot()
    qtbot.addWidget(event_plot)

    curve = "TEST:EVENT:PLOT"
    event_plot.addChannel(curve)

    assert event_plot.curveAtIndex(0).channel.address == "TEST:EVENT:PLOT"
