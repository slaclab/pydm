import logging
import numpy as np

from p4p.client.thread import Context, Disconnected
from p4p.wrapper import Value
from qtpy.QtCore import Slot, Qt
from pydm.data_plugins import is_read_only
from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection
from typing import Set
from .pva_codec import decompress


logger = logging.getLogger(__name__)


class PVAContext(object):
    """ Singleton class responsible for holding the p4p pva context. """
    __instance = None

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        self.context = Context('pva', maxsize=2, nt=False)

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
        self.add_listener(channel)
        self._value = None
        self._severity = None
        self._precision = None
        self._enum_strs = None
        self._units = None
        self._upper_ctrl_limit = None
        self._lower_ctrl_limit = None

    def clear_cache(self):
        self._value = None
        self._severity = None
        self._precision = None
        self._enum_strs = None
        self._units = None
        self._upper_ctrl_limit = None
        self._lower_ctrl_limit = None

#{'valueAlarm.active', 'valueAlarm.highWarningLimit', 'control.limitHigh', 'value', 'valueAlarm.lowAlarmSeverity', 'valueAlarm.lowWarningSeverity', 'alarm.message',
    # 'display.limitLow', 'display.limitHigh', 'valueAlarm.hysteresis', 'valueAlarm.highAlarmSeverity', 'alarm', 'alarm.severity', 'timeStamp.nanoseconds', 'control.limitLow',
    # 'timeStamp.secondsPastEpoch', 'display.form.choices', 'valueAlarm.highWarningSeverity', 'control', 'timeStamp.userTag', 'timeStamp', 'display.form', 'control.minStep',
    # 'display', 'display.form.index', 'alarm.status', 'valueAlarm.highAlarmLimit', 'display.precision', 'valueAlarm.lowAlarmLimit', 'valueAlarm.lowWarningLimit', 'display.description',
    # 'display.units', 'valueAlarm'}



    def send_new_value(self, value: Value):
        if isinstance(value, Disconnected):
            self._connected = False
            self.clear_cache()
            self.connection_state_signal.emit(False)
        else:
            if not self._connected:
                self._connected = True
                self.connection_state_signal.emit(True)

            self.write_access_signal.emit(True)  # TODO: This should probably come from somewhere?

            for changed_value in value.changedSet():
                if changed_value == 'value' and not np.array_equal(value.value, self._value):
                    if 'NTNDArray' in value.getID():
                        self.preprocess_array(value)
                    new_value = value.value
                    if new_value is not None and not np.array_equal(new_value, self._value):
                        self._value = new_value
                        if isinstance(new_value, np.ndarray):
                            self.new_value_signal[np.ndarray].emit(new_value)
                        elif isinstance(new_value, float):
                            self.new_value_signal[float].emit(new_value)
                        elif isinstance(new_value, int):
                            self.new_value_signal[int].emit(new_value)
                        elif isinstance(new_value, str):
                            self.new_value_signal[str].emit(new_value)
                        else:
                            raise ValueError(f'No matching signal for value: {value} with type: {type(value)}')
                elif changed_value == 'alarm.severity' and value.alarm.severity != self._severity:
                    self._severity = value.alarm.severity
                    print(f'sending new severity: {value.alarm.severity}')
                    self.new_severity_signal.emit(value.alarm.severity)
                elif changed_value == 'display.precision' and value.display.precision != self._precision:
                    self._precision = value.display.precision
                    self.prec_signal.emit(value.display.precision)
 #               elif changed_value == 'display.form.choices' and value.display.form.choices != self._enum_strs: # TODO: Is this actually the same thing?
 #                   self._enum_strs = value.display.form.choices
 #                   self.enum_strings_signal.emit(value.display.form.choices)
                elif changed_value == 'display.units' and value.display.units != self._units:
                    self._units = value.display.units
                    self.unit_signal.emit(value.display.units)
                elif changed_value == 'control.limitLow' and value.control.limitLow != self._lower_ctrl_limit:
                    self._lower_ctrl_limit = value.control.limitLow
                    self.lower_ctrl_limit_signal.emit(value.control.limitLow)
                elif changed_value == 'control.limitHigh' and value.control.limitHigh != self._upper_ctrl_limit:
                    self._upper_ctrl_limit = value.control.limitHigh
                    self.upper_ctrl_limit_signal.emit(value.control.limitHigh)

    def preprocess_array(self, value):
        decompress(value)
#        try:
#            decompress(value)
#        except Exception as e:
#            print(f'Could not decompress data: exception: {e}')


    def put_value(self, value):
        if is_read_only():
            return

        # Check write access?
        try:
            PVAContext().context.put(self.monitor.name, value)
        except Exception as e:
            logger.exception(f"Unable to put value: {value} to channel: {self.monitor.name}  Exception: {e}")

    def add_listener(self, channel):
        print(f'Adding listener for channel: {channel}')
        super().add_listener(channel)

        if channel.value_signal is not None:
            try:
                channel.value_signal[str].connect(self.put_value, Qt.QueuedConnection)
            except KeyError:
                pass
            try:
                channel.value_signal[int].connect(self.put_value, Qt.QueuedConnection)
            except KeyError:
                pass
            try:
                channel.value_signal[float].connect(self.put_value, Qt.QueuedConnection)
            except KeyError:
                pass
            try:
                channel.value_signal[np.ndarray].connect(self.put_value, Qt.QueuedConnection)
            except KeyError:
                pass

    def close(self):
        self.monitor.close()
        # TODO: Anything else?
        super().close()


class P4PPlugin(PyDMPlugin):
    # NOTE: protocol is intentionally "None" to keep this plugin from getting directly imported.
    # If this plugin is chosen as the One True PVA Plugin in pva_plugin.py, the protocol will
    # be properly set before it is used.
    protocol = None
    connection_class = Connection
