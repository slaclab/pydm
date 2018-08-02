import json
import logging
from qtpy.QtWidgets import QApplication, QWidget, QStyle, QStyleOption
from qtpy.QtGui import QPainter, QPixmap
from qtpy.QtCore import Property, Qt, QSize, QSizeF, QRectF, qInstallMessageHandler
from qtpy.QtSvg import QSvgRenderer
from ..utilities import is_pydm_app
from .base import PyDMWidget

logger = logging.getLogger(__name__)


class PyDMSymbol(QWidget, PyDMWidget):
    """
    PyDMSymbol will render an image (symbol) for each value of a channel.

    Parameters
    ----------
    parent : QWidget
        The parent widget for the Label
    init_channel : str, optional
        The channel to be used by the widget.
    """
    def __init__(self, parent=None, init_channel=None):
        QWidget.__init__(self, parent)
        PyDMWidget.__init__(self, init_channel=init_channel)
        if 'Index' not in PyDMSymbol.RULE_PROPERTIES:
            PyDMSymbol.RULE_PROPERTIES = PyDMWidget.RULE_PROPERTIES.copy()
            PyDMSymbol.RULE_PROPERTIES.update(
                {'Index': ['set_current_key', object]})
        self.app = QApplication.instance()
        self._current_key = 0
        self._state_images_string = ""
        self._state_images = {}  # Keyed on state values (ints), values are (filename, qpixmap or qsvgrenderer) tuples.
        self._aspect_ratio_mode = Qt.KeepAspectRatio
        self._sizeHint = self.minimumSizeHint()
        self._painter = QPainter()

    def init_for_designer(self):
        """
        Method called after the constructor to tweak configurations for
        when using the widget with the Qt Designer
        """
        self.value = 0
        self._current_key = 0

    def set_current_key(self, current_key):
        """
        Change the image being displayed for the one given by `current_key`.

        Parameters
        ----------
        current_key : object
            The current_key parameter can be of any type as long as it matches
            the type used as key for the imageFiles dictionary.

        """
        if self._current_key != current_key:
            self._current_key = current_key
            self.update()

    @Property(str)
    def imageFiles(self):
        """
        JSON-formatted dictionary keyed on states (integers), with filenames
        of the image file to display for the state.

        Returns
        -------
        str
        """
        if not self._state_images:
            return self._state_images_string
        return json.dumps({str(state): val[0] for (state, val) in self._state_images.items()})

    @imageFiles.setter
    def imageFiles(self, new_files):
        """
        JSON-formatted dictionary keyed on states (integers), with filenames
        of the image file to display for the state.

        Parameters
        ----------
        new_files : str
        """
        self._state_images_string = str(new_files)
        try:
            new_file_dict = json.loads(self._state_images_string)
        except Exception:
            self._state_images = {}
            return
        self._sizeHint = QSize(0, 0)
        for (state, filename) in new_file_dict.items():
            if is_pydm_app():
                try:
                    file_path = self.app.get_path(filename)
                except Exception as e:
                    logger.exception("Couldn't get file with path %s", filename)
                    file_path = filename
            else:
                file_path = filename
            # First, lets try SVG.  We have to try SVG first, otherwise
            # QPixmap will happily load the SVG and turn it into a raster image.
            # Really annoying: We have to try to load the file as SVG,
            # and we expect it will fail often (because many images aren't SVG).
            # Qt prints a warning message to stdout any time SVG loading fails.
            # So we have to temporarily silence Qt warning messages here.
            qInstallMessageHandler(self.qt_message_handler)
            svg = QSvgRenderer()
            svg.repaintNeeded.connect(self.update)
            if svg.load(file_path):
                self._state_images[int(state)] = (filename, svg)
                self._sizeHint = self._sizeHint.expandedTo(svg.defaultSize())
                qInstallMessageHandler(None)
                continue
            qInstallMessageHandler(None)
            # SVG didn't work, lets try QPixmap
            image = QPixmap(file_path)
            if not image.isNull():
                self._state_images[int(state)] = (filename, image)
                self._sizeHint = self._sizeHint.expandedTo(image.size())
                continue
            # If we get this far, the file specified could not be loaded at all.
            logger.error("Could not load image: {}".format(filename))
            self._state_images[int(state)] = (filename, None)

    @Property(Qt.AspectRatioMode)
    def aspectRatioMode(self):
        """
        Which aspect ratio mode to use.

        Returns
        -------
        Qt.AspectRatioMode
        """
        return self._aspect_ratio_mode

    @aspectRatioMode.setter
    def aspectRatioMode(self, new_mode):
        """
        Which aspect ratio mode to use.

        Parameters
        -----------
        new_mode : Qt.AspectRatioMode
        """
        if new_mode != self._aspect_ratio_mode:
            self._aspect_ratio_mode = new_mode
            self.update()

    def connection_changed(self, connected):
        """
        Callback invoked when the connection state of the Channel is changed.
        This callback acts on the connection state to enable/disable the widget
        and also trigger the change on alarm severity to ALARM_DISCONNECTED.

        Parameters
        ----------
        connected : int
            When this value is 0 the channel is disconnected, 1 otherwise.
        """
        super(PyDMSymbol, self).connection_changed(connected)
        self.update()

    def value_changed(self, new_val):
        """
        Callback invoked when the Channel value is changed.

        Parameters
        ----------
        new_val : int
            The new value from the channel.
        """
        super(PyDMSymbol, self).value_changed(new_val)
        self._current_key = new_val
        self.update()

    def sizeHint(self):
        """
        This property holds the recommended size for the widget.

        Returns
        -------
        QSize
        """
        return self._sizeHint

    def minimumSizeHint(self):
        """
        This property holds the recommended minimum size for the widget.

        Returns
        -------
        QSize
        """
        return QSize(10, 10)  # This is totally arbitrary, I just want *some* visible nonzero size

    def paintEvent(self, event):
        """
        Paint events are sent to widgets that need to update themselves,
        for instance when part of a widget is exposed because a covering
        widget was moved.

        At PyDMSymbol this method handles the alarm painting with parameters
        from the stylesheet and draws the proper image.

        Parameters
        ----------
        event : QPaintEvent
        """
        self._painter.begin(self)
        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, self._painter, self)
        # self._painter.setRenderHint(QPainter.Antialiasing)
        if self._current_key is None:
            self._painter.end()
            return
        image_to_draw = self._state_images.get(self._current_key, (None, None))[1]
        if image_to_draw is None:
            self._painter.end()
            return
        if isinstance(image_to_draw, QPixmap):
            w = float(image_to_draw.width())
            h = float(image_to_draw.height())
            if self._aspect_ratio_mode == Qt.IgnoreAspectRatio:
                scale = (event.rect().width() / w, event.rect().height() / h)
            elif self._aspect_ratio_mode == Qt.KeepAspectRatio:
                sf = min(event.rect().width() / w, event.rect().height() / h)
                scale = (sf, sf)
            elif self._aspect_ratio_mode == Qt.KeepAspectRatioByExpanding:
                sf = max(event.rect().width() / w, event.rect().height() / h)
                scale = (sf, sf)
            self._painter.scale(scale[0], scale[1])
            self._painter.drawPixmap(event.rect().x(), event.rect().y(), image_to_draw)
        elif isinstance(image_to_draw, QSvgRenderer):
            draw_size = QSizeF(image_to_draw.defaultSize())
            draw_size.scale(QSizeF(event.rect().size()), self._aspect_ratio_mode)
            image_to_draw.render(self._painter, QRectF(0.0, 0.0, draw_size.width(), draw_size.height()))
        self._painter.end()

    def qt_message_handler(self, msg_type, *args):
        # Intentionally suppress all qt messages.  Make sure not to leave this handler installed.
        pass
