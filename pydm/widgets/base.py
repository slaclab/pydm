import weakref
import logging
import functools
import json
import numpy as np
from qtpy.QtWidgets import QApplication, QMenu, QGraphicsOpacityEffect, QToolTip
from qtpy.QtGui import QCursor
from qtpy.QtCore import Qt, QEvent, Signal, Slot, Property
from .channel import PyDMChannel
from .. import data_plugins
from .. import tools
from ..utilities import is_qt_designer, remove_protocol
from .rules import RulesDispatcher

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

logger = logging.getLogger(__name__)


def is_channel_valid(channel):
    """
    Verify if a channel string is valid.
    For now a valid channel is a channel in which:
    - It is not None
    - It is not an empty string

    Parameters
    ----------
    channel : str
        The channel value

    Returns
    -------
    valid : bool
        Returns True if the channel is valid, False otherwise.
    """
    return channel is not None and channel != ""


def only_if_channel_set(fcn):
    """Decorator to avoid executing a method if a channel is not valid or configured."""

    @functools.wraps(fcn)
    def wrapper(self, *args, **kwargs):
        if is_channel_valid(self._channel):
            return fcn(self, *args, **kwargs)
        else:
            return

    return wrapper


def widget_destroyed(channels, widget):
    """
    Callback invoked when the Widget is destroyed.
    This method is used to ensure that the channels are disconnected.

    Parameters
    ----------
    channels : list
        A list of PyDMChannel objects that this widget uses.
    widget : weakref
        Weakref to the widget.
    """
    chs = channels()
    if chs:
        for ch in chs:
            if ch:
                ch.disconnect(destroying=True)

    RulesDispatcher().unregister(widget)


class PyDMPrimitiveWidget(object):
    """
    Primitive class that determines that a given widget is a PyDMWidget.
    All Widget classes from PyDMWidget will be True for
    isinstance(obj, PyDMPrimitiveWidget)
    """
    DEFAULT_RULE_PROPERTY = "Visible"
    RULE_PROPERTIES = {
        'Enable': ['setEnabled', bool],
        'Visible': ['setVisible', bool],
        'Opacity': ['set_opacity', float]
    }

    def __init__(self):
        self._rules = None
        self._opacity = 1.0

    def opacity(self):
        """
        Float value between 0 and 1 representing the opacity of the widget
        where 0 means transparent.

        Returns
        -------
        opacity : float
        """
        return self._opacity

    def set_opacity(self, val):
        """
        Float value between 0 and 1 representing the opacity of the widget
        where 0 means transparent.

        Parameters
        ----------
        val : float
            The new value for the opacity
        """
        op = QGraphicsOpacityEffect(self)
        if val > 1:
            val = 1
        elif val < 0:
            val = 0
        self._opacity = val
        op.setOpacity(val)  # 0 to 1 will cause the fade effect to kick in
        self.setGraphicsEffect(op)
        self.setAutoFillBackground(True)


    @Slot(dict)
    def rule_evaluated(self, payload):
        """
        Callback called when a rule has a new value for a property.

        Parameters
        ----------
        payload : dict
            Dictionary containing the rule name, the property to be set and the
            new value.

        Returns
        -------
        None
        """
        name = payload.get('name', '')
        prop = payload.get('property', '')
        value = payload.get('value', None)

        if prop not in self.RULE_PROPERTIES:
            logger.error('Error at Rule: %s. %s is not part of this widget properties.',
                         name, prop)
            return

        method_name, data_type = self.RULE_PROPERTIES[prop]
        method = getattr(self, method_name)
        method(value)

    @Property(str, designable=False)
    def rules(self):
        """
        JSON-formatted list of dictionaries, with rules for the widget.

        Returns
        -------
        str
        """
        return self._rules

    @rules.setter
    def rules(self, new_rules):
        """
        JSON-formatted list of dictionaries, with rules for the widget.

        Parameters
        ----------
        new_rules : str

        Returns
        -------
        None
        """
        if new_rules != self._rules:
            self._rules = new_rules
            try:
                rules_list = json.loads(self._rules)
                RulesDispatcher().register(self, rules_list)
            except JSONDecodeError as ex:
                logger.exception('Invalid format for Rules')


