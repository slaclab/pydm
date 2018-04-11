from ..PyQt.QtGui import QFrame, QComboBox, QHBoxLayout
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, Qt
from .base import PyDMWritableWidget
from pydm.utilities import is_pydm_app


class PyDMEnumComboBox(QFrame, PyDMWritableWidget):
    """
    A QComboBox with support for Channels and more from PyDM

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
    activated : int, str
        Emitted when the user chooses an item in the combobox.
    currentIndexChanged : int, str
        Emitted when the index is changed in the combobox.
    highlighted : int, str
        Emitted when an item in the combobox popup list is highlighted
        by the user.
    """
    activated = pyqtSignal([int], [str])
    currentIndexChanged = pyqtSignal([int], [str])
    highlighted = pyqtSignal([int], [str])

    def __init__(self, parent=None, init_channel=None):
        QFrame.__init__(self, parent)
        PyDMWritableWidget.__init__(self, init_channel=init_channel)
        self.horizontal_layout = QHBoxLayout(self)
        self.combo_box = QComboBox(self)
        self.horizontal_layout.addWidget(self.combo_box)
        # Internal values for properties
        self._has_enums = False
        self.combo_box.activated[int].connect(self.internal_combo_box_activated_int)
        self.combo_box.activated[str].connect(self.internal_combo_box_activated_str)
        self.combo_box.currentIndexChanged[int].connect(self.internal_combo_box_index_changed_int)
        self.combo_box.currentIndexChanged[str].connect(self.internal_combo_box_index_changed_str)
        self.combo_box.highlighted[int].connect(self.internal_combo_box_highlighted_int)
        self.combo_box.highlighted[str].connect(self.internal_combo_box_highlighted_str)
        self.combo_box.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.combo_box.contextMenuEvent = self.open_context_menu

    # Internal methods
    def set_items(self, enums):
        """
        Internal method to fill the ComboBox items based on a list
        of strings.

        Parameters
        ----------
        new_enum_strings : tuple
            The new list of values
        """
        self.combo_box.clear()
        for enum in enums:
            self.combo_box.addItem(enum)
        self._has_enums = True
        self.check_enable_state()

    def check_enable_state(self):
        """
        Checks whether or not the widget should be disable.
        This method also disables the widget and add a Tool Tip
        with the reason why it is disabled.

        """
        status = self._write_access and self._connected and self._has_enums
        tooltip = ""
        if not self._connected:
            tooltip += "PV is disconnected."
        elif not self._write_access:
            if is_pydm_app() and self.app.is_read_only():
                tooltip += "Running PyDM on Read-Only mode."
            else:
                tooltip += "Access denied by Channel Access Security."
        elif not self._has_enums:
            tooltip += "Enums not available."

        self.setToolTip(tooltip)
        self.setEnabled(status)

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
        super(PyDMEnumComboBox, self).enum_strings_changed(new_enum_strings)
        self.set_items(new_enum_strings)

    def value_changed(self, new_val):
        """
        Callback invoked when the Channel value is changed.
        Sets the value of new_value accordingly at the ComboBox.

        Parameters
        ----------
        new_value : str, int, float, bool or np.ndarray
            The new value from the channel. The type depends on the channel.
        """
        if new_val is not None:
            super(PyDMEnumComboBox, self).value_changed(new_val)
            self.combo_box.setCurrentIndex(new_val)

    # Internal combo box signal handling.
    # In places where we just forward the signal, we may want to instead
    # just do self.signal = self.combo_box.signal
    # in __init__...
    @pyqtSlot(int)
    def internal_combo_box_activated_int(self, index):
        """
        PyQT Slot for when the user chooses an item in the combobox.
        This slot triggers the ```send_value_signal``` and
        ```activated``` signals.

        Parameters
        ----------
        index : int

        """
        self.send_value_signal.emit(index)
        self.activated[int].emit(index)

    @pyqtSlot(str)
    def internal_combo_box_activated_str(self, text):
        """
        PyQT Slot for when the user chooses an item in the combobox.
        This slot triggers the ```activated``` signal.

        Parameters
        ----------
        text : str

        """
        self.activated[str].emit(text)

    @pyqtSlot(int)
    def internal_combo_box_index_changed_int(self, index):
        """
        PyQT Slot for when the index is changed in the combobox.
        This slot triggers the ```currentIndexChanged``` signal.

        Parameters
        ----------
        index : int

        """
        self.currentIndexChanged[int].emit(index)

    @pyqtSlot(str)
    def internal_combo_box_index_changed_str(self, text):
        """
        PyQT Slot for when the index is changed in the combobox.
        This slot triggers the ```currentIndexChanged``` signal.

        Parameters
        ----------
        text : str

        """
        self.currentIndexChanged[str].emit(text)

    @pyqtSlot(int)
    def internal_combo_box_highlighted_int(self, index):
        """
        PyQT Slot for when an item in the combobox popup list is
        highlighted by the user.
        This slot triggers the ```highlighted``` signal.

        Parameters
        ----------
        index : int

        """
        self.highlighted[int].emit(index)

    @pyqtSlot(str)
    def internal_combo_box_highlighted_str(self, text):
        """
        PyQT Slot for when an item in the combobox popup list is
        highlighted by the user.
        This slot triggers the ```highlighted``` signal.

        Parameters
        ----------
        text : str

        """
        self.highlighted[str].emit(text)
