from qtpy.QtCore import (Qt, QSize, Property, Slot, Q_ENUMS)
from qtpy.QtWidgets import (QWidget, QButtonGroup, QGridLayout, QPushButton,
                            QRadioButton, QCheckBox)

from .. import data_plugins
from .base import PyDMWritableWidget


class WidgetType(object):
    PushButton = 0
    RadioButton = 1


class_for_type = [QPushButton, QRadioButton]


class PyDMEnumButton(QWidget, PyDMWritableWidget, WidgetType):
    """
    A QWidget that renders buttons for every option of Enum Items.
    For now three types of buttons can be rendered:
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
    Q_ENUMS(WidgetType)
    WidgetType = WidgetType

    def __init__(self, parent=None, init_channel=None):
        QWidget.__init__(self, parent)
        PyDMWritableWidget.__init__(self, init_channel=init_channel)
        self._has_enums = False
        self.setLayout(QGridLayout(self))
        self._btn_group = QButtonGroup()
        self._btn_group.setExclusive(True)
        self._btn_group.buttonClicked[int].connect(self.handle_button_clicked)
        self._widget_type = WidgetType.PushButton
        self._orientation = Qt.Vertical
        self._widgets = []
        self.rebuild_widgets()

    def minimumSizeHint(self):
        """
        This property holds the recommended minimum size for the widget.

        Returns
        -------
        QSize
        """
        # This is totally arbitrary, I just want *some* visible nonzero size
        return QSize(50, 100)

    @Property(WidgetType)
    def widgetType(self):
        """
        The widget type to be used when composing the group.

        Returns
        -------
        WidgetType
        """
        return self._widget_type

    @widgetType.setter
    def widgetType(self, new_type):
        """
        The widget type to be used when composing the group.

        Parameters
        ----------
        new_type : WidgetType
        """
        if new_type != self._widget_type:
            self._widget_type = new_type
            self.rebuild_widgets()

    @Property(Qt.Orientation)
    def orientation(self):
        """
        Whether to lay out the bit indicators vertically or horizontally.

        Returns
        -------
        int
        """
        return self._orientation

    @orientation.setter
    def orientation(self, new_orientation):
        """
        Whether to lay out the bit indicators vertically or horizontally.

        Parameters
        -------
        new_orientation : Qt.Orientation, int
        """
        self._orientation = new_orientation
        self.rebuild_layout()

    @Slot(int)
    def handle_button_clicked(self, id):
        """
        Handles the event of a button being clicked.

        Parameters
        ----------
        id : int
            The clicked button id.
        """
        self.send_value_signal.emit(id)

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
                        self.layout().removeWidget(w)

    def rebuild_widgets(self):
        """
        Rebuild the list of widgets based on a new enum or generates a default
        list of fake strings so we can see something at Designer.
        """
        def generate_widgets(items):
            while len(self._widgets) != 0:
                w = self._widgets.pop(0)
                self._btn_group.removeButton(w)
                w.deleteLater()

            for idx, entry in enumerate(items):
                w = class_for_type[self._widget_type](parent=self)
                w.setCheckable(True)
                w.setText(entry)
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
        if self.orientation == Qt.Vertical:
            for i, widget in enumerate(self._widgets):
                self.layout().addWidget(widget, i, 0)
        elif self.orientation == Qt.Horizontal:
            for i, widget in enumerate(self._widgets):
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
        super(PyDMEnumButton, self).value_changed(new_val)
        if new_val is not None:
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
        super(PyDMEnumButton, self).enum_strings_changed(new_enum_strings)
        self._has_enums = True
        self.check_enable_state()
        self.rebuild_widgets()
