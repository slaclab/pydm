import pytest
import logging

from pydm.widgets.logdisplay import PyDMLogDisplay


@pytest.fixture(scope='module')
def log():
    log = logging.getLogger('log_test.pydm')
    return log


def test_write(qtbot, log):
    logd = PyDMLogDisplay(parent=None, logname=log.name, level=logging.INFO)
    qtbot.addWidget(logd)
    logd.show()
    # Watch our error message show up in the log
    err_msg = 'This is a test of the emergency broadcast system'
    log.error(err_msg)
    assert err_msg in logd.text.toPlainText()
    # Debug shouldn't show up
    debug_msg = 'Pay no attention to the man behind the curtain'
    log.debug(debug_msg)
    assert debug_msg not in logd.text.toPlainText()
    # Change the level so debug does show up
    logd.setLevel('DEBUG')
    assert logd.handler.level == logging.DEBUG
    assert logd.log.level <= logging.DEBUG
    log.debug(debug_msg)
    assert debug_msg in logd.text.toPlainText()
    # Change the name and make sure we still see what we need
    logd.logname = 'log_test'
    info_msg = 'The more things change the more they stay the same'
    log.info(info_msg)
    assert info_msg in logd.text.toPlainText()
