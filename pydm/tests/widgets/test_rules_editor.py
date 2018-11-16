import os
import pytest
import logging
import json
import copy
import webbrowser

from qtpy import QtCore
from qtpy.QtWidgets import QMessageBox, QTableWidgetSelectionRange

from ...widgets.label import PyDMLabel
from ...widgets.rules_editor import RulesEditor


def test_rules_editor(qtbot, monkeypatch):
    """
    Test the rules editor in general.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    monkeypatch : fixture
        To override dialog behaviors
    """
    # Create the base widget
    widget = PyDMLabel()
    qtbot.addWidget(widget)

    # Ensure that no rules are set
    assert widget.rules is None

    # Create a rule editor for this widget
    empty = RulesEditor(widget)
    qtbot.addWidget(empty)

    empty.show()

    # Abort the changes
    empty.cancelChanges()

    # Create the rules data for the widget
    rules_list = [{'name': 'Rule #1', 'property': 'Enable',
                   'expression': 'ch[0] > 1',
                   'channels': [
                       {'channel': 'ca://MTEST:Float', 'trigger': True}]}]

    # Add the rules to the widget
    widget.rules = json.dumps(rules_list)

    # Create a new Editor Window
    re = RulesEditor(widget)
    qtbot.addWidget(re)
    re.show()

    assert re.lst_rules.count() == 1
    assert not re.frm_edit.isEnabled()

    re.lst_rules.setCurrentRow(0)
    assert re.frm_edit.isEnabled()
    assert re.txt_name.text() == 'Rule #1'
    assert re.cmb_property.currentText() == 'Enable'
    assert re.tbl_channels.rowCount() == 1
    assert re.tbl_channels.item(0, 0).text() == 'ca://MTEST:Float'
    assert re.tbl_channels.item(0, 1).checkState() == QtCore.Qt.Checked
    assert re.lbl_expected_type.text() == 'bool'
    assert re.txt_expression.text() == 'ch[0] > 1'

    qtbot.keyClicks(re.txt_name, '-Test')
    qtbot.keyClick(re.txt_name, QtCore.Qt.Key_Return)
    assert re.txt_name.text() == 'Rule #1-Test'
    assert re.rules[0]['name'] == 'Rule #1-Test'

    qtbot.mouseClick(re.btn_add_channel, QtCore.Qt.LeftButton)
    re.tbl_channels.item(1, 0).setText("ca://TEST")
    assert re.rules[0]['channels'][1]['channel'] == 'ca://TEST'
    assert re.rules[0]['channels'][1]['trigger'] is False

    re.txt_expression.clear()
    qtbot.keyClicks(re.txt_expression, 'ch[0] < 1')
    qtbot.keyClick(re.txt_expression, QtCore.Qt.Key_Return)
    assert re.txt_expression.text() == 'ch[0] < 1'
    assert re.rules[0]['expression'] == 'ch[0] < 1'

    # Test Delete with Confirm - NO
    assert re.tbl_channels.rowCount() == 2
    re.tbl_channels.setRangeSelected(QTableWidgetSelectionRange(1, 0, 1, 1), True)
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.No)
    qtbot.mouseClick(re.btn_del_channel, QtCore.Qt.LeftButton)
    assert re.tbl_channels.rowCount() == 2

    # Test Delete with Confirm - YES
    re.tbl_channels.setRangeSelected(QTableWidgetSelectionRange(1, 0, 1, 1), True)
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Yes)
    qtbot.mouseClick(re.btn_del_channel, QtCore.Qt.LeftButton)
    assert re.tbl_channels.rowCount() == 1
    assert len(re.rules[0]['channels']) == 1

    # Test Delete with Invalid Selection
    re.tbl_channels.setRangeSelected(QTableWidgetSelectionRange(1, 0, 1, 1), True)
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Yes)
    qtbot.mouseClick(re.btn_del_channel, QtCore.Qt.LeftButton)
    assert re.tbl_channels.rowCount() == 1
    assert len(re.rules[0]['channels']) == 1

    qtbot.mouseClick(re.btn_add_rule, QtCore.Qt.LeftButton)
    assert re.lst_rules.count() == 2
    assert re.frm_edit.isEnabled()
    assert re.txt_name.text() == 'New Rule'
    assert re.cmb_property.currentText() == widget.DEFAULT_RULE_PROPERTY
    assert re.tbl_channels.rowCount() == 0
    assert re.txt_expression.text() == ''

    qtbot.mouseClick(re.btn_add_channel, QtCore.Qt.LeftButton)
    assert re.tbl_channels.item(0, 0).text() == ''
    assert re.tbl_channels.item(0, 1).checkState() == QtCore.Qt.Checked

    qtbot.mouseClick(re.btn_add_channel, QtCore.Qt.LeftButton)
    assert re.tbl_channels.item(1, 0).text() == ''
    assert re.tbl_channels.item(1, 1).checkState() == QtCore.Qt.Unchecked

    # Switch between the rules
    re.lst_rules.setCurrentRow(0)
    re.lst_rules.setCurrentRow(1)

    # Delete Rule 1 - Confirm - NO
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.No)
    qtbot.mouseClick(re.btn_del_rule, QtCore.Qt.LeftButton)
    assert re.lst_rules.count() == 2

    # Delete Rule 1 - Confirm - YES
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Yes)
    qtbot.mouseClick(re.btn_del_rule, QtCore.Qt.LeftButton)
    assert re.frm_edit.isEnabled() is False
    assert re.lst_rules.count() == 1

    re.lst_rules.setCurrentRow(0)
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Yes)
    qtbot.mouseClick(re.btn_del_rule, QtCore.Qt.LeftButton)
    assert re.frm_edit.isEnabled() is False
    assert re.lst_rules.count() == 0

    # Delete Empty List - Confirm - YES
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Yes)
    qtbot.mouseClick(re.btn_del_rule, QtCore.Qt.LeftButton)
    assert re.frm_edit.isEnabled() is False
    assert re.lst_rules.count() == 0


