from pydm.widgets.eventplot import PyDMEventPlot


def test_add_channel(qtbot):
    """A quick check to ensure adding a channel to an event plot works as expected"""
    event_plot = PyDMEventPlot()
    qtbot.addWidget(event_plot)

    curve = "TEST:EVENT:PLOT"
    event_plot.addChannel(curve)

    # We need redrawPlot here to stop a specific pyside6 error where the internal C++ object for the plot gets
    # deleted early. This only happens in the case of running all the tests together with pytest.
    event_plot.redrawPlot()

    assert event_plot.curveAtIndex(0).channel.address == "TEST:EVENT:PLOT"
