import io
import sys
import traceback
from six.moves import queue
from collections import namedtuple

from qtpy import QtWidgets, QtCore

from .utilities import only_main_thread

"""
Utility functions which installs an exception hook and displays any global 
uncaught exception to operators.

excepthook is based on https://fman.io/blog/pyqt-excepthook/
raise_to_operator is based on https://github.com/pcdshub/typhos/blob/0837405e8d8b73227ac34eb69d2390eed85f3c65/typhos/utils.py#L318
"""


class ExceptionDispatcher(QtCore.QThread):
    """
    Singleton QTread class that receives and dispatch uncaught exceptions via
    the `newException` signal.
    """
    newException = QtCore.Signal(object)

    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = QtCore.QThread.__new__(ExceptionDispatcher,
                                                    *args, **kwargs)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self, *args, **kwargs):
        if self.__initialized:
            return
        super(ExceptionDispatcher, self).__init__(*args, **kwargs)
        self.__initialized = True
        self.app = QtWidgets.QApplication.instance()
        self.app.aboutToQuit.connect(self.requestInterruption)
        self._queue = queue.Queue()

    def add(self, exc_type, exc_value, exc_tb):
        """
        Add an uncaught exception into the Queue.

        Parameters
        ----------
        exc_type : type
            The exception type
        exc_value : Exception
            The exception object
        exc_tb : traceback
            The traceback namedtuple.
        """
        self._queue.put((exc_type, exc_value, exc_tb))

    def run(self):
        def create_entry(entry):
            # Use the Type and message to deduplicate the errors
            key = (entry[0], str(entry[1]))
            return {key: entry}

        while not self.isInterruptionRequested():
            bucket = {}
            # Wait until we have an error
            data = self._queue.get(block=True, timeout=None)  # Block forever
            # Wait a bit to check if we have more
            self.msleep(200)

            bucket.update(create_entry(data))

            # Collect all errors
            while not self._queue.empty():
                data = self._queue.get(block=False)
                bucket.update(create_entry(data))

            # Emit unique errors to listeners
            for _, v in bucket.items():
                self.newException.emit(data)


class DefaultExceptionNotifier(QtCore.QObject):
    """
    Default handler for exceptions which prints at the shell the exception
    and also calls `raise_to_operator` to display a dialog with the exception
    information.
    """
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = QtCore.QObject.__new__(DefaultExceptionNotifier,
                                                    *args, **kwargs)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self, *args, **kwargs):
        if self.__initialized:
            return
        super(DefaultExceptionNotifier, self).__init__(*args, **kwargs)
        self.__initialized = True
        ExceptionDispatcher().newException.connect(self.receiveException)

    @QtCore.Slot(tuple)
    def receiveException(self, exception_data):
        exc_type, exc_value, enriched_tb = exception_data
        traceback.print_exception(exc_type, exc_value, enriched_tb)
        raise_to_operator(exc_value)


_old_excepthook = None

fake_tb = namedtuple(
    'fake_tb', ('tb_frame', 'tb_lasti', 'tb_lineno', 'tb_next')
)


def excepthook(exc_type, exc_value, exc_tb):
    enriched_tb = _add_missing_frames(exc_tb) if exc_tb else exc_tb
    ExceptionDispatcher().add(exc_type, exc_value, enriched_tb)


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


def install(use_default_handler=True):
    """
    Install the exception hook handler.
    If use_dialog is specified, a QMessageBox will also be presented.

    Parameters
    ----------
    use_default_handler : bool
        Whether or not to use the default handler. If not using it, users
        must connect to the `ExceptionDispatcher.newException` signal.
    """
    global _old_excepthook

    if _old_excepthook is None:
        _old_excepthook = sys.excepthook

    dispatcher = ExceptionDispatcher()
    if dispatcher.isRunning():
        return
    if use_default_handler:
        handler = DefaultExceptionNotifier()
    dispatcher.start()
    sys.excepthook = excepthook


def uninstall():
    """
    Uninstall the exception hook handler and revert to the previous value.
    """
    global _old_excepthook

    if _old_excepthook is None:
        return
    sys.excepthook = _old_excepthook
    ExceptionDispatcher().requestInterruption()
    _old_excepthook = None


@only_main_thread
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
