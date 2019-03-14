import json
import os
import webbrowser
from collections import OrderedDict
from copy import deepcopy

from qtpy import QtWidgets, QtCore

from pydm import data_plugins
from pydm.data_plugins.data_store import DEFAULT_INTROSPECTION
from pydm.utilities import protocol_and_address
from pydm.config import DEFAULT_PROTOCOL


class ChannelEditor(QtWidgets.QDialog):
    """
    QDialog for user-friendly editing of the Channels in a widget inside the Qt
    Designer.

    Parameters
    ----------
    widget : PyDMWidget
        The widget which we want to edit the `rules` property.
    """
    PROPERTY = 0
    DISPLAY = 1
    VALUE = 2

    def __init__(self, config, parent=None):
        super(ChannelEditor, self).__init__(parent)

        self.config = config
        self.original_config = deepcopy(config)
        self.return_value = None

        # The central widget which is specific for each Data Plugin on PyDM
        self.plugin_param_widget = None

        # Placeholder for the current selected item on the list
        self.lst_channel_item = None

        # Flag for the methods to mark if we are loading data through code
        # to block callbacks from happening.
        self.loading_data = True

        # A list of available Data plugins
        self.available_plugins = data_plugins.plugin_modules.keys()

        self.introspection_widgets = OrderedDict()

        self.setup_ui()

        for idx, cfg in enumerate(self.config):
            _, display, value = cfg
            self.config[idx][ChannelEditor.VALUE] = self.parse_address(value)
            item = QtWidgets.QListWidgetItem(display, parent=self.lst_channels)
            self.lst_channels.addItem(item)
        self.lst_channels.setCurrentRow(0)
        if len(self.config) == 1:
            self.list_frame.setVisible(False)

    @staticmethod
    def parse_address(address):
        if not address:
            return {}
        try:
            configs = json.loads(address)
        except json.JSONDecodeError:
            # Kept here for backwards compatibility...
            protocol, addr = protocol_and_address(address)
            configs = {
                'connection': {
                    'protocol': protocol,
                    'parameters': {'address': addr},
                },
                'use_introspection': True,
                'introspection': {}
            }
        return configs

    def setup_ui(self):
        """
        Create the required UI elements for the form.

        Returns
        -------
        None
        """
        self.setWindowTitle("PyDM Channel Editor")
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.setContentsMargins(5, 5, 5, 5)
        vlayout.setSpacing(5)
        self.setLayout(vlayout)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.setSpacing(5)
        vlayout.addLayout(hlayout)

        # Creating the widgets for the String List and
        # buttons to add and remove actions
        self.list_frame = QtWidgets.QFrame(parent=self)
        self.list_frame.setMinimumHeight(300)
        self.list_frame.setMaximumWidth(200)
        self.list_frame.setLineWidth(1)
        self.list_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.list_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        lf_layout = QtWidgets.QVBoxLayout()
        self.list_frame.setLayout(lf_layout)

        self.lst_channels = QtWidgets.QListWidget()
        self.lst_channels.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                  QtWidgets.QSizePolicy.Expanding)
        )
        self.lst_channels.itemSelectionChanged.connect(self.load_from_list)
        lf_layout.addWidget(self.lst_channels)

        hlayout.addWidget(self.list_frame)

        buttons_layout = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton("Save", parent=self)
        save_btn.setAutoDefault(False)
        save_btn.setDefault(False)
        save_btn.clicked.connect(self.saveChanges)
        cancel_btn = QtWidgets.QPushButton("Cancel", parent=self)
        cancel_btn.setAutoDefault(False)
        cancel_btn.setDefault(False)
        cancel_btn.clicked.connect(self.cancelChanges)
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)

        vlayout.addLayout(buttons_layout)

        # Creating the widgets that we will use to compose the
        # rule parameters
        self.frm_edit = QtWidgets.QFrame()
        self.frm_edit.setMinimumSize(600, 400)
        self.frm_edit.setEnabled(False)
        self.frm_edit.setLineWidth(1)
        self.frm_edit.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frm_edit.setFrameShape(QtWidgets.QFrame.StyledPanel)

        frm_edit_layout = QtWidgets.QVBoxLayout()
        self.frm_edit.setLayout(frm_edit_layout)

        hlayout.addWidget(self.frm_edit)

        cmb_plugin_layout = QtWidgets.QFormLayout()
        cmb_plugin_layout.setFieldGrowthPolicy(
            QtWidgets.QFormLayout.ExpandingFieldsGrow)

        lbl_property = QtWidgets.QLabel("Data Plugin:")
        self.cmb_plugin = QtWidgets.QComboBox()

        for name in self.available_plugins:
            self.cmb_plugin.addItem(name)
        cmb_plugin_layout.addRow(lbl_property, self.cmb_plugin)
        self.cmb_plugin.currentTextChanged.connect(self.plugin_changed)

        frm_edit_layout.addLayout(cmb_plugin_layout)

        self.param_layout = QtWidgets.QVBoxLayout()
        frm_edit_layout.addLayout(self.param_layout)

        intro_group = QtWidgets.QGroupBox(self)
        intro_group.setTitle("Data Keys")

        intro_group.setLayout(QtWidgets.QVBoxLayout())
        self.chb_introspection = QtWidgets.QCheckBox()
        self.chb_introspection.setText("Use Introspection ?")
        self.chb_introspection.clicked.connect(self.introspection_changed)

        self.frm_datakeys = QtWidgets.QFrame()
        self.frm_datakeys.setLayout(QtWidgets.QFormLayout())
        self.frm_datakeys.layout().setFieldGrowthPolicy(
            QtWidgets.QFormLayout.AllNonFixedFieldsGrow
        )

        keys_scroll = QtWidgets.QScrollArea(self)
        keys_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        keys_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        keys_scroll.setWidget(self.frm_datakeys)
        keys_scroll.setWidgetResizable(True)
        keys_scroll.setMinimumHeight(200)

        for key in DEFAULT_INTROSPECTION:
            label_text = ' '.join(key.split('_')).title() + " Key"
            label = QtWidgets.QLabel(label_text)
            self.introspection_widgets[key] = QtWidgets.QLineEdit(
                self.frm_datakeys)
            self.frm_datakeys.layout().addRow(label,
                                              self.introspection_widgets[key])

        intro_group.layout().addWidget(self.chb_introspection)
        intro_group.layout().addWidget(keys_scroll)

        frm_edit_layout.addWidget(intro_group)

        frm_edit_layout.addStretch(1)

    def plugin_changed(self, plugin):
        def cleanup():
            try:
                if self.plugin_param_widget:
                    self.param_layout.removeWidget(self.plugin_param_widget)
                    self.plugin_param_widget.setVisible(False)
                    self.plugin_param_widget.deleteLater()
            except RuntimeError:
                pass

        module = data_plugins.plugin_modules.get(plugin, None)
        cleanup()
        if module:
            self.plugin_param_widget = module.param_editor(self)
            self.param_layout.addWidget(self.plugin_param_widget)

    def introspection_changed(self, checked):
        self.frm_datakeys.setVisible(not checked)

    def clear_form(self):
        """Clear the form and reset the fields."""
        self.loading_data = True
        self.cmb_plugin.setCurrentIndex(-1)
        self.loading_data = False

    def load_from_list(self):
        """
        Load an entry from the list into the editing form.

        Returns
        -------
        None
        """
        if self.lst_channel_item is not None:
            self.save_item()
            self.clear_form()

        item = self.lst_channels.currentItem()
        idx = self.lst_channels.indexFromItem(item).row()

        if idx < 0:
            return

        self.loading_data = True
        self.lst_channel_item = item
        data = self.config[idx][ChannelEditor.VALUE]
        conn = data.get('connection', {})
        plugin = conn.get('protocol', '')

        if not plugin and DEFAULT_PROTOCOL:
            plugin = DEFAULT_PROTOCOL

        if plugin:
            self.cmb_plugin.setCurrentText(plugin)
            self.plugin_changed(conn.get('protocol', ''))
            self.plugin_param_widget.parameters = conn.get('parameters', {})
        else:
            self.cmb_plugin.setCurrentIndex(-1)
        checked = data.get('use_introspection', True)
        self.chb_introspection.setChecked(checked)
        self.introspection_changed(checked)

        intro = data.get('introspection', {})
        for k, val in intro.items():
            self.introspection_widgets[k].setText(val)

        self.frm_edit.setEnabled(True)
        self.loading_data = False

    def save_item(self, index=None):
        if not index:
            idx = self.lst_channels.indexFromItem(self.lst_channel_item).row()
        else:
            idx = index

        if self.cmb_plugin.currentIndex() < 0:
            return

        self.config[idx][ChannelEditor.VALUE] = {
            'connection': {
                'protocol': self.cmb_plugin.currentText(),
                'parameters': self.plugin_param_widget.parameters,
            },
            'use_introspection': self.chb_introspection.isChecked(),
            'introspection': self.collect_introspection()
        }

    def collect_introspection(self):
        return {k: w.text() for k, w in self.introspection_widgets.items()}

    def get_current_index(self):
        """
        Calculate and return the selected index from the list of rules.

        Returns
        -------
        int
            The index selected at the list of rules or -1 in case the item
            does not exist.
        """
        if self.lst_channel_item is None:
            return -1
        return self.lst_channel_item.indexFromItem(self.lst_channel_item).row()

    @staticmethod
    def open_help(open=True):
        """
        Open the Help context for Rules.
        The documentation website prefix is given by the `PYDM_DOCS_URL`
        environmnet variable. If not defined it defaults to
        `https://slaclab.github.io/pydm`

        Parameters
        ----------
        open : bool
            Whether or not we should use the web browser to open the page.
        """
        docs_url = os.getenv("PYDM_DOCS_URL", None)
        if docs_url is None:
            docs_url = "https://slaclab.github.io/pydm"
        expression_url = "widgets/widget_rules/index.html"
        help_url = "{}/{}".format(docs_url, expression_url)
        if open:
            webbrowser.open(help_url, new=2, autoraise=True)
        else:
            return help_url

    def is_data_valid(self):
        """
        Sanity check the form data.

        Returns
        -------
        tuple : (bool, str)
            True and "" in case there is no error or False and the error
            message otherwise.
        """
        return self.plugin_param_widget.validate()

    @QtCore.Slot()
    def saveChanges(self):
        """Save the channel configs and set `return_value`."""
        self.save_item()
        status, message = self.is_data_valid()
        if status:
            for idx, cfg in enumerate(self.config):
                self.config[idx][ChannelEditor.VALUE] = json.dumps(
                    cfg[ChannelEditor.VALUE]
                )
            self.return_value = self.config
            self.accept()
        else:
            QtWidgets.QMessageBox.critical(self, "Error Saving", message,
                                           QtWidgets.QMessageBox.Ok)

    @QtCore.Slot()
    def cancelChanges(self):
        """Abort the changes and close the dialog."""
        self.return_value = self.original_config
        self.close()

    def closeEvent(self, event):
        if self.return_value is None:
            self.return_value = self.original_config
        super(ChannelEditor, self).closeEvent(event)


