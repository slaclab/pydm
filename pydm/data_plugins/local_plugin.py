"""
Plugin to allow users to arbitrarily connect python object attributes to widget
channels. This handles the polling tasks to update the gui.
"""
import inspect
import numpy as np
from qtpy.QtWidgets import QWidget
from qtpy.QtCore import Slot, Qt, QCoreApplication, QTimer
from pydm.data_plugins.plugin import PyDMPlugin, PyDMConnection


class LocalPlugin(PyDMPlugin):
    """
    Plugin that only exists in a local space to connect to a local object.

    The user must:
    1. self-define protocol to talk to their object
    2. make sure all attributes and function calls exist and work
    3. make sure their obj code is not slow or resource-intensive
    4. call add_widgets or include widgets in the constructor that already
       have valid channel addresses with this new protocol

    If refresh=0 (passive refresh) it is up to the user to call
    connect_to_update to connect a signal to the "update" connection slot to
    manage updates.

    Some examples:

    LocalPlugin("motor", motor_obj, [widget1, widget2])
    motor_obj.field, default refresh    -> "motor://field"
    motor_obj.pvname, default refresh   -> "motor://pvname"
    motor_obj.wm(), refresh every 1 sec -> "motor://wm()?t=1"
    motor_obj.wm(), with no refresh:    -> "motor://wm()?t=0"

    LocalPlugin("ipm", ipm_obj, [widget3])
    ipm_obj.ch(1), default refresh      -> "ipm://ch(1)"
    ipm_obj.ch(2), refresh every 2 sec  -> "ipm://ch(2)?t=2"

    Note that function args will be casted as floats or strings for simplicity.
    """

    def __init__(self, protocol, obj, widgets=[], refresh=1.0):
        """
        :param protocol: custom local protocol
                         only valid for input widgets and their children
        :type protocol:  str
        :param obj: object to use for this plugin
        :type obj:  object
        :param widgets: widgets to connect to obj
        :type widgets:  list of QWidget
        :param refresh: default seconds to wait before checking new values
                        refresh=0 means no auto-refresh by default
        :type refresh:  float or int
        """
        super(LocalPlugin, self).__init__()
        app = QCoreApplication.instance()
        standard_protocol = app.plugins.keys()
        if protocol in standard_protocol:
            err = "Protocol {} invalid, same as a standard protocol"
            raise Exception(err.format(protocol))
        self.base_protocol = protocol
        self.protocol = protocol + "://"
        self.connection_class = connection_class_factory(obj, refresh)
        self.add_widgets(widgets)

    def add_widgets(self, widgets):
        """
        Apply LocalPlugin to additional widgets.

        :param widgets: Additional widgets to connect to obj
        :type widgets:  list of QWidget
        """
        target_widgets = []
        for widget in widgets:
            target_widgets.append(widget)
            target_widgets.extend(widget.findChildren(QWidget))
        for widget in target_widgets:
            if hasattr(widget, "channels"):
                for channel in widget.channels():
                    channel_protocol = str(channel.address).split("://")[0]
                    if self.base_protocol == channel_protocol:
                        self.add_connection(channel)

    def connect_to_update(self, address, signal):
        """
        Connect signal to the update slot of the connection associated with
        address. This allows a user to manage update timings without polling.

        :param address: Everything after the protocol:// portion of the
                        channel.address string.
        :type address:  str
        :param signal: User signal to connect to the update slot.
        :type signal:  Signal()
        """
        try:
            connection = self.connections[address]
        except KeyError:
            err = "No connectino with address {} found!"
            raise KeyError(err.format(address))
        signal.connect(connection.update)


