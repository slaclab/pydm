import pytest
import logging

from qtpy.QtWidgets import QApplication, QWidget
from pydm.widgets.logdisplay import PyDMLogDisplay


@pytest.fixture(scope="module")
def log():
    log = logging.getLogger("log_test.pydm")
    return log


def test_write(qtbot, log):
    parent = QWidget()
    qtbot.addWidget(parent)

    logd = PyDMLogDisplay(parent=parent, logname=log.name, level=logging.INFO)
    qtbot.addWidget(logd)
    logd.show()
    assert logd.logLevel == logging.INFO
    assert logd.logName == log.name
    assert logd.parent() == parent

    # Watch our error message show up in the log
    err_msg = "This is a test of the emergency broadcast system"
    log.error(err_msg)
    assert err_msg in logd.text.toPlainText()
    # Debug shouldn't show up
    debug_msg = "Pay no attention to the man behind the curtain"
    log.debug(debug_msg)
    assert debug_msg not in logd.text.toPlainText()
    # Change the level so debug does show up
    logd.setLevel("DEBUG")
    assert logd.handler.level == logging.DEBUG
    assert logd.log.level <= logging.DEBUG
    log.debug(debug_msg)
    assert debug_msg in logd.text.toPlainText()
    # Change the name and make sure we still see what we need
    logd.logname = "log_test"
    info_msg = "The more things change the more they stay the same"
    log.info(info_msg)
    assert info_msg in logd.text.toPlainText()
    logd.clear()
    assert logd.text.toPlainText() == ""

    # Calling .deleteLater() here on pyside6 causes weird behavior with the underlying c++ object in next testcase,
    # maybe since the logger is associated with the previous logd instance when it gets deleted?


def test_handler_cleanup(qtbot, log):
    logd = PyDMLogDisplay(logname=log.name, level=logging.DEBUG)
    qtbot.addWidget(logd)
    del logd
    log.error("This will explode if the handler does not exist")
    assert log.handlers == []
