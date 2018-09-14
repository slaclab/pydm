import os
import json
import functools
import webbrowser

from qtpy import QtWidgets, QtCore, QtDesigner
from ..utilities.iconfont import IconFont


class RulesEditor(QtWidgets.QDialog):
    """
    QDialog for user-friendly editing of the Rules in a widget inside the Qt
    Designer.

    Parameters
    ----------
    widget : PyDMWidget
        The widget which we want to edit the `rules` property.
    """

    def __init__(self, widget, parent=None):
        super(RulesEditor, self).__init__(parent)

        self.widget = widget
        self.lst_rule_item = None
        self.loading_data = True

        self.available_properties = widget.RULE_PROPERTIES
        self.default_property = widget.DEFAULT_RULE_PROPERTY

        self.setup_ui()

        try:
            self.rules = json.loads(widget.rules)
        except:
            self.rules = []

        for ac in self.rules:
            self.lst_rules.addItem(ac.get("name", ''))

    def setup_ui(self):
        """
        Create the required UI elements for the form.

        Returns
        -------
        None
        """
        iconfont = IconFont()

        self.setWindowTitle("PyDM Widget Rules Editor")
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
        list_frame = QtWidgets.QFrame(parent=self)
        list_frame.setMinimumHeight(300)
        list_frame.setMinimumWidth(240)
        list_frame.setLineWidth(1)
        list_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        list_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        lf_layout = QtWidgets.QVBoxLayout()
        list_frame.setLayout(lf_layout)

        lf_btn_layout = QtWidgets.QHBoxLayout()
        lf_btn_layout.setContentsMargins(0, 0, 0, 0)
        lf_btn_layout.setSpacing(5)

        self.btn_add_rule = QtWidgets.QPushButton(parent=self)
        self.btn_add_rule.setAutoDefault(False)
        self.btn_add_rule.setDefault(False)
        self.btn_add_rule.setText("Add Rule")
        self.btn_add_rule.clicked.connect(self.add_rule)

        self.btn_del_rule = QtWidgets.QPushButton(parent=self)
        self.btn_del_rule.setAutoDefault(False)
        self.btn_del_rule.setDefault(False)
        self.btn_del_rule.setText("Remove Rule")
        self.btn_del_rule.clicked.connect(self.del_rule)

        lf_btn_layout.addWidget(self.btn_add_rule)
        lf_btn_layout.addWidget(self.btn_del_rule)

        lf_layout.addLayout(lf_btn_layout)

        self.lst_rules = QtWidgets.QListWidget()
        self.lst_rules.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding))
        self.lst_rules.itemSelectionChanged.connect(self.load_from_list)
        lf_layout.addWidget(self.lst_rules)

        hlayout.addWidget(list_frame)

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
        self.frm_edit.setEnabled(False)
        self.frm_edit.setLineWidth(1)
        self.frm_edit.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frm_edit.setFrameShape(QtWidgets.QFrame.StyledPanel)

        frm_edit_layout = QtWidgets.QVBoxLayout()
        self.frm_edit.setLayout(frm_edit_layout)

        hlayout.addWidget(self.frm_edit)

        edit_name_layout = QtWidgets.QFormLayout()
        edit_name_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        lbl_name = QtWidgets.QLabel("Rule Name:")
        self.txt_name = QtWidgets.QLineEdit()
        self.txt_name.editingFinished.connect(self.name_changed)
        edit_name_layout.addRow(lbl_name, self.txt_name)
        lbl_property = QtWidgets.QLabel("Property:")
        self.cmb_property = QtWidgets.QComboBox()
        for name, prop in self.available_properties.items():
            self.cmb_property.addItem(name, prop)
        edit_name_layout.addRow(lbl_property, self.cmb_property)

        frm_edit_layout.addLayout(edit_name_layout)

        btn_add_remove_layout = QtWidgets.QHBoxLayout()
        self.btn_add_channel = QtWidgets.QPushButton()
        self.btn_add_channel.setAutoDefault(False)
        self.btn_add_channel.setDefault(False)
        self.btn_add_channel.setText("Add Channel")
        self.btn_add_channel.setIconSize(QtCore.QSize(16, 16))
        self.btn_add_channel.setIcon(iconfont.icon("plus-circle"))
        self.btn_add_channel.clicked.connect(self.add_channel)
        self.btn_del_channel = QtWidgets.QPushButton()
        self.btn_del_channel.setAutoDefault(False)
        self.btn_del_channel.setDefault(False)
        self.btn_del_channel.setText("Remove Channel")
        self.btn_del_channel.setIconSize(QtCore.QSize(16, 16))
        self.btn_del_channel.setIcon(iconfont.icon("minus-circle"))
        self.btn_del_channel.clicked.connect(self.del_channel)
        btn_add_remove_layout.addWidget(self.btn_add_channel)
        btn_add_remove_layout.addWidget(self.btn_del_channel)

        frm_edit_layout.addLayout(btn_add_remove_layout)

        self.tbl_channels = QtWidgets.QTableWidget()
        self.tbl_channels.setMinimumWidth(350)
        self.tbl_channels.setShowGrid(True)
        self.tbl_channels.setCornerButtonEnabled(False)
        self.tbl_channels.model().dataChanged.connect(self.tbl_channels_changed)
        headers = ["Channel", "Trigger?"]
        self.tbl_channels.setColumnCount(len(headers))
        self.tbl_channels.setHorizontalHeaderLabels(headers)
        header = self.tbl_channels.horizontalHeader()
        header.setResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)

        frm_edit_layout.addWidget(self.tbl_channels)

        expression_layout = QtWidgets.QFormLayout()
        expression_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        lbl_expected = QtWidgets.QLabel("Expected Type:")
        self.lbl_expected_type = QtWidgets.QLabel(parent=self)
        # self.lbl_expected_type.setText("")
        self.lbl_expected_type.setStyleSheet(
            "color: rgb(0, 128, 255); font-weight: bold;")
        expression_layout.addRow(lbl_expected, self.lbl_expected_type)

        lbl_expression = QtWidgets.QLabel("Expression:")
        expr_help_layout = QtWidgets.QHBoxLayout()
        self.txt_expression = QtWidgets.QLineEdit()
        self.txt_expression.editingFinished.connect(self.expression_changed)
        expr_help_layout.addWidget(self.txt_expression)
        self.btn_help = QtWidgets.QPushButton()
        self.btn_help.setAutoDefault(False)
        self.btn_help.setDefault(False)
        self.btn_help.setText("Help")
        self.btn_help.setStyleSheet("background-color: rgb(176, 227, 255);")
        self.btn_help.clicked.connect(functools.partial(self.open_help, open=True))
        expr_help_layout.addWidget(self.btn_help)
        expression_layout.addRow(lbl_expression, expr_help_layout)

        self.cmb_property.currentIndexChanged.connect(self.property_changed)
        self.cmb_property.setCurrentText(self.default_property)

        frm_edit_layout.addLayout(expression_layout)

    def clear_form(self):
        """Clear the form and reset the fields."""
        self.loading_data = True
        self.lst_rule_item = None
        self.txt_name.setText("")
        self.cmb_property.setCurrentIndex(-1)
        self.tbl_channels.clearContents()
        self.txt_expression.setText("")
        self.frm_edit.setEnabled(False)
        self.loading_data = False

    def load_from_list(self):
        """
        Load an entry from the list into the editing form.

        Returns
        -------
        None
        """
        item = self.lst_rules.currentItem()
        idx = self.lst_rules.indexFromItem(item).row()

        if idx < 0:
            return

        self.loading_data = True
        self.lst_rule_item = item
        data = self.rules[idx]
        self.txt_name.setText(data.get('name', ''))
        self.cmb_property.setCurrentText(data.get('property', ''))
        self.property_changed(0)
        self.txt_expression.setText(data.get('expression', ''))

        channels = data.get('channels', [])
        self.tbl_channels.clearContents()
        self.tbl_channels.setRowCount(len(channels))
        vlabel = [str(i) for i in range(len(channels))]
        self.tbl_channels.setVerticalHeaderLabels(vlabel)
        for row, ch in enumerate(channels):
            ch_name = ch.get('channel', '')
            ch_tr = ch.get('trigger', False)
            self.tbl_channels.setItem(row, 0,
                                      QtWidgets.QTableWidgetItem(str(ch_name)))
            checkBoxItem = QtWidgets.QTableWidgetItem()
            if ch_tr:
                checkBoxItem.setCheckState(QtCore.Qt.Checked)
            else:
                checkBoxItem.setCheckState(QtCore.Qt.Unchecked)
            self.tbl_channels.setItem(row, 1, checkBoxItem)
        self.frm_edit.setEnabled(True)
        self.loading_data = False

    def add_rule(self):
        """Add a new rule to the list of rules."""
        default_name = "New Rule"
        data = {"name": default_name,
                "property": self.default_property,
                "expression": "",
                "channels": []
                }
        self.rules.append(data)
        self.lst_rule_item = QtWidgets.QListWidgetItem()
        self.lst_rule_item.setText(default_name)
        self.lst_rules.addItem(self.lst_rule_item)
        self.lst_rules.setCurrentItem(self.lst_rule_item)
        self.load_from_list()
        self.txt_name.setFocus()

    def get_current_index(self):
        """
        Calculate and return the selected index from the list of rules.

        Returns
        -------
        int
            The index selected at the list of rules or -1 in case the item
            does not exist.
        """
        if self.lst_rule_item is None:
            return -1
        return self.lst_rules.indexFromItem(self.lst_rule_item).row()

    def change_entry(self, entry, value):
        """
        Change an entry at the rules dictionary.

        Parameters
        ----------
        entry : str
            The key for the dictionary
        value : any
            The value to set on the key. It can be any type, depending on the
            key.

        Returns
        -------
        None
        """
        idx = self.get_current_index()
        self.rules[idx][entry] = value

    def del_rule(self):
        """Delete the rule selected in the rules list."""
        idx = self.get_current_index()
        if idx < 0:
            return
        name = self.lst_rule_item.text()

        confirm_message = "Are you sure you want to delete Rule: {}?".format(
            name)
        reply = QtWidgets.QMessageBox().question(self, 'Message',
                                             confirm_message,
                                             QtWidgets.QMessageBox.Yes,
                                             QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            self.lst_rules.takeItem(idx)
            self.lst_rules.clearSelection()
            self.rules.pop(idx)
            self.clear_form()

    def add_channel(self):
        """Add a new empty channel to the table."""
        self.loading_data = True

        # Make the first entry be checked as suggestion
        if self.tbl_channels.rowCount() == 0:
            state = QtCore.Qt.Checked
        else:
            state = QtCore.Qt.Unchecked

        self.tbl_channels.insertRow(self.tbl_channels.rowCount())
        row = self.tbl_channels.rowCount() - 1
        self.tbl_channels.setItem(row, 0, QtWidgets.QTableWidgetItem(""))
        checkBoxItem = QtWidgets.QTableWidgetItem()
        checkBoxItem.setCheckState(state)
        checkBoxItem.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsUserCheckable)
        self.tbl_channels.setItem(row, 1, checkBoxItem)
        vlabel = [str(i) for i in range(self.tbl_channels.rowCount())]
        self.tbl_channels.setVerticalHeaderLabels(vlabel)
        self.loading_data = False
        self.tbl_channels_changed()

    def del_channel(self):
        """Delete the selected channel at the table."""
        items = self.tbl_channels.selectedIndexes()
        if len(items) == 0:
            return

        c = "channel" if len(items) == 1 else "channels"
        confirm_message = "Delete the selected {}?".format(c)
        reply = QtWidgets.QMessageBox().question(self, 'Message',
                                             confirm_message,
                                             QtWidgets.QMessageBox.Yes,
                                             QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            for itm in reversed(items):
                row = itm.row()
                self.tbl_channels.removeRow(row)

        self.tbl_channels_changed()

    def open_help(self, open=True):
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

    def name_changed(self):
        """Callback executed when the rule name is changed."""
        self.lst_rule_item.setText(self.txt_name.text())
        self.change_entry("name", self.txt_name.text())

    def property_changed(self, index):
        """Callback executed when the property is selected."""
        try:
            prop = self.cmb_property.currentData()
            self.lbl_expected_type.setText(prop[1].__name__)
            idx = self.get_current_index()
            self.change_entry("property", self.cmb_property.currentText())
        except:
            self.lbl_expected_type.setText("")

    def tbl_channels_changed(self, *args, **kwargs):
        """Callback executed when the channels in the table are modified."""
        if self.loading_data:
            return

        new_channels = []

        for row in range(self.tbl_channels.rowCount()):
            ch = self.tbl_channels.item(row, 0).text()
            tr = self.tbl_channels.item(row,
                                        1).checkState() == QtCore.Qt.Checked
            new_channels.append({"channel": ch, "trigger": tr})

        self.change_entry("channels", new_channels)

    def expression_changed(self):
        """Callback executed when the expression is modified."""
        self.change_entry("expression", self.txt_expression.text())

    def is_data_valid(self):
        """
        Sanity check the form data.

        Returns
        -------
        tuple : (bool, str)
            True and "" in case there is no error or False and the error message
            otherwise.
        """
        errors = []
        for idx, rule in enumerate(self.rules):
            name = rule.get("name")
            expression = rule.get("expression")
            channels = rule.get("channels", [])

            if name is None or name == "":
                errors.append("Rule #{} has no name.".format(idx + 1))
            if expression is None or expression == "":
                errors.append("Rule #{} has no expression.".format(idx + 1))
            if len(channels) == 0:
                errors.append("Rule #{} has no channel.".format(idx + 1))
            else:
                found_trigger = False
                for ch_idx, ch in enumerate(channels):
                    if not ch.get("channel", ""):
                        errors.append(
                            "Rule #{} - Ch. #{} has no channel.".format(idx + 1,
                                                                        ch_idx))
                    if ch.get("trigger", False) and not found_trigger:
                        found_trigger = True

                if not found_trigger:
                    errors.append(
                        "Rule #{} has no channel for trigger.".format(idx + 1))

        if len(errors) > 0:
            error_msg = os.linesep.join(errors)
            return False, error_msg

        return True, ""

    @QtCore.Slot()
    def saveChanges(self):
        """Save the new rules at the widget `rules` property."""
        # If the form is being edited, we make sure self.rules has all the
        # latest values from the form before we try to validate.  This fixes
        # a problem where the last form item change wouldn't get saved unless
        # the user knew to hit 'enter' or leave the field to end editing before
        # hitting save.
        if self.frm_edit.isEnabled():
            self.expression_changed()
            self.name_changed()
            self.tbl_channels_changed()
        status, message = self.is_data_valid()
        if status:
            data = json.dumps(self.rules)
            formWindow = QtDesigner.QDesignerFormWindowInterface.findFormWindow(self.widget)
            if formWindow:
                formWindow.cursor().setProperty("rules", data)
            self.accept()
        else:
            QtWidgets.QMessageBox.critical(self, "Error Saving", message,
                                       QtWidgets.QMessageBox.Ok)

    @QtCore.Slot()
    def cancelChanges(self):
        """Abort the changes and close the dialog."""
        self.close()