def connection_class_factory(obj, refresh=1.0):
    """
    Create a Connection class for connecting to fields of an object.

    :param obj: object to use as the data source
    :type obj:  object
    :param refresh: default refresh rate for fields
    :type refresh:  float
    """

    class Connection(PyDMConnection):
        """
        Class that manages object attribute access.
        """

        def __init__(self, channel, address, parent=None):
            """
            Parse address, apply options, and add the first listener.
            Start polling the field/method if applicable.

            :param channel: :class:`PyDMChannel` object as the first listener.
            :type channel:  :class:`PyDMChannel`
            :param address: Name of the field to check, plus additional args.
                            Currently supported args are t, the refresh rate,
                            e.g. field?t=3, func(name)?t=4, are both valid.
                            Additional args must be primitives.
            :type address:  QString
            :param parent: PyQt widget that this widget is inside of.
            :type parent:  QWidget
            """
            super(Connection, self).__init__(channel, address, parent)
            self.obj = obj
            self.refresh = refresh
            # remove all whitespace from address and convert to str
            address = "".join(str(address).split())
            # separate attr/func calls from settings (opts)
            parts = address.split("?")
            # call will be something like "value" or "func(3,key=lock)"
            call = parts[0]
            call_elems = call.split("(")
            # attr is the attribute that we look for in obj
            self.attr = call_elems[0]
            # now we check if this is supposed to be a function call
            if len(call_elems) > 1:
                # take everything except the )
                args_string = call_elems[1][:-1]
                args = args_string.split(",")
                self.args = []
                self.kwargs = {}
                for arg in args:
                    if len(arg) > 0:
                        # determine if *args or **kwargs for each
                        k_split = arg.split("=")
                        if len(k_split) > 1:
                            # **kwargs
                            key = k_split[0]
                            value = k_split[1]
                            try:
                                value = float(value)
                            except:
                                pass
                            self.kwargs[key] = value
                        else:
                            # *args
                            try:
                                value = float(arg)
                            except:
                                if arg == "''" or arg == '""':
                                    value = ""
                                else:
                                    value = arg
                            self.args.append(value)
            if len(parts) > 1:
                # opts will be something like t=4,gds=text
                opts = parts[1]
                all_opts = opts.split(",")
                for o in all_opts:
                    fld, value = o.split("=")
                    if fld == "t":
                        self.refresh = float(value)
            try:
                spec = inspect.getargspec(getattr(obj, self.attr))
                self.nargs = len(spec.args) - 1
            except:
                self.nargs = None
            if self.refresh > 0:
                self.update_timer = QTimer()
                self.update_timer.timeout.connect(self.update)
                self.update_timer.start(1000.0 * self.refresh)
            self.add_listener(channel)

        def get_value(self):
            """
            Return the current value of this connection.

            :rtyp: Can be any type, user defined.
            """
            attr = getattr(self.obj, self.attr)
            try:
                args = self.args
                kwargs = self.kwargs
                return attr(*args, **kwargs)
            except AttributeError:
                return attr

        @Slot()
        def update(self):
            """
            Get a new value from the object and send it to all listeners.
            If an exception was thrown, send a disconnected signal.
            """
            try:
                value = self.get_value()
            except:
                self.send_connection_state(False)
                return
            self.send_connection_state(True)
            self.send_new_value(value)

        def send_new_value(self, value=None):
            """
            Send a value to every channel listening for our obj.

            :param value: Value to emit to our listeners.
            :type value:  int, float, str, or np.ndarray.
            """
            if isinstance(value, np.generic):
                value = np.asscalar(value)
            if isinstance(value, np.ndarray):
                self.new_waveform_signal.emit(value)
            elif isinstance(value, (int, float, str)):
                self.new_value_signal[type(value)].emit(value)
            else:
                self.new_value_signal[str].emit(str(value))

        def send_connection_state(self, conn=None):
            """
            Send an update on our connection state to every listener.

            :param conn: True if attribute exists, False otherwise.
            :type conn:  bool
            """
            self.connection_state_signal.emit(conn)

        def is_connected(self):
            """
            Return True if we can get a value.
            """
            try:
                self.get_value()
                return True
            except:
                return False

        @Slot(int)
        @Slot(float)
        @Slot(str)
        @Slot(np.ndarray)
        def put_value(self, value):
            """
            Set our object attribute's value. If the attribute is a function,
            we will execute it.

            :param value: The value we'd like to set in our object.
            :type value:  int, float, str, or np.ndarray.
            """
            # Field: replace value
            if self.nargs is None:
                try:
                    setattr(obj, self.attr, value)
                except:
                    return
            # Function of zero arguments: call function
            elif self.nargs == 0:
                try:
                    getattr(obj, self.attr)()
                except:
                    return
            # Function of one argument: call function with value
            elif self.nargs == 1:
                try:
                    getattr(obj, self.attr)(value)
                except:
                    return
            # Function with many arguments: distribute arguments to args
            elif self.nargs > 1:
                try:
                    getattr(obj, self.attr)(*value)
                except:
                    return
            else:
                return
            # If we set a value, update now.
            self.update()

        @Slot(np.ndarray)
        def put_waveform(self, value):
            """
            This is a deprecated function kept temporarily for compatibility
            with old code.

            :param value: The waveform value we'd like to put to our attr.
            :type value:  np.ndarray
            """
            self.put_value(value)

        def add_listener(self, channel):
            """
            Connect a channel's signals and slots with this object's signals
            and slots.

            :param channel: The channel to connect.
            :type channel:  :class:`PyDMChannel`
            """
            super(Connection, self).add_listener(channel)
            if self.is_connected():
                self.send_connection_state(conn=True)
                self.update()
            try:
                channel.value_signal[str].connect(self.put_value, Qt.QueuedConnection)
                channel.value_signal[int].connect(self.put_value, Qt.QueuedConnection)
                channel.value_signal[float].connect(self.put_value, Qt.QueuedConnection)
            except:
                pass
            try:
                channel.waveform_signal.connect(self.put_value, Qt.QueuedConnection)
            except:
                pass

    return Connection
