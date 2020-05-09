import functools
import logging
import json
import math
import numpy as np

from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection
from qtpy.QtCore import Slot, QThread, Signal
from qtpy.QtWidgets import QApplication

import pydm

logger = logging.getLogger(__name__)


class CalcThread(QThread):
    new_data_signal = Signal(dict)

    def __init__(self, config, *args, **kwargs):
        QThread.__init__(self, *args, **kwargs)
        self.app = QApplication.instance()
        self.app.aboutToQuit.connect(self.requestInterruption)

        self.config = config

        self._channels = []
        self._calculate = False
        self._value = None
        self._values = None
        self._connections = None
        self._expression = self.config.get('expr', '')

        for ch_idx, ch in enumerate(self.config.get('channels', [])):
            conn_cb = functools.partial(self.callback_conn, ch_idx)
            value_cb = functools.partial(self.callback_value, ch_idx)
            c = pydm.PyDMChannel(ch, connection_slot=conn_cb,
                                 value_slot=value_cb)
            self._channels.append(c)

    @property
    def connected(self):
        return all(self._connections)

    @property
    def value(self):
        return self._value

    def _connect(self):
        self._values = [None]*len(self._channels)
        self._connections = [False]*len(self._channels)
        for ch in self._channels:
            ch.connect()

    def _disconnect(self):
        for ch in self._channels:
            ch.disconnect()

    def _send_update(self):
        self.new_data_signal.emit({"connection": self.connected,
                                   "value": self.value})

    def run(self):
        self._connect()
        while not self.isInterruptionRequested():
            if self._calculate:
                self.calculate_expression()
            self.msleep(33)  # 30Hz

    def callback_value(self, ch_index, value):
        """
        Callback executed when a channel receives a new value.

        Parameters
        ----------
        ch_index : int
            The channel index on the list for this rule.
        value : any
            The new value for this channel.

        Returns
        -------
        None
        """
        self._values[ch_index] = value
        if not self.connected:
            self.warn_unconnected_channels()
            return
        self._calculate = True

    def callback_conn(self, ch_index, value):
        """
        Callback executed when a channel connection status is changed.

        Parameters
        ----------
        ch_index : int
            The channel index on the list for this rule.
        value : bool
            Whether or not this channel is connected.

        Returns
        -------
        None
        """
        self._connections[ch_index] = value
        self._send_update()

    def warn_unconnected_channels(self):
        logger.debug(
            "Calculation '%s': Not all channels are connected, skipping execution.",
            self.objectName())

    def calculate_expression(self):
        """
        Evaluate the expression defined by the rule and emit the `rule_signal`
        with the new value.

        .. warning

            This method mutates the input rule in-place

        Returns
        -------
        None
        """
        self._calculate = False
        vals = list(self._values)

        eval_env = {'np': np,
                    'ch': vals}
        eval_env.update({k: v
                         for k, v in math.__dict__.items()
                         if k[0] != '_'})

        try:
            ret = eval(self._expression, eval_env)
            self._value = ret
            self._send_update()
        except Exception as e:
            logger.exception("Error while evaluating CalcPlugin connection %s",
                             self.objectName())


class Connection(PyDMConnection):
    def __init__(self, channel, address, protocol=None, parent=None):
        super(Connection, self).__init__(channel, address, protocol, parent)
        self._calc_thread = None
        self._configuration = {}
        self._waiting_config = True

        self.add_listener(channel)
        self._init_connection()

        self._setup_calc(address)

    def _init_connection(self):
        self.write_access_signal.emit(False)

    def _setup_calc(self, address):
        if not self._waiting_config:
            logger.debug('CalcPlugin connection already configured.')
            return
        try:
            self._configuration = json.loads(address)
        except:
            logger.info("Invalid configuration for CalcPlugin connection. %s",
                        address)
            return

        if self._configuration.get('channels') \
                and self._configuration.get('expr'):
            self._waiting_config = False

        name = self._configuration.get('name')

        self._calc_thread = CalcThread(self._configuration)
        self._calc_thread.setObjectName("calc_{}".format(name))
        self._calc_thread.new_data_signal.connect(self.receive_new_data)
        self._calc_thread.start()

    @Slot(dict)
    def receive_new_data(self, data):
        if not data:
            return
        conn = data.get('connection', False)
        val = data.get('value', None)
        self.connected = conn
        self.connection_state_signal.emit(conn)
        if val:
            self.new_value_signal[type(val)].emit(val)

    @Slot(int)
    @Slot(float)
    @Slot(str)
    @Slot(np.ndarray)
    def put_value(self, new_val):
        return

    def add_listener(self, channel):
        super(Connection, self).add_listener(channel)

    def close(self):
        self._calc_thread.requestInterruption()


class CalculationPlugin(PyDMPlugin):
    protocol = "calc"
    connection_class = Connection

    @staticmethod
    def get_connection_id(channel):
        address = PyDMPlugin.get_address(channel)
        j_addr = json.loads(address)
        name = j_addr.get('name')
        if not name:
            raise ValueError("Name is a required field for calc plugin")
