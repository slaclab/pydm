import io
import sys
import traceback
from collections import namedtuple

from qtpy import QtWidgets

"""
Utility functions which installs an exception hook and displays any global 
uncaught exception to operators.

excepthook is based on https://fman.io/blog/pyqt-excepthook/
raise_to_operator is based on https://github.com/pcdshub/typhos/blob/0837405e8d8b73227ac34eb69d2390eed85f3c65/typhos/utils.py#L318
"""


_use_dialog = True
_old_excepthook = None

fake_tb = namedtuple(
    'fake_tb', ('tb_frame', 'tb_lasti', 'tb_lineno', 'tb_next')
)


def excepthook(exc_type, exc_value, exc_tb):
    global _use_dialog

    enriched_tb = _add_missing_frames(exc_tb) if exc_tb else exc_tb

    # Note: sys.__excepthook__(...) would not work here.
    # We need to use print_exception(...):
    traceback.print_exception(exc_type, exc_value, enriched_tb)
    if _use_dialog:
        raise_to_operator(exc_value)


def _add_missing_frames(tb):
    """
    Originally from: https://fman.io/blog/pyqt-excepthook/

    When an exception occurs in Python, sys.excepthook(...) is called with an
    exc_tb parameter. This parameter contains the information for each of the
    lines in the Tracebacks shown above. The reason why the first version of
    our code did not include f() in the traceback was that it did not appear
    in exc_tb.

    To fix the problem, our additional excepthook code above creates a "fake"
    traceback that includes the missing entries. Fortunately, the necessary
    information is available in the .tb_frame property of the original
    traceback. Finally, the default sys.__excepthook__(...) does not work with
    fake data, so we need to call traceback.print_exception(...) instead.
    """
    result = fake_tb(tb.tb_frame, tb.tb_lasti,
                     tb.tb_lineno, tb.tb_next)
    frame = tb.tb_frame.f_back
    while frame:
        result = fake_tb(frame, frame.f_lasti,
                         frame.f_lineno, result)
        frame = frame.f_back
    return result


def install(use_dialog=True):
    """
    Install the exception hook handler.
    If use_dialog is specified, a QMessageBox will also be presented.

    Parameters
    ----------
    use_dialog : bool
        Wether or not to display a QMessageBox to the operator.
    """
    global _old_excepthook
    global _use_dialog

    if _old_excepthook is None:
        _old_excepthook = sys.excepthook

    _use_dialog = use_dialog
    sys.excepthook = excepthook

def uninstall():
    """
    Uninstall the exception hook handler and revert to the previous value.
    """
    global _old_excepthook

    if _old_excepthook is None:
        return
    sys.excepthook = _old_excepthook
    _old_excepthook = None


def raise_to_operator(exc):
    """Utility function to show an Exception to the operator"""
    err_msg = QtWidgets.QMessageBox()
    err_msg.setText('{}: {}'.format(exc.__class__.__name__, exc))
    err_msg.setWindowTitle(type(exc).__name__)
    err_msg.setIcon(QtWidgets.QMessageBox.Critical)
    handle = io.StringIO()
    traceback.print_tb(exc.__traceback__, file=handle)
    handle.seek(0)
    err_msg.setDetailedText(handle.read())
    err_msg.exec_()
    return err_msg
