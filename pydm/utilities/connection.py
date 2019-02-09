import logging

from qtpy.QtWidgets import QWidget

logger = logging.getLogger(__name__)


def _change_connection_status(widget, status):
    """
    Connect or disconnect the inner channels of widgets on the
    given widget based on the status parameter.

    Parameters
    ----------
    widget : QWidget
        The widget which will be iterated over for channel connection.

    status : bool
        If True, will call connect on the channels otherwise it will call
        disconnect.
    """
    widgets = [widget]
    widgets.extend(widget.findChildren(QWidget))
    for child_widget in widgets:
        if hasattr(child_widget, 'channels'):
            if child_widget.channels() is None:
                continue
            for channel in child_widget.channels():
                if channel is None:
                    continue
                if status:
                    channel.connect()
                else:
                    channel.disconnect()

def establish_widget_connections(widget):
    """
    Connect the inner channels of widgets on the given widget.

    Parameters
    ----------
    widget : QWidget
        The widget which will be iterated over for channel connection.
    """
    _change_connection_status(widget, True)


def close_widget_connections(widget):
    """
    Disconnect the inner channels of widgets on the given widget.

    Parameters
    ----------
    widget : QWidget
        The widget which will be iterated over for channel disconnection.
    """
    _change_connection_status(widget, False)