def test_rules_editor_data_valid(qtbot):
    """
    Test the rules form validation.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    """
    def validate(expected_status, expected_msg):
        status, msg = re.is_data_valid()
        assert status == expected_status
        assert expected_msg in msg

    # Create the base widget
    widget = PyDMLabel()
    qtbot.addWidget(widget)

    rules_list = [{'name': 'Rule #1', 'property': 'Enable',
                   'expression': 'ch[0] > 1',
                   'channels': [
                       {'channel': 'ca://MTEST:Float', 'trigger': True}]}]

    # Add the rules to the widget
    widget.rules = json.dumps(rules_list)

    # Ensure that no rules are set
    assert widget.rules is not None

    # Create a rule editor for this widget
    re = RulesEditor(widget)
    qtbot.addWidget(re)

    validate(True, '')

    rules_original = copy.deepcopy(re.rules)

    re.rules[0]['name'] = ''
    validate(False, 'has no name')

    re.rules = copy.deepcopy(rules_original)
    re.rules[0]['expression'] = ''
    validate(False, 'has no expression')

    re.rules = copy.deepcopy(rules_original)
    old_channels = re.rules[0]['channels']
    re.rules[0]['channels'] = []
    validate(False, 'has no channel')
    re.rules[0]['channels'] = old_channels

    re.rules[0]['channels'][0]['trigger'] = False
    validate(False, 'has no channel for trigger')

    re.rules[0]['channels'][0]['channel'] = None
    validate(False, 'Ch. #0 has no channel.')
    re.rules[0]['channels'][0]['channel'] = ''
    validate(False, 'Ch. #0 has no channel.')


def test_rules_editor_open_help(qtbot, monkeypatch):
    """
    Test the Open Help button

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget test
    monkeypatch : fixture
        To override dialog behaviors
    """
    # Create the base widget
    widget = PyDMLabel()
    qtbot.addWidget(widget)

    # Create a new Editor Window
    re = RulesEditor(widget)
    qtbot.addWidget(re)
    re.show()

    re.lst_rules.setCurrentRow(0)

    url = re.open_help(open=False)
    base_url = os.getenv("PYDM_DOCS_URL", "https://slaclab.github.io/pydm")
    exp_url = base_url+"/widgets/widget_rules/index.html"
    assert url == exp_url

    monkeypatch.setattr(webbrowser, 'open',
                        lambda *args, **kwargs: '')
    re.open_help()
