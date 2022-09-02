import logging
import numpy as np

from p4p.client.thread import Context, Disconnected
from p4p.wrapper import Value
from .pva_codec import decompress
from pydm.data_plugins import is_read_only
from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection
from pydm.widgets.channel import PyDMChannel
from qtpy.QtCore import QObject, Qt
from typing import Optional

logger = logging.getLogger(__name__)


class Connection(PyDMConnection):

    def __init__(self, channel: PyDMChannel, address: str,
                 protocol: Optional[str] = None, parent: Optional[QObject] = None):
        """
        Manages the connection to a channel using the P4P library. A given channel can have multiple listeners.

        Parameters
        ----------
        channel : PyDMChannel
            The channel that this connection is connected to.
        address : str
             The address of the PV.
        protocol : str, optional
             The protocol prepended to the address.
        parent : QObject, optional
             The parent object of this connection.
        """
        super().__init__(channel, address, protocol, parent)
        self._connected = False
        self.monitor = P4PPlugin.context.monitor(name=address,
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
        self._upper_alarm_limit = None
        self._lower_alarm_limit = None
        self._upper_warning_limit = None
        self._lower_warning_limit = None
        self._timestamp = None

    def clear_cache(self) -> None:
        """ Clear out all the stored values of this connection. """
        self._value = None
        self._severity = None
        self._precision = None
        self._enum_strs = None
        self._units = None
        self._upper_ctrl_limit = None
        self._lower_ctrl_limit = None
        self._upper_alarm_limit = None
        self._lower_alarm_limit = None
        self._upper_warning_limit = None
        self._lower_warning_limit = None
        self._timestamp = None

    def send_new_value(self, value: Value) -> None:
        """ Callback invoked whenever a new value is received by our monitor. Emits signals based on values changed. """
        if isinstance(value, Disconnected):
            self._connected = False
            self.clear_cache()
            self.connection_state_signal.emit(False)
        else:
            if not self._connected:
                self._connected = True
                self.connection_state_signal.emit(True)
                # Note that there is no way to get the actual write access value from p4p, so defaulting to True for now
                self.write_access_signal.emit(True)

            self._value = value
            for changed_value in value.changedSet():
                if changed_value == 'value':
                    new_value = value.value
                    if new_value is not None:
                        if isinstance(new_value, np.ndarray):
                            if 'NTNDArray' in value.getID():
                                new_value = decompress(value)
                            self.new_value_signal[np.ndarray].emit(new_value)
                        elif isinstance(new_value, list):
                            self.new_value_signal[np.ndarray].emit(np.array(new_value))
                        elif isinstance(new_value, float):
                            self.new_value_signal[float].emit(new_value)
                        elif isinstance(new_value, int):
                            self.new_value_signal[int].emit(new_value)
                        elif isinstance(new_value, str):
                            self.new_value_signal[str].emit(new_value)
                        else:
                            raise ValueError(f'No matching signal for value: {new_value} with type: {type(new_value)}')
                # Sometimes unchanged control variables appear to be returned with value changes, so checking against
                # stored values to avoid sending misleading signals. Will revisit on data plugin changes.
                elif changed_value == 'alarm.severity' and value.alarm.severity != self._severity:
                    self._severity = value.alarm.severity
                    self.new_severity_signal.emit(value.alarm.severity)
                elif changed_value == 'display.precision' and value.display.precision != self._precision:
                    self._precision = value.display.precision
                    self.prec_signal.emit(value.display.precision)
                elif changed_value == 'display.units' and value.display.units != self._units:
                    self._units = value.display.units
                    self.unit_signal.emit(value.display.units)
                elif changed_value == 'control.limitLow' and value.control.limitLow != self._lower_ctrl_limit:
                    self._lower_ctrl_limit = value.control.limitLow
                    self.lower_ctrl_limit_signal.emit(value.control.limitLow)
                elif changed_value == 'control.limitHigh' and value.control.limitHigh != self._upper_ctrl_limit:
                    self._upper_ctrl_limit = value.control.limitHigh
                    self.upper_ctrl_limit_signal.emit(value.control.limitHigh)
                elif changed_value == 'valueAlarm.highAlarmLimit' and \
                        value.valueAlarm.highAlarmLimit != self._upper_alarm_limit:
                    self._upper_alarm_limit = value.valueAlarm.highAlarmLimit
                    self.upper_alarm_limit_signal.emit(value.valueAlarm.highAlarmLimit)
                elif changed_value == 'valueAlarm.lowAlarmLimit' and \
                        value.valueAlarm.lowAlarmLimit != self._lower_alarm_limit:
                    self._lower_alarm_limit = value.valueAlarm.lowAlarmLimit
                    self.lower_alarm_limit_signal.emit(value.valueAlarm.lowAlarmLimit)
                elif changed_value == 'valueAlarm.highWarningLimit' and \
                        value.valueAlarm.highWarningLimit != self._upper_warning_limit:
                    self._upper_warning_limit = value.valueAlarm.highWarningLimit
                    self.upper_warning_limit_signal.emit(value.valueAlarm.highWarningLimit)
                elif changed_value == 'valueAlarm.lowWarningLimit' and \
                        value.valueAlarm.lowWarningLimit != self._lower_warning_limit:
                    self._lower_warning_limit = value.valueAlarm.lowWarningLimit
                    self.lower_warning_limit_signal.emit(value.valueAlarm.lowWarningLimit)
                elif changed_value == 'timeStamp.secondsPastEpoch' and \
                        value.timeStamp.secondsPastEpoch != self._timestamp:
                    self._timestamp = value.timeStamp.secondsPastEpoch
                    self.timestamp_signal.emit(value.timeStamp.secondsPastEpoch)

    def put_value(self, value):
        """ Write a value to the PV """
        if is_read_only():
            logger.warning(f'PyDM read-only mode is enabled, could not write value: {value} to {self.address}')
            return

        try:
            P4PPlugin.context.put(self.monitor.name, value)
        except Exception as e:
            logger.error(f"Unable to put value: {value} to channel {self.monitor.name}: {e}")

    def add_listener(self, channel: PyDMChannel):
        """
        Adds a listener to this connection, connecting the appropriate signals/slots to the input PyDMChannel.

        Parameters
        ----------
        channel : PyDMChannel
            The channel that will be listening to any changes from this connection
        """
        super().add_listener(channel)
        if self.monitor is not None and self._connected:
            # Adding a listener to an already connected PV. Manually send the signals indicating the PV is
            # connected, and what the last known values were.
            self.connection_state_signal.emit(True)
            self.write_access_signal.emit(True)
            value_to_send = self._value
            self.clear_cache()
            if value_to_send is not None:
                self.send_new_value(value_to_send)

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
        """ Closes out this connection. """
        self.monitor.close()
        super().close()


class P4PPlugin(PyDMPlugin):
    # NOTE: protocol is intentionally "None" to keep this plugin from getting directly imported.
    # If this plugin is chosen as the One True PVA Plugin in pva_plugin.py, the protocol will
    # be properly set before it is used.
    protocol = None
    connection_class = Connection
    context = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if P4PPlugin.context is None:
            # Create the p4p pva context for all connections to use
            context = Context('pva', nt=False)  # Disable automatic value unwrapping
            P4PPlugin.context = context
