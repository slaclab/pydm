import logging
from typing import List

from qtpy.QtCore import Qt, QSize, Slot, QMargins
from qtpy.QtGui import QPainter
from qtpy.QtWidgets import (
    QWidget,
    QButtonGroup,
    QGridLayout,
    QPushButton,
    QRadioButton,
    QStyleOption,
    QStyle,
    QAbstractButton,
)

from .base import PyDMWritableWidget, PostParentClassInitSetup
from pydm import data_plugins
from pydm.utilities import ACTIVE_QT_WRAPPER, QtWrapperTypes

if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYSIDE6:
    from PySide6.QtCore import Property
else:
    from PyQt5.QtCore import pyqtProperty as Property


class WidgetType(object):
    PushButton = 0
    RadioButton = 1


if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYSIDE6:
    from PySide6.QtCore import QEnum
    from enum import Enum

    @QEnum
    # overrides prev enum def
    class WidgetType(Enum):  # noqa: F811
        PushButton = 0
        RadioButton = 1


class_for_type = {WidgetType.PushButton: QPushButton, WidgetType.RadioButton: QRadioButton}

logger = logging.getLogger(__name__)


class PyDMEnumButton(QWidget, PyDMWritableWidget):
    """
    A QWidget that renders buttons for every option of Enum Items.
    For now, two types of buttons can be rendered:
    - Push Button
    - Radio Button

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.

    Signals
    -------
    send_value_signal : int, float, str, bool or np.ndarray
        Emitted when the user changes the value.
    """

    if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYQT5:
        from PyQt5.QtCore import Q_ENUM

        Q_ENUM(WidgetType)
    WidgetType = WidgetType

    # Make enum definitions known to this class
    PushButton = WidgetType.PushButton
    RadioButton = WidgetType.RadioButton

    def __init__(self, parent=None, init_channel=None):
        QWidget.__init__(self, parent)
        PyDMWritableWidget.__init__(self, init_channel=init_channel)
        self._invert_order = False
        self._use_custom_order = False
        self._custom_order = []
        self._has_enums = False
        self._checkable = True
        self.setLayout(QGridLayout(self))
        self._layout_spacing_horizontal = 6
        self._layout_spacing_vertical = 6
        self._layout_margins = QMargins(9, 9, 9, 9)
        self._btn_group = QButtonGroup()
        self._btn_group.setExclusive(True)
        self._btn_group.buttonClicked.connect(self.handle_button_clicked)
        self._widget_type = WidgetType.PushButton
        self._orientation = Qt.Vertical
        self._widgets = []
        self.rebuild_widgets()
        # Execute setup calls that must be done here in the widget class's __init__,
        # and after it's parent __init__ calls have completed.
        # (so we can avoid pyside6 throwing an error, see func def for more info)
        PostParentClassInitSetup(self)

    # On pyside6, we need to expilcity call pydm's base class's eventFilter() call or events
    # will not propagate to the parent classes properly.
    def eventFilter(self, obj, event):
        return PyDMWritableWidget.eventFilter(self, obj, event)

    def minimumSizeHint(self):
        """
        This property holds the recommended minimum size for the widget.

        Returns
        -------
        QSize
        """
        # This is totally arbitrary, I just want *some* visible nonzero size
        return QSize(50, 100)

    def readItems(self) -> List[str]:
        """
        Items to be displayed in the button group.

        This property can be overridden by the items coming from the control system.
        Because C++ QStringList expects a list type, we need to make sure that None is never returned.

        Returns
        -------
        List[str]
        """
        return self.enum_strings or []

    def setItems(self, value) -> None:
        self.enum_strings_changed(value)

    items = Property("QStringList", readItems, setItems)

    def readUseCustomOrder(self) -> bool:
        """
        Whether or not to use custom order for the button group.

        Returns
        -------
        bool
        """
        return self._use_custom_order

    def setUseCustomOrder(self, value) -> None:
        if value != self._use_custom_order:
            self._use_custom_order = value
            self.rebuild_layout()

    useCustomOrder = Property(bool, readUseCustomOrder, setUseCustomOrder)

    def readInvertOrder(self) -> bool:
        """
        Whether or not to invert the order for the button group.

        Returns
        -------
        bool
        """
        return self._invert_order

    def setInvertOrder(self, value) -> None:
        if value != self._invert_order:
            self._invert_order = value
            if self._has_enums:
                self.rebuild_layout()

    invertOrder = Property(bool, readInvertOrder, setInvertOrder)

    def readCustomOrder(self) -> List[str]:
        """
        Index list in which items are to be displayed in the button group.

        Returns
        -------
        List[str]
        """
        return self._custom_order

    def setCustomOOrder(self, value) -> None:
        if value != self._custom_order:
            try:
                [int(v) for v in value]
            except ValueError:
                logger.error("customOrder values can only be integers.")
                return
            self._custom_order = value
            if self.useCustomOrder and self._has_enums:
                self.rebuild_layout()

    customOrder = Property("QStringList", readCustomOrder, setCustomOOrder)

    def readWidgetType(self) -> WidgetType:
        """
        The widget type to be used when composing the group.

        Returns
        -------
        WidgetType
        """
        return self._widget_type

    def setWidgetType(self, new_type) -> None:
        """
        The widget type to be used when composing the group.

        Parameters
        ----------
        new_type : WidgetType
        """
        if new_type != self._widget_type:
            self._widget_type = new_type
            self.rebuild_widgets()

    widgetType = Property(WidgetType, readWidgetType, setWidgetType)

    def readOrientation(self) -> int | Qt.Orientation:
        """
        Whether to lay out the bit indicators vertically or horizontally.

        Returns
        -------
        int
        """
        return self._orientation

    def setOrientation(self, new_orientation) -> None:
        """
        Whether to lay out the bit indicators vertically or horizontally.

        Parameters
        -------
        new_orientation : Qt.Orientation, int
        """
        if new_orientation != self._orientation:
            self._orientation = new_orientation
            self.rebuild_layout()

    prop_type = int if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYSIDE6 else Qt.Orientation
    orientation = Property(prop_type, readOrientation, setOrientation)

    def readMarginTop(self) -> int:
        """
        The top margin of the QGridLayout of buttons.

        Returns
        -------
        int
        """
        return self._layout_margins.top()

    def setMarginTop(self, new_margin) -> None:
        """
        Set the top margin of the QGridLayout of buttons.

        Parameters
        -------
        int
        """
        new_margin = max(0, int(new_margin))
        self._layout_margins.setTop(new_margin)
        self.layout().setContentsMargins(self._layout_margins)

    marginTop = Property(int, readMarginTop, setMarginTop)

    def readMarginBottom(self) -> int:
        """
        The bottom margin of the QGridLayout of buttons.

        Returns
        -------
        int
        """
        return self._layout_margins.bottom()

    def setMarginBottom(self, new_margin) -> None:
        """
        Set the bottom margin of the QGridLayout of buttons.

        Parameters
        -------
        int
        """
        new_margin = max(0, int(new_margin))
        self._layout_margins.setBottom(new_margin)
        self.layout().setContentsMargins(self._layout_margins)

    marginBottom = Property(int, readMarginBottom, setMarginBottom)

    def readMarginLeft(self) -> int:
        """
        The left margin of the QGridLayout of buttons.

        Returns
        -------
        int
        """
        return self._layout_margins.left()

    def setMarginLeft(self, new_margin) -> None:
        """
        Set the left margin of the QGridLayout of buttons.

        Parameters
        -------
        int
        """
        new_margin = max(0, int(new_margin))
        self._layout_margins.setLeft(new_margin)
        self.layout().setContentsMargins(self._layout_margins)

    marginLeft = Property(int, readMarginLeft, setMarginLeft)

    def readMarginRight(self) -> int:
        """
        The right margin of the QGridLayout of buttons.

        Returns
        -------
        int
        """
        return self._layout_margins.right()

    def setMarginRight(self, new_margin) -> None:
        """
        Set the right margin of the QGridLayout of buttons.

        Parameters
        -------
        int
        """
        new_margin = max(0, int(new_margin))
        self._layout_margins.setRight(new_margin)
        self.layout().setContentsMargins(self._layout_margins)

    marginRight = Property(int, readMarginRight, setMarginRight)

    def readHorizontalSpacing(self) -> int:
        """
        The horizontal gap of the QGridLayout containing the QButtonGroup.

        Returns
        -------
        int
        """
        return self._layout_spacing_horizontal

    def setHorizontalSpacing(self, new_spacing) -> None:
        """
        Set the layout horizontal gap between buttons.

        Parameters
        -------
        new_spacing : int
        """
        new_spacing = max(0, int(new_spacing))
        if new_spacing != self._layout_spacing_horizontal:
            self._layout_spacing_horizontal = new_spacing
            self.layout().setHorizontalSpacing(new_spacing)

    horizontalSpacing = Property(int, readHorizontalSpacing, setHorizontalSpacing)

    def readVerticalSpacing(self) -> int:
        """
        The vertical gap of the QGridLayout containing the QButtonGroup.

        Returns
        -------
        int
        """
        return self._layout_spacing_vertical

    def setVerticalSpacing(self, new_spacing) -> None:
        """
        Set the layout vertical gap between buttons.

        Parameters
        -------
        new_spacing : int
        """
        new_spacing = max(0, int(new_spacing))
        if new_spacing != self._layout_spacing_vertical:
            self._layout_spacing_vertical = new_spacing
            self.layout().setVerticalSpacing(new_spacing)

    verticalSpacing = Property(int, readVerticalSpacing, setVerticalSpacing)

    def readCheckable(self) -> bool:
        """
        Whether or not the button should be checkable.

        Returns
        -------
        bool
        """
        return self._checkable

    def setCheckable(self, value) -> None:
        if value != self._checkable:
            self._checkable = value
            for widget in self._widgets:
                widget.setCheckable(value)

    checkable = Property(bool, readCheckable, setCheckable)

    @Slot(QAbstractButton)
    def handle_button_clicked(self, button):
        """
        Handles the event of a button being clicked.

        Parameters
        ----------
        id : QAbstractButton
            The clicked button button.
        """
        button_id = self._btn_group.id(button)  # get id of the button in the group
        self.send_value_signal.emit(button_id)

    def clear(self):
        """
        Remove all inner widgets from the layout
        """
        for col in range(0, self.layout().columnCount()):
            for row in range(0, self.layout().rowCount()):
                item = self.layout().itemAtPosition(row, col)
                if item is not None:
                    w = item.widget()
                    if w is not None:
                        w.hide()
                        self.layout().removeWidget(w)

    def rebuild_widgets(self):
        """
        Rebuild the list of widgets based on a new enum or generates a default
        list of fake strings so we can see something at Designer.
        """

        def generate_widgets(items):
            while len(self._widgets) != 0:
                w = self._widgets.pop(0)
                w.hide()
                self._btn_group.removeButton(w)
                w.deleteLater()

            for idx, entry in enumerate(items):
                w = class_for_type[self._widget_type](parent=self)
                w.setCheckable(self.checkable)
                w.setText(entry)
                w.setVisible(False)
                self._widgets.append(w)
                self._btn_group.addButton(w, idx)

        self.clear()
        if self._has_enums:
            generate_widgets(self.enum_strings)
        else:
            generate_widgets(["Item 1", "Item 2", "Item ..."])

        self.rebuild_layout()

    def rebuild_layout(self):
        """
        Method to reorganize the top-level widget and its contents
        according to the layout property values.
        """
        self.clear()

        if self.useCustomOrder:
            order = [int(v) for v in self.customOrder]
        else:
            order = list(range(len(self._widgets)))

        if self.invertOrder:
            order = order[::-1]

        for i, idx in enumerate(order):
            try:
                widget = self._widgets[idx]
                widget.setVisible(True)
            except IndexError:
                if self._has_enums:
                    logger.error(
                        "Invalid index for PyDMEnumButton %s. Index: %s, Range: 0 to %s",
                        self.objectName(),
                        idx,
                        len(self._widgets) - 1,
                    )
                continue
            if self.orientation == Qt.Vertical:
                self.layout().addWidget(widget, i, 0)
            elif self.orientation == Qt.Horizontal:
                self.layout().addWidget(widget, 0, i)

    def check_enable_state(self):
        """
        Checks whether or not the widget should be disable.
        This method also disables the widget and add a Tool Tip
        with the reason why it is disabled.

        """
        status = self._write_access and self._connected and self._has_enums
        tooltip = ""
        if not self._connected:
            tooltip += "Channel is disconnected."
        elif not self._write_access:
            if data_plugins.is_read_only():
                tooltip += "Running PyDM on Read-Only mode."
            else:
                tooltip += "Access denied by Channel Access Security."
        elif not self._has_enums:
            tooltip += "Enums not available."

        self.setToolTip(tooltip)
        self.setEnabled(status)

    def value_changed(self, new_val):
        """
        Callback invoked when the Channel value is changed.

        Parameters
        ----------
        new_val : int
            The new value from the channel.
        """
        if new_val is not None and new_val != self.value:
            super().value_changed(new_val)
            btn = self._btn_group.button(new_val)
            if btn:
                btn.setChecked(True)

    def enum_strings_changed(self, new_enum_strings):
        """
        Callback invoked when the Channel has new enum values.
        This callback also triggers a value_changed call so the
        new enum values to be broadcasted.

        Parameters
        ----------
        new_enum_strings : tuple
            The new list of values
        """
        if new_enum_strings is not None and new_enum_strings != self.enum_strings:
            super().enum_strings_changed(new_enum_strings)
            self._has_enums = True
            self.check_enable_state()
            self.rebuild_widgets()

    def paintEvent(self, _):
        """
        Paint events are sent to widgets that need to update themselves,
        for instance when part of a widget is exposed because a covering
        widget was moved.

        At PyDMDrawing this method handles the alarm painting with parameters
        from the stylesheet, configures the brush, pen and calls ```draw_item```
        so the specifics can be performed for each of the drawing classes.

        Parameters
        ----------
        event : QPaintEvent
        """
        painter = QPainter(self)
        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)
        painter.setRenderHint(QPainter.Antialiasing)