class PyDMWidget(PyDMPrimitiveWidget):
    """
    PyDM base class for Read-Only widgets.
    This class implements all the functions of connection, alarm
    handling and more.

    Parameters
    ----------
    init_channel : str, optional
        The channel to be used by the widget.

    """
    # Alarm types
    ALARM_NONE = 0
    ALARM_MINOR = 1
    ALARM_MAJOR = 2
    ALARM_INVALID = 3
    ALARM_DISCONNECTED = 4

    def __init__(self, init_channel=None):
        super(PyDMWidget, self).__init__()

        if not all([prop in PyDMPrimitiveWidget.RULE_PROPERTIES for prop in
                    ['Position - X', 'Position - Y']]):
            PyDMWidget.RULE_PROPERTIES = PyDMPrimitiveWidget.RULE_PROPERTIES.copy()
            PyDMWidget.RULE_PROPERTIES.update(
                {'Position - X': ['setX', int],
                 'Position - Y': ['setY', int]})

        self.app = QApplication.instance()
        self._connected = True
        self._channel = None
        self._channels = list()
        self._show_units = False
        self._alarm_sensitive_content = False
        self._alarm_sensitive_border = True
        self._alarm_state = self.ALARM_NONE
        self._tooltip = None

        self._precision_from_pv = True
        self._prec = 0
        self._unit = ""

        self._upper_ctrl_limit = None
        self._lower_ctrl_limit = None

        self.enum_strings = None
        self.format_string = "{}"

        self.value = None
        self.channeltype = None
        self.subtype = None

        # If this label is inside a PyDMApplication (not Designer) start it in
        # the disconnected state.
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.contextMenuEvent = self.open_context_menu
        self.channel = init_channel
        if not is_qt_designer():
            self._connected = False
            self.alarmSeverityChanged(self.ALARM_DISCONNECTED)
            self.check_enable_state()

        self.destroyed.connect(
            functools.partial(widget_destroyed, self.channels, weakref.ref(self))
        )

    def widget_ctx_menu(self):
        """
        Fetch the Widget specific context menu which will be populated with additional tools by `assemble_tools_menu`.

        Returns
        -------
        QMenu or None
            If the return of this method is None a new QMenu will be created by `assemble_tools_menu`.
        """
        return None

    def generate_context_menu(self):
        """
        Generates the custom context menu, and populates it with any external
        tools that have been loaded.  PyDMWidget subclasses should override
        this method (after calling superclass implementation) to add the menu.

        Returns
        -------
        QMenu
        """
        menu = self.widget_ctx_menu()
        if menu is None:
            menu = QMenu(parent=self)

        kwargs = {'channels': self.channels_for_tools(), 'sender': self}
        tools.assemble_tools_menu(menu, widget_only=True, **kwargs)
        return menu

    def open_context_menu(self, ev):
        """
        Handler for when the Default Context Menu is requested.

        Parameters
        ----------
        ev : QEvent
        """
        menu = self.generate_context_menu()
        action = menu.exec_(self.mapToGlobal(ev.pos()))
        del menu

    def init_for_designer(self):
        """
        Method called after the constructor to tweak configurations for
        when using the widget with the Qt Designer
        """
        self._connected = True

    def connection_changed(self, connected):
        """
        Callback invoked when the connection state of the Channel is changed.
        This callback acts on the connection state to enable/disable the widget
        and also trigger the change on alarm severity to ALARM_DISCONNECTED.

        Parameters
        ----------
        connected : int
            When this value is 0 the channel is disconnected, 1 otherwise.
        """
        self._connected = connected
        self.check_enable_state()
        if not connected:
            self.alarmSeverityChanged(self.ALARM_DISCONNECTED)
        else:
            self.alarmSeverityChanged(self.ALARM_NONE)

    def value_changed(self, new_val):
        """
        Callback invoked when the Channel value is changed.

        Parameters
        ----------
        new_val : str, int, float, bool or np.ndarray
            The new value from the channel. The type depends on the channel.
        """
        self.value = new_val
        self.channeltype = type(self.value)
        if self.channeltype == np.ndarray:
            self.subtype = self.value.dtype.type
        else:
            try:
                if self.channeltype == unicode:
                    # For Python 2.7, set the the channel type to str instead of unicode
                    self.channeltype = str
            except NameError:
                pass

        self.update_format_string()

    @Property(int, designable=False)
    def alarmSeverity(self):
        return self._alarm_state

    @alarmSeverity.setter
    def alarmSeverity(self, new_severity):
        if self._alarm_state != new_severity:
            self._alarm_state = new_severity

    def alarm_severity_changed(self, new_alarm_severity):
        """
        Callback invoked when the Channel alarm severity is changed.
        This callback is not processed if the widget has no channel
        associated with it.
        This callback handles the composition of the stylesheet to be
        applied and the call
        to update to redraw the widget with the needed changes for the
        new state.

        Parameters
        ----------
        new_alarm_severity : int
            The new severity where 0 = NO_ALARM, 1 = MINOR, 2 = MAJOR
            and 3 = INVALID
        """
        # 0 = NO_ALARM, 1 = MINOR, 2 = MAJOR, 3 = INVALID
        if not self._channel:
            self._alarm_state = PyDMWidget.ALARM_NONE
        else:
            self._alarm_state = new_alarm_severity
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def enum_strings_changed(self, new_enum_strings):
        """
        Callback invoked when the Channel has new enum values.
        This callback also triggers a value_changed call so the
        new enum values to be broadcasted

        Parameters
        ----------
        new_enum_strings : tuple
            The new list of values
        """
        if new_enum_strings != self.enum_strings:
            self.enum_strings = new_enum_strings
            self.value_changed(self.value)

    def eventFilter(self, obj, event):
        """
        EventFilter to redirect "middle click" to :meth:`.show_address_tooltip`
        """
        # Override the eventFilter to capture all middle mouse button events,
        # and show a tooltip if needed.
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.MiddleButton:
                self.show_address_tooltip(event)
                return True
        return False

    def show_address_tooltip(self, event):
        """
        Show the PyDMTooltip and copy address to clipboard

        This is intended to replicate the behavior of the "middle click" from
        EDM. If the QWidget does not have a valid PyDMChannel nothing will be
        displayed
        """
        if not len(self._channels):
            logger.warning("Object %r has no PyDM Channels", self)
            return
        addr = self.channels()[0].address
        QToolTip.showText(event.globalPos(), addr)
        # If the address has a protocol, strip it out before putting it on the
        # clipboard.
        copy_text = remove_protocol(addr)

        clipboard = QApplication.clipboard()
        clipboard.setText(copy_text)
        event = QEvent(QEvent.Clipboard)
        self.app.sendEvent(clipboard, event)

    def unit_changed(self, new_unit):
        """
        Callback invoked when the Channel has new unit value.
        This callback also triggers an update_format_string call so the
        new unit value is considered if ```showUnits``` is set.

        Parameters
        ----------
        new_unit : str
            The new unit
        """
        if self._unit != new_unit:
            self._unit = new_unit
            if self.value is not None:
                self.value_changed(self.value)

    def precision_changed(self, new_precision):
        """
        Callback invoked when the Channel has new precision value.
        This callback also triggers an update_format_string call so the
        new precision value is considered.

        Parameters
        ----------
        new_precison : int or float
            The new precision value
        """
        if self._precision_from_pv and new_precision != self._prec:
            self._prec = new_precision
            if self.value is not None:
                self.value_changed(self.value)

    def ctrl_limit_changed(self, which, new_limit):
        """
        Callback invoked when the Channel receives new control limit
        values.

        Parameters
        ----------
        which : str
            Which control limit was changed. "UPPER" or "LOWER"
        new_limit : float
            New value for the control limit
        """
        if which == "UPPER":
            self._upper_ctrl_limit = new_limit
        else:
            self._lower_ctrl_limit = new_limit

    @Slot(bool)
    def connectionStateChanged(self, connected):
        """
        PyQT Slot for changes on the Connection State of the Channel
        This slot sends the connection state to the ```connection_changed```
        callback.

        Parameters
        ----------
        connected : bool
        """
        # false = disconnected, true = connected
        self.connection_changed(connected)

    @Slot(int)
    @Slot(float)
    @Slot(str)
    @Slot(bool)
    @Slot(np.ndarray)
    def channelValueChanged(self, new_val):
        """
        PyQT Slot for changes on the Value of the Channel
        This slot sends the value to the ```value_changed``` callback.

        Parameters
        ----------
        new_val : int, float, str, bool or np.ndarray
        """
        self.value_changed(new_val)

    @Slot(int)
    def alarmSeverityChanged(self, new_alarm_severity):
        """
        PyQT Slot for changes on the Alarm Severity of the Channel
        This slot sends the severity value to the
        ```alarm_severity_changed``` callback.

        Parameters
        ----------
        new_alarm_severity : int
        """
        self.alarm_severity_changed(new_alarm_severity)

    @Slot(tuple)
    def enumStringsChanged(self, new_enum_strings):
        """
        PyQT Slot for changes on the string values of the Channel
        This slot sends the new strings to the
        ```enum_strings_changed``` callback.

        Parameters
        ----------
        new_enum_strings : tuple
        """
        self.enum_strings_changed(new_enum_strings)

    @Slot(str)
    def unitChanged(self, new_unit):
        """
        PyQT Slot for changes on the unit of the Channel
        This slot sends the new unit string to the
        ```unit_changed``` callback.

        Parameters
        ----------
        new_unit : str
        """
        self.unit_changed(new_unit)

    @Slot(int)
    @Slot(float)
    def precisionChanged(self, new_prec):
        """
        PyQT Slot for changes on the precision of the Channel
        This slot sends the new precision value to the
        ```precision_changed``` callback.

        Parameters
        ----------
        new_prec : int or float
        """
        self.precision_changed(new_prec)

    @Slot(float)
    def upperCtrlLimitChanged(self, new_limit):
        """
        PyQT Slot for changes on the upper control limit value of the Channel
        This slot sends the new limit value to the
        ```ctrl_limit_changed``` callback.

        Parameters
        ----------
        new_limit : float
        """
        self.ctrl_limit_changed("UPPER", new_limit)

    @Slot(float)
    def lowerCtrlLimitChanged(self, new_limit):
        """
        PyQT Slot for changes on the lower control limit value of the Channel
        This slot sends the new limit value to the
        ```ctrl_limit_changed``` callback.

        Parameters
        ----------
        new_limit : float
        """
        self.ctrl_limit_changed("LOWER", new_limit)

    @Slot()
    def force_redraw(self):
        """
        PyQT Slot to force a redraw on the widget.

        """
        self.update()

    def setX(self, new_x):
        """
        Set the X position of the Widget on the screen.

        Parameters
        ----------
        new_x : int
            The new X position

        Returns
        -------
        None
        """
        point = self.pos()
        point.setX(new_x)
        self.move(point)

    def setY(self, new_y):
        """
        Set the Y position of the Widget on the screen.

        Parameters
        ----------
        new_y : int
            The new Y position

        Returns
        -------
        None
        """
        point = self.pos()
        point.setY(new_y)
        self.move(point)

    @Property(bool)
    def alarmSensitiveContent(self):
        """
        Whether or not the content color changes when alarm severity
        changes.

        Returns
        -------
        bool
            True means that the content color will be changed in case of
            alarm severity changes.
        """
        return self._alarm_sensitive_content

    @alarmSensitiveContent.setter
    def alarmSensitiveContent(self, checked):
        """
        Whether or not the content color changes when alarm severity
        changes.

        Parameters
        ----------
        checked : bool
            True means that the content color will be changed in case of
            alarm severity changes.
        """
        self._alarm_sensitive_content = checked
        self.alarm_severity_changed(self._alarm_state)

    @Property(bool)
    def alarmSensitiveBorder(self):
        """
        Whether or not the border color changes when alarm severity changes.

        Returns
        -------
        bool
            True means that the border color will be changed in case of
            alarm severity changes.
        """
        return self._alarm_sensitive_border

    @alarmSensitiveBorder.setter
    def alarmSensitiveBorder(self, checked):
        """
        Whether or not the border color changes when alarm severity
        changes.

        Parameters
        ----------
        checked : bool
            True means that the border color will be changed in case of
            alarm severity changes.
        """
        self._alarm_sensitive_border = checked
        self.alarm_severity_changed(self._alarm_state)

    @Property(bool)
    def precisionFromPV(self):
        """
        A choice whether or not to use the precision given by channel.

        If set to False, the value received will be displayed as is, with
        no modification to the number of displayed significant figures.
        However, if set to True, and the channel specifies a display
        precision, a float or integer channel value will be set to display
        the correct precision. When using an EPICS Channel, the precision
        value corresponds to the PV's PREC field.

        It is also important to note, that if the value of the channel
        is a String, the choice of True or False will have no affect on
        the display.

        Returns
        -------
        precison_from_pv : bool
            True means that the widget will use the precision information
            from the Channel if available.
        """
        return self._precision_from_pv

    @precisionFromPV.setter
    def precisionFromPV(self, value):
        """
        A choice whether or not to use the precision given by channel.

        If set to False, the value received will be displayed as is, with
        no modification to the number of displayed significant figures.
        However, if set to True, and the channel specifies a display
        precision, a float or integer channel value will be set to
        display the correct precision. When using an EPICS Channel, the
        precision value corresponds to the PV's PREC field.

        It is also important to note, that if the value of the channel is
        a String, the choice of True or False will have no affect on the
        display.

        Parameters
        ----------
        value : bool
            True means that the widget will use the precision information
            from the PV if available.
        """
        if self._precision_from_pv != bool(value):
            self._precision_from_pv = value

    @Property(int)
    def precision(self):
        """
        The precision to be used when formatting the output of the PV

        Returns
        -------
        prec : int
            The current precision value
        """
        return self._prec

    @precision.setter
    def precision(self, new_prec):
        """
        The precision to be used when formatting the output of the PV.
        This has no effect when ```precisionFromPV``` is True.

        Parameters
        ----------
        new_prec : int
            The new precision value to use
        """
        # Only allow one to change the property if not getting the precision
        # from the PV
        if self._precision_from_pv:
            return
        if new_prec and self._prec != int(new_prec) and new_prec >= 0:
            self._prec = int(new_prec)
            self.value_changed(self.value)

    @Property(bool)
    def showUnits(self):
        """
        A choice whether or not to show the units given by the channel

        If set to True, the units given in the channel will be displayed
        with the value. If using an EPICS channel, this will automatically
        be linked to the EGU field of the PV.

        Returns
        -------
        show_units : bool
            True means that the unit will be appended to the output value
            format string
        """
        return self._show_units

    @showUnits.setter
    def showUnits(self, show_units):
        """
        A choice whether or not to show the units given by the channel

        If set to True, the units given in the channel will be displayed
        with the value. If using an EPICS channel, this will automatically
        be linked to the EGU field of the PV.

        Paramters
        ---------
        show_units : bool
            True means that the unit will be appended to the output value
            format string
        """
        if self._show_units != show_units:
            self._show_units = show_units
            self.update_format_string()

    @Property(str)
    def channel(self):
        """
        The channel address in use for this widget.

        Returns
        -------
        channel : str
            Channel address
        """
        if self._channel:
            return str(self._channel)
        return None

    @channel.setter
    def channel(self, value):
        """
        The channel address to use for this widget.

        Parameters
        ----------
        value : str
            Channel address
        """
        if self._channel != value:
            # Remove old connections
            for channel in [c for c in self._channels if
                            c.address == self._channel]:
                channel.disconnect()
                self._channels.remove(channel)
            # Load new channel
            self._channel = str(value)
            channel = PyDMChannel(address=self._channel,
                                  connection_slot=self.connectionStateChanged,
                                  value_slot=self.channelValueChanged,
                                  severity_slot=self.alarmSeverityChanged,
                                  enum_strings_slot=self.enumStringsChanged,
                                  unit_slot=self.unitChanged,
                                  prec_slot=self.precisionChanged,
                                  upper_ctrl_limit_slot=self.upperCtrlLimitChanged,
                                  lower_ctrl_limit_slot=self.lowerCtrlLimitChanged,
                                  value_signal=None,
                                  write_access_slot=None)
            # Load writeable channels if our widget requires them. These should
            # not exist on the base PyDMWidget but prevents us from duplicating
            # the method below to only make two more connections
            if hasattr(self, 'writeAccessChanged'):
                channel.write_access_slot = self.writeAccessChanged
            if hasattr(self, 'send_value_signal'):
                channel.value_signal = self.send_value_signal
            # Connect write channels if we have them
            channel.connect()
            self._channels.append(channel)

    def update_format_string(self):
        """
        Reconstruct the format string to be used when representing the
        output value.

        Returns
        -------
        format_string : str
            The format string to be used including or not the precision
            and unit
        """
        self.format_string = "{}"
        if isinstance(self.value, (int, float)):
            self.format_string = "{:." + str(self._prec) + "f}"
        if self._show_units and self._unit != "":
            self.format_string += " {}".format(self._unit)
        return self.format_string

    def restore_original_tooltip(self):
        if self._tooltip is None:
            self._tooltip = self.toolTip()
        return self._tooltip

    @only_if_channel_set
    def check_enable_state(self):
        """
        Checks whether or not the widget should be disable.
        This method also disables the widget and add a Tool Tip
        with the reason why it is disabled.
        """
        status = self._connected
        tooltip = self.restore_original_tooltip()
        if not status:
            if tooltip != '':
                tooltip += '\n'
            tooltip += "PV is disconnected."

        self.setToolTip(tooltip)
        self.setEnabled(status)

    def get_ctrl_limits(self):
        """
        Returns a tuple with the control limits for the channel

        Returns
        -------
        (lower, upper) : tuple
            Lower and Upper control limits
        """
        return self._lower_ctrl_limit, self._upper_ctrl_limit

    def channels(self):
        """
        Returns the channels being used for this Widget.

        Returns
        -------
        channels : list
            List of PyDMChannel objects
        """
        if len(self._channels):
            return self._channels
        else:
            return None

    def channels_for_tools(self):
        """
        Returns a list of channels useful for external tools.
        The default implementation here is just to return
        self.channels(), but some widgets will want to re-implement
        this, especially if they have multiple channels, but only
        one real 'signal' channel.

        Returns
        -------
        list
        """
        return self.channels()


