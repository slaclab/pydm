import enum
import os
import re
import platform
import weakref
import logging
import functools
import json
import copy
import numpy as np
from qtpy.QtWidgets import QApplication, QMenu, QGraphicsOpacityEffect, QToolTip, QWidget
from qtpy.QtGui import QCursor, QIcon, QClipboard
from qtpy.QtCore import Qt, QEvent, Signal, Slot, Property
from .channel import PyDMChannel
from pydm import data_plugins, tools, config
from pydm.utilities import is_qt_designer, remove_protocol
from pydm.display import Display
from .rules import RulesDispatcher
from datetime import datetime
from typing import Optional

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

logger = logging.getLogger(__name__)

try:
    str_types = (str, unicode)
except NameError:
    str_types = (str,)


def get_icon_file(name: str) -> str:
    """
    Returns the absolute path to the icon filename provided.

    Parameters
    ----------
    name : str
        The filename of the icon, relative to ``pydm.icons``.

    Returns
    -------
    str
        The absolute path to the icon file.
    """
    base_path = os.path.dirname(os.path.realpath(__file__))
    icon_path = os.path.join(base_path, "icons", name)
    return icon_path


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


def refresh_style(widget):
    """
    Method that traverse the widget tree starting at `widget` and refresh the
    style for this widget and its children.

    Parameters
    ----------
    widget : QWidget
    """
    widgets = [widget]

    try:
        widgets.extend(widget.findChildren(QWidget))
    except Exception:
        # If we fail it means that widget is probably destroyed
        return
    for child_widget in widgets:
        try:
            child_widget.style().unpolish(child_widget)
            child_widget.style().polish(child_widget)
            child_widget.update()
        except Exception as ex:
            # Widget was probably destroyed
            logger.debug("Error while refreshing stylesheet. %s ", ex)


def PostParentClassInitSetup(self):
    # This function should only be called from a pydm widget class's __init__ call, and *not* from
    # from the __init__ of it's parent classes (PyDMWidget/PyDMPrimitiveWidget) where it throws an error on pyside6.
    # The error is pyside6 thinks the widget class's parent __init__ calls are not getting called
    # in the proper order, despite the fact that we explicitly call them so there should be no real issue.
    # (see commit-msg of beb3c5533b717c3c9a00bd35c8615d900abbc03c for more explanation)
    self.setContextMenuPolicy(Qt.DefaultContextMenu)
    if not is_qt_designer():
        # Install event filter only if not running in Designer
        self.installEventFilter(self)
        # Will call the widget class's check_enable_state if it has one, else will use PyDMWidget's.
        self.check_enable_state()

    self.destroyed.connect(functools.partial(widget_destroyed, self.channels, weakref.ref(self)))


