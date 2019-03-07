import logging
import weakref

from qtpy.QtCore import QObject, Signal, Slot

import pydm.data_plugins
from pydm import config
from pydm.utilities import is_qt_designer
from pydm.data_plugins.data_store import DataStore

logger = logging.getLogger(__name__)


def clear_channel_address(channel):
    # We must remove spaces, \n, \t and other crap from
    # channel address
    if channel is None:
        return None
    return str(channel).strip()


class PyDMChannel(QObject):
    """
    Object to hold signals and slots for a PyDM Widget interface to an
    external plugin

    The purpose of this class is to create a templated slot and signals
    list that can be sent to an external plugin. The type of plugin is
    determined by the PyDMApplication based on the identifier placed at
    the beginning of the :attr:`.address` attribute. This allows a generic
    way to connect slots and signals to functionality within your PyDM
    Widget. Slots should be connected to functions on your created widget
    that perform actions upon changes. For instance, the :attr:`.value_slot`
    will be automatically called every time a new value is found by the
    plugin. This should probably linked to a function that updates the
    display to report the new value. Signals perform the reverse operation.
    These should be used to send new values back to the plugin to update
    the source.

    Using this structure to interface with plugins allows your created PyDM
    Widget a greater flexibility in choosing its underlying source. For
    instance, returning to the example of the :attr:`.value_slot`,
    getting a value to display from channel access or from the EPICS Archiver
    are very different operations. However, actually displaying the value
    should be identical. By simply attaching your PyDM Widget's display
    functionality to the :attr:`.value_slot` you have created a
    Widget that can do either interchangeably, all the user has to do is
    specify the correct address signature and the rest of the work is done
    by the underlying plugins.

    Parameters
    ----------
    parent : QObject, optional
        The parent of this PyDMChannel. Defaults to None.

    address : str, optional
        The name of the address to be used by the plugin. This
        should usually be a user inputted field when a specific
        PyDM widget is initialized

    callback : callable, optional
        The function or method to be invoked when data changes for this channel

    """
    transmit = Signal([dict])

    def __init__(self, parent=None, address=None, callback=None, *args,
                 **kwargs):
        super(PyDMChannel, self).__init__(parent=parent)
        self._address = None
        self._monitors = set()  # Convert to list of WeakMethod in the future
        self.address = address
        print('Creating channel for: ', address, ' with callback: ', callback)
        if callback:
            self.subscribe(callback)

    @Slot()
    def notified(self):
        data, intro = self.get(with_introspection=True)
        for mon in self._monitors:
            try:
                mon(data=data, introspection=intro)
            except Exception as ex:
                logger.exception("Error invoking callback for %r", self)

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, address):
        self._address = clear_channel_address(address)

    def connect(self):
        """
        Connect a PyDMChannel to the proper PyDMPlugin
        """
        if not self.address:
            return
        if is_qt_designer() and not config.DESIGNER_ONLINE:
            return
        logger.debug("Connecting %r", self.address)
        # Connect to proper PyDMPlugin
        try:
            pydm.data_plugins.establish_connection(self)
        except Exception:
            logger.exception("Unable to make proper connection for %r", self)

    def disconnect(self, destroying=False):
        """
        Disconnect a PyDMChannel
        """
        if is_qt_designer() and not config.DESIGNER_ONLINE:
            return
        try:
            plugin = pydm.data_plugins.plugin_for_address(self.address)
            if not plugin:
                return
            plugin.remove_connection(self, destroying=destroying)
        except Exception as exc:
            logger.exception("Unable to remove connection for %r", self)

    def get(self, with_introspection=False):
        return DataStore().fetch(self.address, with_introspection)

    def put(self, data):
        self.transmit.emit(data)

    def subscribe(self, callback):
        if callable(callback):
            self._monitors.add(callback)
        else:
            logger.error('Callback for %r must be a callable.', self)

    def unsubscribe(self, callback):
        self._monitors.remove(callback)

    def clear_subscriptions(self):
        self._monitors = set()

    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.address == other.address
        return NotImplemented

    def __ne__(self, other):
        equality_result = self.__eq__(other)
        if equality_result is not NotImplemented:
            return not equality_result
        return NotImplemented

    def __hash__(self):
        return id(self)

    def __repr__(self):
        return '<PyDMChannel ({:})>'.format(self.address)