if __name__ == '__main__':
    class TestWidget(QtWidgets.QWidget):
        _CHANNELS_CONFIG = OrderedDict(
            [
                ('channel', 'Channel'),
                ('imageChannel', 'Image Channel (optional)'),
            ]
        )

        def __init__(self, *args, **kwargs):
            super(TestWidget, self).__init__(*args, **kwargs)
            self._channel = None
            self._image_channel = json.dumps(
                {
                    'connection': {
                        'protocol': 'archiver',
                        'parameters': {'address': 'test_archiver'},
                    },
                    'use_introspection': False,
                    'introspection': {'CONNECTION': 'FOO', 'VALUE': 'BAR.X',
                                      'SEVERITY': 'BAR.Z',
                                      'WRITE_ACCESS': 'TEST',
                                      'ENUM_STRINGS': '', 'UNIT': '',
                                      'PRECISION': '',
                                      'UPPER_LIMIT': '', 'LOWER_LIMIT': ''}}
            )

        @QtCore.Property(str)
        def channel(self):
            return self._channel

        @channel.setter
        def channel(self, ch):
            if self._channel != ch:
                self._channel = ch
                print('New Channel: ', ch)

        @QtCore.Property(str)
        def imageChannel(self):
            return self._image_channel

        @imageChannel.setter
        def imageChannel(self, ch):
            if self._image_channel != ch:
                self._image_channel = ch
                print('New Image Channel: ', ch)


    app = QtWidgets.QApplication([])
    tw = TestWidget()

    config_map = []
    for prop, display in tw._CHANNELS_CONFIG.items():
        attr = getattr(tw, prop)
        if callable(attr):
            value = attr()
        else:
            value = attr
        config_map.append([prop, display, value])
    editor = ChannelEditor(config_map, parent=None)
    editor.exec_()
    print('Editor finished with: ')
    print(editor.return_value)
    for new_config in editor.return_value:
        prop, _, value = new_config
        attr = getattr(tw, prop)
        if callable(attr):
            value = attr(value)
        else:
            setattr(tw, prop, value)
