import logging
import numpy as np

from p4p.client.thread import Context, Disconnected
from p4p.wrapper import Value
from qtpy.QtCore import Slot
from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection


logger = logging.getLogger(__name__)


class PVAContext(object):
    """ Singleton class responsible for holding the pva context. """
    __instance = None

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        self.context = Context('pva', maxsize=2)

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(PVAContext)
            cls.__instance.__initialized = False
        return cls.__instance


class Connection(PyDMConnection):

    def __init__(self, channel, address, protocol=None, parent=None):
        super().__init__(channel, address, protocol, parent)
        self._connected = True
        self.monitor = PVAContext().context.monitor(name=address,
                                                    cb=self.send_new_value,
                                                    notify_disconnect=True)
        self._value = None
        self._severity = None
        self._precision = None
        self._enum_strs = None
        self._unit = None
        self._upper_ctrl_limit = None
        self._lower_ctrl_limit = None

    def clear_cache(self):
        self._value = None
        self._severity = None
        self._precision = None
        self._enum_strs = None
        self._unit = None
        self._upper_ctrl_limit = None
        self._lower_ctrl_limit = None

    def send_new_value(self, value: Value):
        if isinstance(value, Disconnected):
            self._connected = False
            self.connection_state_signal.emit(False)

            self.data = {'CONNECTION': False}
        else:
            if not self._connected:
                self._connected = True
                self.connection_state_signal.emit(True)
                # TODO: It sure would be nice if the changedSet worked the way I expect it to
            if value.value is not None and not np.array_equal(value, self._value):
                self.

    def close(self):
        self.monitor.close()
        super(Connection, self).close()


class P4PPlugin(PyDMPlugin):
    # NOTE: protocol is intentionally "None" to keep this plugin from getting directly imported.
    # If this plugin is chosen as the One True PVA Plugin in pva_plugin.py, the protocol will
    # be properly set before it is used.
    protocol = None
    connection_class = Connection