class PyDMWritableWidget(PyDMWidget):
    """
    PyDM base class for Writable widgets.
    This class implements the send_value_signal and also the event filter for write access changes on PVs.

    Parameters
    ----------
    init_channel : str, optional
        The channel to be used by the widget.

    Signals
    -------
    send_value_signal : int, float, str, bool or np.ndarray
        Emitted when the user changes the value
    """

    __Signals__ = ("send_value_signal([int], [float], [str], [bool], [np.ndarray])")

    # Emitted when the user changes the value.
    send_value_signal = Signal([int], [float], [str], [bool], [np.ndarray])

    def __init__(self, init_channel=None):
        self._write_access = False
        super(PyDMWritableWidget, self).__init__(init_channel=init_channel)
        self.app = QApplication.instance()
        # We should  install the Event Filter only if we are running
        # and not at the Designer
        if not is_qt_designer():
            self.installEventFilter(self)

    def init_for_designer(self):
        """
        Method called after the constructor to tweak configurations for
        when using the widget with the Qt Designer
        """
        super(PyDMWritableWidget, self).init_for_designer()
        self._write_access = True

    def eventFilter(self, obj, event):
        """
        Filters events on this object.

        Params
        ------
        object : QObject
            The object that is being handled.
        event : QEvent
            The event that is happening.

        Returns
        -------
        bool
            True to stop the event from being handled further; otherwise
            return false.
        """
        channel = getattr(self, 'channel', None)
        if is_channel_valid(channel):
            status = self._write_access and self._connected

            if event.type() == QEvent.Leave:
                QApplication.restoreOverrideCursor()

            if event.type() == QEvent.Enter and not status:
                QApplication.setOverrideCursor(QCursor(Qt.ForbiddenCursor))

        return PyDMWidget.eventFilter(self, obj, event)

    def write_access_changed(self, new_write_access):
        """
        Callback invoked when the Channel has new write access value.
        This callback calls check_enable_state so it can act on the widget
        enabling or disabling it accordingly

        Parameters
        ----------
        new_write_access : bool
            True if write operations to the channel are allowed.
        """
        self._write_access = new_write_access
        self.check_enable_state()

    @Slot(bool)
    def writeAccessChanged(self, write_access):
        """
        PyQT Slot for changes on the write access value of the Channel
        This slot sends the write access value to the ```write_access_changed``` callback.

        Parameters
        ----------
        write_access : bool
        """
        self.write_access_changed(write_access)

    @only_if_channel_set
    def check_enable_state(self):
        """
        Checks whether or not the widget should be disable.
        This method also disables the widget and add a Tool Tip
        with the reason why it is disabled.
        """
        status = self._write_access and self._connected
        tooltip = self.restore_original_tooltip()
        if not self._connected:
            if tooltip != '':
                tooltip += '\n'
            tooltip += "PV is disconnected."
        elif not self._write_access:
            if tooltip != '':
                tooltip += '\n'
            if data_plugins.is_read_only():
                tooltip += "Running PyDM on Read-Only mode."
            else:
                tooltip += "Access denied by Channel Access Security."
        self.setToolTip(tooltip)
        self.setEnabled(status)
