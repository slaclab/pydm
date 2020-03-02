import io
import sys
import traceback
from collections import namedtuple
from qtpy import QtWidgets


class QtExceptionHandler:
    """Utility class which installs an exception hook and displays any global uncaught exception to
    operators.

    excepthook is based on https://fman.io/blog/pyqt-excepthook/
    raise_to_operator is based on https://github.com/pcdshub/typhos/blob/0837405e8d8b73227ac34eb69d2390eed85f3c65/typhos/utils.py#L318
    """
    _use_dialog = True
    _old_excepthook = None

    fake_tb = namedtuple(
        'fake_tb', ('tb_frame', 'tb_lasti', 'tb_lineno', 'tb_next')
    )

    @staticmethod
    def excepthook(exc_type, exc_value, exc_tb):
        enriched_tb = QtExceptionHandler._add_missing_frames(
            exc_tb) if exc_tb else exc_tb

        # Note: sys.__excepthook__(...) would not work here.
        # We need to use print_exception(...):
        traceback.print_exception(exc_type, exc_value, enriched_tb)
        if QtExceptionHandler._use_dialog:
            QtExceptionHandler.raise_to_operator(exc_value)

    @staticmethod
    def _add_missing_frames(tb):
        result = QtExceptionHandler.fake_tb(tb.tb_frame, tb.tb_lasti,
                                            tb.tb_lineno, tb.tb_next)
        frame = tb.tb_frame.f_back
        while frame:
            result = QtExceptionHandler.fake_tb(frame, frame.f_lasti,
                                                frame.f_lineno, result)
            frame = frame.f_back
        return result

    @staticmethod
    def install(use_dialog=True):
        """
        Install the exception hook handler.
        If use_dialog is specified, a QMessageBox will also be presented.

        Parameters
        ----------
        use_dialog : bool
            Wether or not to display a QMessageBox to the operator.
        """
        if QtExceptionHandler._old_excepthook is None:
            QtExceptionHandler._old_excepthook = sys.excepthook
        QtExceptionHandler._use_dialog = use_dialog
        sys.excepthook = QtExceptionHandler.excepthook

    @staticmethod
    def uninstall():
        """
        Uninstall the exception hook handler and revert to the previous value.
        """
        if QtExceptionHandler._old_excepthook is None:
            return
        sys.excepthook = QtExceptionHandler._old_excepthook
        QtExceptionHandler._old_excepthook = None

    @staticmethod
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
