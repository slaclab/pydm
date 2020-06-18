import collections
import functools
import json
import jsonschema
import logging
import math
import threading
import warnings

import numpy as np
from qtpy.QtCore import Slot, QThread, Signal, Qt
from qtpy.QtWidgets import QApplication

import pydm
from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection

logger = logging.getLogger(__name__)

CALC_ADDRESS_SCHEMA = json.loads("""
{
    "definitions": {
        "channel": {
            "type": "object",
            "additionalProperties": {"type": "string"}
        }
    },

    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "expr": {"type": "string"},
        "channels": {"$ref": "#/definitions/channel"}
    },
    "required": ["name", "expr", "channels"]
}
""")

CALC_ADDRESS_MINIMUM_SCHEMA = json.loads("""
{
    "type": "object",
    "properties": {
        "name": {"type": "string"}
    },
    "required": ["name"],
    "additionalProperties": false
}
""")

def epics_string(value, string_encoding="utf-8"):
    # Stop at the first zero (EPICS convention)
    # Assume the ndarray is one-dimensional
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        zeros = np.where(value == 0)[0]
    if zeros.size > 0:
        value = value[:zeros[0]]
    r = value.tobytes().decode(string_encoding)
    return r


class CalcThread(QThread):
    eval_env = {'math': math,
                'np': np,
                'numpy': np,
                'epics_string': epics_string}

    new_data_signal = Signal(dict)

    def __init__(self, config, *args, **kwargs):
        QThread.__init__(self, *args, **kwargs)
        self.app = QApplication.instance()
        self.app.aboutToQuit.connect(self.requestInterruption)

        self.config = config

        self._calculate = threading.Event()
        self._names = []
        self._channels = []
        self._value = None
        self._values = collections.defaultdict(None)
        self._connections = collections.defaultdict(lambda: False)
        self._expression = self.config.get('expr', '')

        channels = self.config.get('channels', {})
        for name, channel in channels.items():
            conn_cb = functools.partial(self.callback_conn, name)
            value_cb = functools.partial(self.callback_value, name)
            c = pydm.PyDMChannel(channel, connection_slot=conn_cb,
                                 value_slot=value_cb)
            self._channels.append(c)
            self._names.append(name)

    @property
    def connected(self):
        return all(v for _, v in self._connections.items())

    def _connect(self):
        for ch in self._channels:
            ch.connect()

    def _disconnect(self):
        for ch in self._channels:
            ch.disconnect()

    def _send_update(self, conn, value):
        self.new_data_signal.emit({"connection": conn,
                                   "value": value})

    def run(self):
        self._connect()

        while True:
            self._calculate.wait()
            self._calculate.clear()
            if self.isInterruptionRequested():
                break
            self.calculate_expression()
        self._disconnect()

    def callback_value(self, name, value):
        """
        Callback executed when a channel receives a new value.

        Parameters
        ----------
        name : str
            The channel variable name.
        value : any
            The new value for this channel.

        Returns
        -------
        None
        """
        self._values[name] = value
        if not self.connected:
            logger.debug(
                "Calculation '%s': Not all channels are connected, skipping execution.",
                self.objectName())
            return
        self._calculate.set()

    def callback_conn(self, name, value):
        """
        Callback executed when a channel connection status is changed.

        Parameters
        ----------
        name : str
            The channel variable name.
        value : bool
            Whether or not this channel is connected.

        """
        self._connections[name] = value
        self._send_update(self.connected, self._value)

    def calculate_expression(self):
        """
        Evaluate the expression defined by the rule and emit the `rule_signal`
        with the new value.
        """
        vals = self._values.copy()
        if any([vals.get(n) is None for n in self._names]):
            logger.debug('Skipping execution as not all values are set.')
            return

        env = dict(CalcThread.eval_env)
        env.update({k: v
                    for k, v in math.__dict__.items()
                    if k[0] != '_'})
        env.update(**vals)

        try:
            ret = eval(self._expression, env)
            self._value = ret
            self._send_update(self.connected, ret)
        except Exception as e:
            logger.exception("Error while evaluating CalcPlugin connection %s",
                             self.objectName())


class Connection(PyDMConnection):
    def __init__(self, channel, address, protocol=None, parent=None):
        super(Connection, self).__init__(channel, address, protocol, parent)
        self._calc_thread = None
        self.value = None
        self._configuration = {}
        self._waiting_config = True

        self.add_listener(channel)
        self._init_connection()

    def _init_connection(self):
        self.write_access_signal.emit(False)

    def add_listener(self, channel):
        self._setup_calc(channel)
        super(Connection, self).add_listener(channel)
        self.broadcast_value()

    def broadcast_value(self):
        self.connection_state_signal.emit(self.connected)
        if self.value is not None:
            self.new_value_signal[type(self.value)].emit(self.value)

    def _setup_calc(self, channel):
        if not self._waiting_config:
            logger.debug('CalcPlugin connection already configured.')
            return

        try:
            address = PyDMPlugin.get_address(channel)
            config = json.loads(address)
            jsonschema.validate(config, CALC_ADDRESS_SCHEMA)
        except:
            logger.debug('CalcPlugin connection waiting for configuration. %s',
                         address)
            return

        self._configuration = config
        self._waiting_config = False

        name = self._configuration.get('name')

        self._calc_thread = CalcThread(self._configuration)
        self._calc_thread.setObjectName("calc_{}".format(name))
        self._calc_thread.new_data_signal.connect(self.receive_new_data,
                                                  Qt.QueuedConnection)
        self._calc_thread.start()
        return True

    @Slot(dict)
    def receive_new_data(self, data):
        if not data:
            return
        try:
            conn = data.get('connection')
            self.connected = conn
            self.connection_state_signal.emit(conn)
        except KeyError:
            logger.debug('Connection was not available yet for calc.')
        try:
            val = data.get('value')
            self.value = val
            if val is not None:
                self.new_value_signal[type(val)].emit(val)
        except KeyError:
            logger.debug('Value was not available yet for calc.')

    def close(self):
        self._calc_thread.requestInterruption()


class CalculationPlugin(PyDMPlugin):
    protocol = "calc"
    connection_class = Connection

    @staticmethod
    def get_connection_id(channel):
        address = PyDMPlugin.get_address(channel)

        try:
            config = json.loads(address)
            jsonschema.validate(config, CALC_ADDRESS_SCHEMA)
        except:
            try:
                jsonschema.validate(config, CALC_ADDRESS_MINIMUM_SCHEMA)
            except:
                msg = "Invalid configuration for CalcPlugin connection. %s"
                logger.exception(msg, address)
                raise ValueError("Name is a required field for calc plugin")

        name = config['name']
        return name
