import logging
import json

from functools import partial
from qtpy.QtCore import QObject, Signal, Slot

from .. import data_plugins
from .. import config as PYDM_CONFIG
from ..utilities import is_qt_designer
from ..data_store import DataStore

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

    def __init__(self, address=None, callback=None,
                 config=None, parent=None,
                 *args, **kwargs):
        super(PyDMChannel, self).__init__(parent=parent)
        if config is None:
            config = {}
        self._config = config
        self._address = None
        self._protocol = None
        self._parameters = None
        self._use_introspection = config.get('use_introspection', True)
        self._introspection = config.get('introspection', {})
        self._monitors = set()  # Convert to list of WeakMethod in the future
        self._busy = False
        self._connected = False
        self.address = address
        if callback:
            self.subscribe(callback)
        self.destroyed.connect(partial(self.disconnect, destroying=True))

    @Slot()
    def notified(self):
        if self._busy:
            return
        self._busy = True
        data, intro = self.get(with_introspection=True)
        if not self._use_introspection:
            intro = self._introspection
        for mon in self._monitors:
            try:
                mon(data=data, introspection=intro)
            except Exception as ex:
                logger.exception("Error invoking callback for %r", self)
        self._busy = False

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, address):
        if address is None:
            conn = self._config.get('connection', None)
            if conn is not None:
                self._protocol = conn.get('protocol')
                self._parameters = conn.get('parameters')
                self._address = json.dumps(conn)
            else:
                self._address = None
        else:
            self._address = clear_channel_address(address)

    def connected(self):
        return self._connected

    def connect(self):
        """
        Connect a PyDMChannel to the proper PyDMPlugin
        """
        if not self.address:
            return
        if is_qt_designer() and not PYDM_CONFIG.DESIGNER_ONLINE:
            return
        logger.debug("Connecting %r", self.address)
        # Connect to proper PyDMPlugin
        try:
            data_plugins.establish_connection(self)
            self._connected = True
        except Exception:
            logger.exception("Unable to make proper connection for %r", self)

    def disconnect(self, destroying=False):
        """
        Disconnect a PyDMChannel
        """
        if is_qt_designer() and not PYDM_CONFIG.DESIGNER_ONLINE:
            return
        try:
            plugin = data_plugins.plugin_for_address(self.address)
            if not plugin:
                return
            plugin.remove_connection(self, destroying=destroying)
        except Exception as exc:
            logger.exception("Unable to remove connection for %r", self)
        self._connected = False

    def get_introspection(self):
        if self._use_introspection:
            return DataStore().introspect(self.address)
        return self._introspection

    def get(self, with_introspection=False):
        ret = DataStore().fetch(self.address, with_introspection)
        if not with_introspection:
            return ret
        data, intro = ret
        # In case of user-defined introspection for inner fields
        if not self._use_introspection:
            intro = self._introspection
        return data, intro

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
