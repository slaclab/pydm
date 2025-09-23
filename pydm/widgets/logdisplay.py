import logging
import functools

from collections import OrderedDict

from qtpy.QtCore import QObject, Slot, Signal, QSize
from qtpy.QtWidgets import (
    QWidget,
    QPlainTextEdit,
    QComboBox,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QStyleOption,
    QStyle,
)
from qtpy.QtGui import QPainter
from pydm.utilities import ACTIVE_QT_WRAPPER, QtWrapperTypes

if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYSIDE6:
    from PySide6.QtCore import Property
else:
    from PyQt5.QtCore import pyqtProperty as Property

logger = logging.getLogger(__name__)


def logger_destroyed(log):
    """
    Callback invoked when the Widget is destroyed.
    This method is used to ensure that the log handlers are cleared.

    Parameters
    ----------
    log : Logger
        The logger object being used by the PyDMLogDisplay widget.
    """
    if log:
        for handler in log.handlers:
            log.removeHandler(handler)


class GuiHandler(QObject, logging.Handler):
    """
    Handler for PyDM Applications

    A composite of a QObject and a logging handler. This can be added to a
    ``logging.Logger`` object just like any standard ``logging.Handler`` and
    will emit logging messages as Signals

    .. code:: python

        # Create a log and GuiHandler
        logger = logging.getLogger()
        ui_handler = GuiHandler(level=logging.INFO)
        # Attach our handler to the log
        logger.addHandler(ui_handler)
        # Publish log message via Signal
        ui_handler.message.connect(mySlot)

    Parameters
    ----------
    level: int
        Level of Handler

    parent: QObject, optional
    """

    message = Signal(str)

    def __init__(self, level=logging.NOTSET, parent=None):
        logging.Handler.__init__(self, level=level)
        QObject.__init__(self, parent)

    def emit(self, record):
        """Emit formatted log messages when received but only if level is set."""
        # Avoid garbage to be presented when master log is running with DEBUG.
        if self.level == logging.NOTSET:
            return
        try:
            self.message.emit(self.format(record))
        except RuntimeError:
            logger.debug("Handler was destroyed at the C++ level.")


class LogLevels(object):
    NOTSET = 0
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    @staticmethod
    def as_dict():
        """
        Returns an ordered dict of LogLevels ordered by value.

        Returns
        -------
        OrderedDict
        """
        # First let's remove the internals
        entries = [
            (k, v)
            for k, v in LogLevels.__dict__.items()
            if not k.startswith("__") and not callable(v) and not isinstance(v, staticmethod)
        ]

        return OrderedDict(sorted(entries, key=lambda x: x[1], reverse=False))


# @QT_WRAPPER_SPECIFIC
if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYSIDE6:
    from PySide6.QtCore import QEnum
    from enum import Enum

    @QEnum
    class LogLevels(Enum):  # noqa F811
        NOTSET = 0
        DEBUG = 10
        INFO = 20
        WARNING = 30
        ERROR = 40
        CRITICAL = 50

        @staticmethod
        def as_dict():
            """
            Returns an ordered dict of LogLevels ordered by value.
            Returns
            -------
            OrderedDict
            """
            # First let's remove the internals
            entries = [(k, v.value) for k, v in LogLevels.__members__.items()]
            return OrderedDict(sorted(entries, key=lambda x: x[1], reverse=False))


