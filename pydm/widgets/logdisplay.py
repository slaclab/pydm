import logging

from pydm.PyQt.QtCore import QObject, pyqtSlot, pyqtSignal, pyqtProperty
from pydm.PyQt.QtGui import (QWidget, QPlainTextEdit, QComboBox, QLabel,
                             QHBoxLayout, QVBoxLayout)

logger = logging.getLogger(__name__)


class GuiHandler(QObject, logging.Handler):
    """
    Handler for PyDM Applications

    A composite of a QObject and a logging handler. This can be added to a
    ``logging.Logger`` object just like any standard ``logging.Handler`` and
    will emit logging messages as pyqtSignals

    .. code:: python

        # Create a log and GuiHandler
        logger = logging.getLogger()
        ui_handler = GuiHandler(level=logging.INFO)
        # Attach our handler to the log
        logger.addHandler(ui_handler)
        # Publish log message via pyqtSignal
        ui_handler.message.connect(mySlot)

    Parameters
    ----------
    level: int
        Level of Handler

    parent: QObject, optional
    """
    message = pyqtSignal(str)

    def __init__(self, level=logging.NOTSET, parent=None):
        logging.Handler.__init__(self, level=level)
        QObject.__init__(self)
        # Set the parent widget
        self.setParent(parent)

    def emit(self, record):
        """Emit formatted log messages when received"""
        self.message.emit(self.format(record))


class PyDMLogDisplay(QWidget):
    """
    Standard display for Log Output

    This widget handles instantating a ``GuiHandler`` and displaying log
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
    terminator = '\n'
    levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    default_format = '%(asctime)s %(message)s'
    default_level = logging.INFO

    def __init__(self, parent=None, logname=None, level=logging.NOTSET):
        QWidget.__init__(self, parent=parent)
        # Create Widgets
        self.label = QLabel('Minimum displayed log level: ')
        self.combo = QComboBox()
        self.text = QPlainTextEdit()
        # Create layout
        layout = QVBoxLayout()
        level_control = QHBoxLayout()
        level_control.addWidget(self.label)
        level_control.addWidget(self.combo)
        layout.addLayout(level_control)
        layout.addWidget(self.text)
        self.setLayout(layout)
        # Allow QCombobox to control log level
        self.combo.addItems(self.levels)
        self.combo.currentIndexChanged[str].connect(self.set_level)
        # Create a handler with the default format
        self.handler = GuiHandler(level=level, parent=self)
        self.logformat = self.default_format
        self.handler.message.connect(self.write)
        # Create logger. Either as a root or given logname
        self.log = None
        self.logname = logname or ''

    @pyqtProperty(str)
    def logname(self):
        """Name of associated log"""
        return self.log.name

    @logname.setter
    def logname(self, name):
        # Disconnect prior log from handler
        if self.log:
            self.log.removeHandler(self.handler)
        # Reattach handler to new handler
        self.log = logging.getLogger(name)
        # Ensure that the log matches level of handler
        self.log.setLevel(self.handler.level)
        # Attach preconfigured handler
        self.log.addHandler(self.handler)

    @pyqtProperty(str)
    def logformat(self):
        """Format for log messages"""
        return self.handler.formatter._fmt

    @logformat.setter
    def logformat(self, fmt):
        self.handler.setFormatter(logging.Formatter(fmt))

    @pyqtSlot(str)
    def write(self, message):
        """Write a message to the log display"""
        # We split the incoming message by new lines. In prior iterations of
        # this widget it was discovered that large blocks of text cause issues
        # at the Qt level.
        for msg in message.split(self.terminator):
            self.text.appendPlainText(msg)

    @pyqtSlot(str)
    def set_level(self, level):
        """Set the level of the contained logger"""
        # Get the level from the incoming string specification
        try:
            level = getattr(logging, level.upper())
        except AttributeError as exc:
            logger.exception("Invalid logging level specified %s",
                             level.upper())
        else:
            # Set the existing handler and logger to this level
            self.log.setLevel(level)
            self.handler.setLevel(level)