class PyDMPrimitiveWidget(object):
    """
    Primitive class that determines that a given widget is a PyDMWidget.
    All Widget classes from PyDMWidget will be True for
    isinstance(obj, PyDMPrimitiveWidget)
    """

    DEFAULT_RULE_PROPERTY = "Visible"
    RULE_PROPERTIES = {
        "Enable": ["setEnabled", bool],
        "Visible": ["setVisible", bool],
        "Opacity": ["set_opacity", float],
    }

    def __init__(self, **kwargs):
        self.app = QApplication.instance()
        self._rules = None
        self._opacity = 1.0

    def __init_subclass__(cls):
        """
        Adds or redefines rule-triggered property configuration for derivative
        classes.

        Parameters
        ----------
        new_properties: dict
            A dictionary containing the properties that can be modified
            through rule triggers. The format of this dictionary must
            follow the one for entries in PyDMPrimitiveWidget.RULE_PROPERTIES.
            Namely, the key should be a name to be displayed by the Rule
            Editor (in designer), and the value a list containing two elements:
            a string naming the method in the class that will handle the
            rule dispatch, and a type matching the one that we expect to
            receive from the PV value.
        """
        if hasattr(cls, "new_properties") and isinstance(cls.new_properties, dict):
            cls.RULE_PROPERTIES = cls.RULE_PROPERTIES.copy()
            cls.RULE_PROPERTIES.update(cls.new_properties)

    @staticmethod
    def get_designer_icon():
        """Icon for usage in Qt designer."""
        return QIcon()

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
        channels_method = getattr(self, "channels", None)
        if channels_method is None:
            return
        channels = channels_method()
        if not channels:
            logger.debug("Widget has no channels to display tooltip")
            return

        addrs = []
        no_proto_addrs = []
        for ch in channels:
            if not ch:
                continue
            addr = ch.address
            if not addr:
                continue
            addrs.append(addr)
            no_proto_addrs.append(remove_protocol(addr))

        tooltip = os.linesep.join(addrs)
        clipboard_text = " ".join(no_proto_addrs)
        QToolTip.showText(event.globalPos(), tooltip)
        # If the address has a protocol, strip it out before putting it on the
        # clipboard.

        clipboard = QApplication.clipboard()

        if platform.system() == "Linux":
            # Mode Selection is only valid for X11.
            clipboard.setText(clipboard_text, mode=QClipboard.Selection)

        clipboard.setText(clipboard_text, mode=QClipboard.Clipboard)
        event = QEvent(QEvent.Clipboard)
        self.app.sendEvent(clipboard, event)

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
        name = payload.get("name", "")
        prop = payload.get("property", "")
        value = payload.get("value", None)

        if prop not in self.RULE_PROPERTIES:
            logger.error("Error at Rule: %s. %s is not part of this widget properties.", name, prop)
            return

        method_name, data_type = self.RULE_PROPERTIES[prop]
        try:
            if data_type == bool and isinstance(value, str_types):
                # We do this as we already import json and for Python:
                # bool("False") -> True
                val = json.loads(value.lower())
            else:
                val = data_type(value)

            method = getattr(self, method_name)
            if callable(method):
                method(val)
            else:
                setattr(self, method_name, val)

        except Exception:
            logger.error(
                "Error at Rule: %s. Could not execute method %s with value %s and type as %s.",
                name,
                method_name,
                value,
                data_type.__name__,
            )

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
            RulesDispatcher().unregister(self)
            try:
                rules_list = json.loads(self._rules)
                if rules_list:
                    RulesDispatcher().register(self, rules_list)
            except JSONDecodeError:
                logger.exception("Invalid format for Rules")

    def find_parent_display(self):
        widget = self.parent()
        while widget is not None:
            if isinstance(widget, Display):
                return widget
            widget = widget.parent()
        return None


class AlarmLimit(str, enum.Enum):
    """An enum for holding values corresponding to the EPICS alarm limits"""

    HIHI = "HIHI"
    HIGH = "HIGH"
    LOW = "LOW"
    LOLO = "LOLO"


class TextFormatter(object):
    default_precision_from_pv = True

    def __init__(self):
        self._show_units = False
        self.format_string = "{}"
        self._precision_from_pv = None
        self._user_prec = 0
        self._prec = 0
        self._unit = ""

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
            self.format_string = "{:." + str(self.precision) + "f}"
        if self._show_units and self._unit != "":
            self.format_string += " {}".format(self._unit)
        return self.format_string

    def precision_changed(self, new_precision):
        """
        Callback invoked when the Channel has new precision value.
        This callback also triggers an update_format_string call so the
        new precision value is considered.

        Parameters
        ----------
        new_precision : int or float
            The new precision value
        """
        if self.precisionFromPV and new_precision != self._prec:
            self._prec = new_precision
            if self.value is not None:
                self.value_changed(self.value)

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

    @Property(int)
    def precision(self):
        """
        The precision to be used when formatting the output of the PV

        Returns
        -------
        prec : int
            The current precision value
        """
        if self.precisionFromPV:
            return self._prec
        return self._user_prec

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
        if self._precision_from_pv is not None and self._precision_from_pv:
            return
        if new_prec and self._user_prec != int(new_prec) and new_prec >= 0:
            self._user_prec = int(new_prec)
            if not is_qt_designer() or config.DESIGNER_ONLINE:
                self.value_changed(self.value)

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

        Parameters
        ---------
        show_units : bool
            True means that the unit will be appended to the output value
            format string
        """
        if self._show_units != show_units:
            self._show_units = show_units
            self.update_format_string()

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
        precision_from_pv : bool
            True means that the widget will use the precision information
            from the Channel if available.
        """
        return self._precision_from_pv if self._precision_from_pv is not None else self.default_precision_from_pv

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
        if self._precision_from_pv is None or self._precision_from_pv != bool(value):
            self._precision_from_pv = value
            self.update_format_string()

    def value_changed(self, new_val):
        """
        Callback invoked when the Channel value is changed.

        Parameters
        ----------
        new_val : str, int, float, bool or np.ndarray
            The new value from the channel. The type depends on the channel.
        """
        super().value_changed(new_val)
        self.update_format_string()