class PyDMLogDisplay(QWidget):
    """
    Standard display for Log Output

    This widget handles instantiating a ``GuiHandler`` and displaying log
    messages to a ``QPlainTextEdit``. The level of the log can be changed from
    inside the widget itself, allowing users to select from any of the
    ``.levels`` specified by the widget.

    Parameters
    ----------
    parent : QObject, optional

    logname : str
        Name of log to display in widget

    level : logging.Level
        Initial level of log display

    """

    if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYQT5:
        from PyQt5.QtCore import Q_ENUM

        Q_ENUM(LogLevels)
    LogLevels = LogLevels

    # Make enum definitions known to this class
    NOTSET = LogLevels.NOTSET
    DEBUG = LogLevels.DEBUG
    INFO = LogLevels.INFO
    WARNING = LogLevels.WARNING
    ERROR = LogLevels.ERROR
    CRITICAL = LogLevels.CRITICAL

    terminator = "\n"
    default_format = "%(asctime)s %(message)s"
    default_level = logging.INFO

    def __init__(self, parent=None, logname=None, level=logging.NOTSET):
        QWidget.__init__(self, parent)
        # Create Widgets
        self.label = QLabel("Minimum displayed log level: ", parent=self)
        self.combo = QComboBox(parent=self)
        self.text = QPlainTextEdit(parent=self)
        self.text.setReadOnly(True)
        self.clear_btn = QPushButton("Clear", parent=self)
        # Create layout
        layout = QVBoxLayout()
        level_control = QHBoxLayout()
        level_control.addWidget(self.label)
        level_control.addWidget(self.combo)
        layout.addLayout(level_control)
        layout.addWidget(self.text)
        layout.addWidget(self.clear_btn)
        self.setLayout(layout)
        # Allow QCombobox to control log level
        for log_level, value in LogLevels.as_dict().items():
            self.combo.addItem(log_level, value)
        self.combo.currentTextChanged.connect(self.setLevel)
        # Allow QPushButton to clear log text
        self.clear_btn.clicked.connect(self.clear)
        # Create a handler with the default format
        self.handler = GuiHandler(level=level, parent=self)
        self.logFormat = self.default_format
        self.handler.message.connect(self.write)
        # Create logger. Either as a root or given logname
        self.log = None
        self.level = None
        self.logName = logname or ""
        self.logLevel = level
        self.destroyed.connect(functools.partial(logger_destroyed, self.log))

    def sizeHint(self):
        return QSize(400, 300)

    def readLogLevel(self) -> LogLevels:
        return self.level

    def setLogLevel(self, level) -> None:
        if level != self.level:
            self.level = level
            idx = self.combo.findData(level)
            self.combo.setCurrentIndex(idx)

    logLevel = Property(LogLevels, readLogLevel, setLogLevel)

    def readLogName(self) -> str:
        """Name of associated log"""
        return self.log.name

    def setLogName(self, name) -> None:
        # Disconnect prior log from handler
        if self.log:
            self.log.removeHandler(self.handler)
        # Reattach handler to new handler
        self.log = logging.getLogger(name)
        # Ensure that the log matches level of handler
        # only if the handler level is less than the log.
        if self.log.level < self.handler.level:
            self.log.setLevel(self.handler.level)
        # Attach preconfigured handler
        self.log.addHandler(self.handler)

    logName = Property(str, readLogName, setLogName)

    def readLogFormat(self) -> str:
        """Format for log messages"""
        return self.handler.formatter._fmt

    def setLogFormat(self, fmt) -> None:
        self.handler.setFormatter(logging.Formatter(fmt))

    logFormat = Property(str, readLogFormat, setLogFormat)

    @Slot(str)
    def write(self, message):
        """Write a message to the log display"""
        # We split the incoming message by new lines. In prior iterations of
        # this widget it was discovered that large blocks of text cause issues
        # at the Qt level.
        for msg in message.split(self.terminator):
            self.text.appendPlainText(msg)

    @Slot()
    def clear(self):
        """Clear the text area."""
        self.text.clear()

    @Slot(str)
    def setLevel(self, level):
        """Set the level of the contained logger"""
        # Get the level from the incoming string specification
        try:
            level = getattr(logging, level.upper())
        except AttributeError:
            logger.exception("Invalid logging level specified %s", level.upper())
        else:
            # Set the existing handler and logger to this level
            self.handler.setLevel(level)
            if self.log.level > self.handler.level or self.log.level == logging.NOTSET:
                self.log.setLevel(self.handler.level)

    def paintEvent(self, _):
        """
        Paint events are sent to widgets that need to update themselves,
        for instance when part of a widget is exposed because a covering
        widget was moved.

        At PyDMDrawing this method handles the alarm painting with parameters
        from the stylesheet, configures the brush, pen and calls ```draw_item```
        so the specifics can be performed for each of the drawing classes.

        Parameters
        ----------
        event : QPaintEvent
        """
        painter = QPainter(self)
        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)
        painter.setRenderHint(QPainter.Antialiasing)