_positionRuleProperties = {"Position - X": ["setX", int], "Position - Y": ["setY", int]}


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

    # this is same for all instances of the class, so don't define with '.self'
    new_properties = _positionRuleProperties

    # Alarm types
    ALARM_NONE = 0
    ALARM_MINOR = 1
    ALARM_MAJOR = 2
    ALARM_INVALID = 3
    ALARM_DISCONNECTED = 4

    def __init__(self, init_channel=None):
        super().__init__()

        self._connected = True
        self._channel = None
        self._channels = list()
        self._show_units = False
        self._alarm_sensitive_content = False
        self._alarm_sensitive_border = True
        self._alarm_state = self.ALARM_NONE
        self._tooltip = None

        self._upper_ctrl_limit = None
        self._lower_ctrl_limit = None

        self.upper_alarm_limit = None
        self.lower_alarm_limit = None
        self.upper_warning_limit = None
        self.lower_warning_limit = None
        self.enum_strings = None
        self.timestamp = None

        self.value = None
        self.channeltype = None
        self.subtype = None

        self._pydm_tool_tip = ""
        self._tool_tip_substrings = []
        self._tool_tip_channel_table = {
            "address": "_channel",
            "connection": "_connected",
            "SEVR": "_alarm_state",
            "enum_strings": "enum_strings",
            "EGU": "_unit",
            "PREC": "_prec",
            "DRVH": "_upper_ctrl_limit",
            "DRVL": "_lower_ctrl_limit",
            "HIHI": "upper_alarm_limit",
            "LOLO": "lower_alarm_limit",
            "HIGH": "upper_warning_limit",
            "LOW": "lower_warning_limit",
            "TIME": "timestamp",
        }

        # If this label is inside a PyDMApplication (not Designer) start it in
        # the disconnected state.
        self.contextMenuEvent = self.open_context_menu
        self.channel = init_channel
        if not is_qt_designer():
            self._connected = False
            self.alarmSeverityChanged(self.ALARM_DISCONNECTED)

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

        kwargs = {"channels": self.channels_for_tools(), "sender": self}
        tools.assemble_tools_menu(menu, widget_only=True, widget=self, **kwargs)

        # Add a view help action if the parent display has an associated help file
        parent_display = self.find_parent_display()
        if parent_display is not None and parent_display.help_window is not None:
            if len(menu.actions()) > 0:
                menu.addSeparator()
            menu.addAction("View Help for this Display", parent_display.show_help)

        return menu

    def open_context_menu(self, ev):
        """
        Handler for when the Default Context Menu is requested.

        Parameters
        ----------
        ev : QEvent
        """
        menu = self.generate_context_menu()
        menu.exec_(self.mapToGlobal(ev.pos()))
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
        if new_alarm_severity == self._alarm_state:
            return
        if not self._channel:
            self._alarm_state = PyDMWidget.ALARM_NONE
        else:
            self._alarm_state = new_alarm_severity
        refresh_style(self)

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

    def timestamp_changed(self, new_timestamp):
        """
        Callback invoked when the Channel has new timestamp values.


        Parameters
        ----------
        new_timestamp : float
            The new timestamp value
        """
        if new_timestamp != self.timestamp:
            self.timestamp = new_timestamp

    def get_address(self):
        if not len(self._channels):
            logger.warning("Object %r has no PyDM Channels", self)
            return
        return self.channels()[0].address

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

    def alarm_limit_changed(self, which: AlarmLimit, new_limit: float) -> None:
        """
        Callback invoked when the channel receives new alarm limit values.

        Parameters
        ----------
        which : AlarmLimit
            Which alarm limit was changed. "HIHI", "HIGH", "LOW", "LOLO"
        new_limit : float
            New value for the alarm limit
        """
        if which is AlarmLimit.HIHI:
            self.upper_alarm_limit = new_limit
        elif which is AlarmLimit.HIGH:
            self.upper_warning_limit = new_limit
        elif which is AlarmLimit.LOW:
            self.lower_warning_limit = new_limit
        elif which is AlarmLimit.LOLO:
            self.lower_alarm_limit = new_limit

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

    @Slot(int)
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

    @Slot(int)
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

    @Slot(int)
    @Slot(float)
    def upper_alarm_limit_changed(self, new_limit: float):
        """
        PyQT slot for changes to the HIHI alarm limit of a PV

        Parameters
        ----------
        new_limit : float
           The new value for the HIHI limit
        """
        self.alarm_limit_changed(AlarmLimit.HIHI, new_limit)

    @Slot(int)
    @Slot(float)
    def lower_alarm_limit_changed(self, new_limit: float):
        """
        PyQT slot for changes to the LOLO alarm limit of a PV

        Parameters
        ----------
        new_limit : float
           The new value for the LOLO limit
        """
        self.alarm_limit_changed(AlarmLimit.LOLO, new_limit)

    @Slot(int)
    @Slot(float)
    def upper_warning_limit_changed(self, new_limit: float):
        """
        PyQT slot for changes to the HIGH alarm limit of a PV

        Parameters
        ----------
        new_limit : float
           The new value for the HIGH limit
        """
        self.alarm_limit_changed(AlarmLimit.HIGH, new_limit)

    @Slot(int)
    @Slot(float)
    def lower_warning_limit_changed(self, new_limit: float):
        """
        PyQT slot for changes to the LOW alarm limit of a PV

        Parameters
        ----------
        new_limit : float
           The new value for the LOW limit
        """
        self.alarm_limit_changed(AlarmLimit.LOW, new_limit)

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

    @Property(str)
    def PyDMToolTip(self):
        """
        The tooltip for this widget.

            Returns
            -------
            toolTip : str
                tooltip info
        """
        return self._pydm_tool_tip

    @PyDMToolTip.setter
    def PyDMToolTip(self, new_tip):
        """
        The tooltip for this widget.

        Parameters
        ----------
        new_tip : str
            tooltip info
        """
        if new_tip != self._pydm_tool_tip:
            self._pydm_tool_tip = str(new_tip)
            parsed_tool_tip = self.parseTip(new_tip)
            self.setToolTip(parsed_tool_tip)

    def parseTip(self, new_tip):
        """
        Fetch the object attribute data for the tooltip.

        Parameters
        ----------
        new_tip : str
            given tooltip string

        Returns
        -------
        tip_with_attribute_info : str
            ToolTip string which has had the attribute names replaced with the attribute values.
        """
        if is_qt_designer():
            return new_tip

        if not self._tool_tip_substrings:
            list_of_attributes = [substring.start() for substring in re.finditer("\$\(", new_tip)]
            tool_tip_substrings = []

            for index in list_of_attributes:
                tool_tip_substrings.append(
                    [new_tip[index + 2 : new_tip.index(")", index)], new_tip[index : new_tip.index(")", index) + 1]]
                )

            self._tool_tip_substrings = copy.deepcopy(tool_tip_substrings)
        else:
            tool_tip_substrings = copy.deepcopy(self._tool_tip_substrings)

        if tool_tip_substrings:
            for index, value in enumerate(tool_tip_substrings):
                if value[0] == "name":
                    value_of_attribute = self.channel
                elif value[0].split(".")[0] == "pv_value":
                    if value[0].count(".") == 0:
                        value_of_attribute = self.value
                    else:
                        attribute = self._tool_tip_channel_table[value[0].split(".", 1)[1]]
                        value_of_attribute = getattr(self, attribute, None)

                        if attribute == "timestamp" and value_of_attribute is not None:
                            value_of_attribute = datetime.fromtimestamp(value_of_attribute)
                else:
                    value_of_attribute = getattr(self, value[0], None)

                if value[0] == "timestamp" and value_of_attribute is not None:
                    value_of_attribute = datetime.fromtimestamp(value_of_attribute)

                tool_tip_substrings[index][0] = str(value_of_attribute)

        tip_with_attribute_info = new_tip

        for value in tool_tip_substrings:
            tip_with_attribute_info = tip_with_attribute_info.replace(value[1], value[0])

        return tip_with_attribute_info

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
        self.set_channel(value)

    def set_channel(self, value):
        """A setter method without a pyqt decorator so subclasses can use this functionality"""
        if self._channel != value:
            # Remove old connections
            for channel in [c for c in self._channels if c.address == self._channel]:
                channel.disconnect()
                self._channels.remove(channel)
            # Load new channel
            self._channel = str(value)
            if not self._channel:
                logger.debug("Channel was set to an empty string.")
                return
            channel = PyDMChannel(
                address=self._channel,
                connection_slot=self.connectionStateChanged,
                value_slot=self.channelValueChanged,
                severity_slot=self.alarmSeverityChanged,
                enum_strings_slot=self.enumStringsChanged,
                unit_slot=None,
                prec_slot=None,
                upper_ctrl_limit_slot=self.upperCtrlLimitChanged,
                lower_ctrl_limit_slot=self.lowerCtrlLimitChanged,
                upper_alarm_limit_slot=self.upper_alarm_limit_changed,
                lower_alarm_limit_slot=self.lower_alarm_limit_changed,
                upper_warning_limit_slot=self.upper_warning_limit_changed,
                lower_warning_limit_slot=self.lower_warning_limit_changed,
                value_signal=None,
                write_access_slot=None,
                timestamp_slot=self.timestamp_changed,
            )
            # Load writeable channels if our widget requires them. These should
            # not exist on the base PyDMWidget but prevents us from duplicating
            # the method below to only make two more connections
            if hasattr(self, "writeAccessChanged"):
                channel.write_access_slot = self.writeAccessChanged
            if hasattr(self, "send_value_signal"):
                channel.value_signal = self.send_value_signal
            # Do the same thing for classes that use the TextFormatter mixin.
            if hasattr(self, "unitChanged"):
                channel.unit_slot = self.unitChanged
            if hasattr(self, "precisionChanged"):
                channel.prec_slot = self.precisionChanged
            # Connect write channels if we have them
            channel.connect()
            self._channels.append(channel)

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
            if tooltip != "":
                tooltip += "\n"
            tooltip += "PV is disconnected."
            tooltip += "\n"
            tooltip += self.get_address()

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

        if event.type() == QEvent.Enter and self._connected:
            if not self._pydm_tool_tip:
                self.setToolTip(self.parseTip(self.toolTip()))
            else:
                self.setToolTip(self.parseTip(self._pydm_tool_tip))
            return True

        return super().eventFilter(obj, event)


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

    __Signals__ = "send_value_signal((int, ), (float, ), (str, ), (bool, ), (object, ))"

    # Emitted when the user changes the value.
    send_value_signal = Signal((int,), (float,), (str,), (bool,), (object,))

    def __init__(self, init_channel=None):
        self._write_access = False
        self._disp_channel = None
        self._disable_put = False
        self._monitor_disp = False
        super().__init__(init_channel=init_channel)

    def init_for_designer(self):
        """
        Method called after the constructor to tweak configurations for
        when using the widget with the Qt Designer
        """
        super().init_for_designer()
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
        channel = getattr(self, "channel", None)

        if is_channel_valid(channel):
            status = self._write_access and self._connected

            if event.type() == QEvent.Leave:
                QApplication.restoreOverrideCursor()

            if event.type() == QEvent.Enter and not status:
                QApplication.setOverrideCursor(QCursor(Qt.ForbiddenCursor))

        return PyDMWidget.eventFilter(self, obj, event)

    @Property(bool)
    def monitorDisp(self) -> bool:
        """
        Whether to monitor the DISP field for this widget's channel
        """
        return self._monitor_disp

    @monitorDisp.setter
    def monitorDisp(self, monitor_disp: bool) -> None:
        """
        Whether to monitor the DISP field for this widget's channel
        """
        if self._monitor_disp != monitor_disp:
            self._monitor_disp = monitor_disp
            if self._disp_channel is not None:
                if monitor_disp:
                    self._disp_channel.connect()
                else:
                    self._disp_channel.disconnect()

    @Property(str)
    def channel(self) -> Optional[str]:
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
    def channel(self, value: str) -> None:
        """
        The channel address in use for this widget. Also sets up a monitor on the DISP field.
        """
        if self._channel != value:
            self.set_channel(value)
            if not self._monitor_disp or self._channel is None:
                return

            base_channel = self._channel.split(".", 1)[0] if "." in self._channel else self._channel
            if self._disp_channel is None or self._disp_channel.address != f"{base_channel}.DISP":
                if self._disp_channel is not None:
                    self._disp_channel.disconnect()
                self._disp_channel = PyDMChannel(address=f"{base_channel}.DISP", value_slot=self.disp_value_changed)
                self._disp_channel.connect()

    def disp_value_changed(self, new_disp_value: int) -> None:
        """Callback function to receive changes to the DISP field of the monitored channel"""
        self._disable_put = new_disp_value
        self.check_enable_state()

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
    def check_enable_state(self) -> None:
        """
        Checks whether or not the widget should be disabled.
        This method also disables the widget and adds a tool tip with the reason why it is disabled.
        """
        status = self._write_access and self._connected and not self._disable_put
        tooltip = self.restore_original_tooltip()
        if not self._connected:
            if tooltip != "":
                tooltip += "\n"
            tooltip += "PV is disconnected."
            tooltip += "\n"
            tooltip += self.get_address()
        elif not self._write_access:
            if tooltip != "":
                tooltip += "\n"
            if data_plugins.is_read_only():
                tooltip += "Running PyDM on Read-Only mode."
            else:
                tooltip += "Access denied by Channel Access Security."
        elif self._disable_put:
            if tooltip != "":
                tooltip += "\n"
            tooltip += "Access denied by DISP field"

        self.setToolTip(tooltip)
        self.setEnabled(status)
