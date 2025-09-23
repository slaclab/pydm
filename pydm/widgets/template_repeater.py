import os
import json
import copy
import logging
from qtpy.QtWidgets import QFrame, QApplication, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QStyle, QSizePolicy, QLayout
from qtpy.QtCore import Qt, QSize, QRect, QPoint
from .base import PyDMPrimitiveWidget
from pydm.utilities import is_qt_designer
import pydm.data_plugins
from pydm.utilities import find_file
from pydm.display import load_file
from pydm.utilities import ACTIVE_QT_WRAPPER, QtWrapperTypes
from pydm.utilities import ACTIVE_QT_WRAPPER, QtWrapperTypes

if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYSIDE6:
    from PySide6.QtCore import Property
else:
    from PyQt5.QtCore import pyqtProperty as Property

logger = logging.getLogger(__name__)


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=-1, h_spacing=-1, v_spacing=-1):
        QLayout.__init__(self, parent)
        self.setContentsMargins(margin, margin, margin, margin)
        self.m_h_space = h_spacing
        self.m_v_space = v_spacing
        self.item_list = []

    def addItem(self, item):
        self.item_list.append(item)

    def horizontalSpacing(self):
        if self.m_h_space >= 0:
            return self.m_h_space
        else:
            return self.smart_spacing(QStyle.PM_LayoutHorizontalSpacing)

    def verticalSpacing(self):
        if self.m_v_space >= 0:
            return self.m_v_space
        else:
            return self.smart_spacing(QStyle.PM_LayoutVerticalSpacing)

    def count(self):
        return len(self.item_list)

    def itemAt(self, index):
        if index >= 0 and index < len(self.item_list):
            return self.item_list[index]
        else:
            return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.item_list):
            return self.item_list.pop(index)
        else:
            return None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        # size += QSize(2*self.margin(), 2*self.margin())
        size += QSize(2 * 8, 2 * 8)
        return size

    def do_layout(self, rect, test_only):
        (left, top, right, bottom) = self.getContentsMargins()
        effective_rect = rect.adjusted(left, top, -right, -bottom)
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0
        for item in self.item_list:
            wid = item.widget()
            space_x = self.horizontalSpacing()
            if space_x == -1:
                space_x = wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            space_y = self.verticalSpacing()
            if space_y == -1:
                space_y = wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = next_x
            line_height = max(line_height, item.sizeHint().height())
        return y + line_height - rect.y() + bottom

    def smart_spacing(self, pm):
        parent = self.parent()
        if not parent:
            return -1
        elif parent.isWidgetType():
            return parent.style().pixelMetric(pm, None, parent)
        else:
            return parent.spacing()


class LayoutType(object):
    Vertical = 0
    Horizontal = 1
    Flow = 2


# @QT_WRAPPER_SPECIFIC
if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYSIDE6:
    from PySide6.QtCore import QEnum
    from enum import Enum

    @QEnum
    # overrides prev enum def
    class LayoutType(Enum):  # noqa F811
        Vertical = 0
        Horizontal = 1
        Flow = 2


layout_class_for_type = {
    LayoutType.Vertical: QVBoxLayout,
    LayoutType.Horizontal: QHBoxLayout,
    LayoutType.Flow: FlowLayout,
}


class PyDMTemplateRepeater(QFrame, PyDMPrimitiveWidget):
    """
    PyDMTemplateRepeater takes a .ui file with macro variables as a template, and a JSON
    file (or a list of dictionaries) with a list of values to use to fill in
    the macro variables, then creates a layout with one instance of the
    template for each item in the list.

    It can be very convenient if you have displays that repeat the same set of
    widgets over and over - for instance, if you have a standard set of
    controls for a magnet, and want to build a display with a list of controls
    for every magnet, the Template Repeater lets you do that with a minimum
    amount of work: just build a template for a single magnet, and a JSON list
    with the data that describes all of the magnets.

    Parameters
    ----------
    parent : optional
        The parent of this widget.
    """

    if ACTIVE_QT_WRAPPER == QtWrapperTypes.PYQT5:
        from PyQt5.QtCore import Q_ENUM

        Q_ENUM(LayoutType)
    LayoutType = LayoutType

    # Make enum definitions known to this class
    Vertical = LayoutType.Vertical
    Horizontal = LayoutType.Horizontal
    Flow = LayoutType.Flow

    def __init__(self, parent=None):
        pydm.data_plugins.initialize_plugins_if_needed()
        QFrame.__init__(self, parent)
        PyDMPrimitiveWidget.__init__(self)
        self._template_filename = ""
        self._recursive_template_search = False
        self._count_shown_in_designer = 1
        self._data_source = ""
        self._data = []
        self._recursive_data_search = False
        self._cached_template = None
        self._parent_macros = None
        self._layout_type = LayoutType.Vertical
        self._temp_layout_spacing = 4
        self.app = QApplication.instance()
        self.rebuild()

    def readLayoutType(self) -> LayoutType:
        """
        The layout type to use.

        Returns
        -------
        LayoutType
        """
        return self._layout_type

    def setLayoutType(self, new_type) -> None:
        """
        The layout type to use.
        Options are:
        - **Vertical**: Instances of the template are laid out vertically, in rows.
        - **Horizontal**: Instances of the template are laid out horizontally, in columns.
        - **Flow**: Instances of the template are laid out horizontally until they reach the edge of the template,
        at which point they "wrap" into a new row.

        Parameters
        ----------
        new_type : LayoutType
        """
        if new_type != self._layout_type:
            self._layout_type = new_type
            self.rebuild()

    layoutType = Property(LayoutType, readLayoutType, setLayoutType)

    def readLayoutSpacing(self) -> int:
        if self.layout():
            return self.layout().spacing()
        return self._temp_layout_spacing

    def setLayoutSpacing(self, new_spacing) -> None:
        self._temp_layout_spacing = new_spacing
        if self.layout():
            self.layout().setSpacing(new_spacing)

    layoutSpacing = Property(int, readLayoutSpacing, setLayoutSpacing)

    def readCountShownInDesigner(self) -> int:
        """
        The number of instances to show in Qt Designer.  This property has no
        effect outside of Designer.

        Returns
        -------
        int
        """
        return self._count_shown_in_designer

    def setCountShownInDesigner(self, new_count) -> None:
        """
        The number of instances to show in Qt Designer.  This property has no
        effect outside of Designer.

        Parameters
        ----------
        new_count : int
        """
        if not is_qt_designer():
            return
        try:
            new_count = int(new_count)
        except ValueError:
            logger.exception("Couldn't convert {} to integer.".format(new_count))
            return
        new_count = max(new_count, 0)
        if new_count != self._count_shown_in_designer:
            self._count_shown_in_designer = new_count
            self.rebuild()

    countShownInDesigner = Property(int, readCountShownInDesigner, setCountShownInDesigner)

    def readTemplateFilename(self) -> str:
        """
        The path to the .ui file to use as a template.

        Returns
        -------
        str
        """
        return self._template_filename

    def setTemplateFilename(self, new_filename) -> None:
        """
        The path to the .ui file to use as a template.

        Parameters
        ----------
        new_filename : str
        """
        if new_filename != self._template_filename:
            self._template_filename = new_filename
            self._cached_template = None
            if self._template_filename:
                self.rebuild()
            else:
                self.clear()

    templateFilename = Property(str, readTemplateFilename, setTemplateFilename)

    def readRecursiveTemplateSearch(self) -> bool:
        """
        Whether or not to search for a provided template file recursively
        in subfolders relative to the location of this widget.

        Returns
        -------
        bool
            If recursive search is enabled.
        """
        return self._recursive_template_search

    def setRecursiveTemplateSearch(self, new_value) -> None:
        """
        Set whether or not to search for a provided template file recursively
        in subfolders relative to the location of this widget.

        Parameters
        ----------
        new_value
            If recursive search should be enabled.
        """
        self._recursive_template_search = new_value

    recursiveTemplateSearch = Property(bool, readRecursiveTemplateSearch, setRecursiveTemplateSearch)

    def _is_json(self, source):
        """
        Validate if the string source is a valid json.

        Parameters
        ----------
        source : str

        Returns
        -------
        tuple (bool, obj)
            True if a valid json or False otherwise.
            Obj will either be the dictionary data or the exception while trying
            to load the JSON string.
        """
        try:
            data = json.loads(source)
            return True, data
        except Exception as ex:
            return False, ex

    def readDataSource(self) -> str:
        """
        The path to the JSON file or a valid JSON string to fill in each
        instance of the template.

        Returns
        -------
        str
        """
        return self._data_source

    def setDataSource(self, data_source) -> None:
        """
        Sets the path to the JSON file or a valid JSON string to fill in each
        instance of the template.

        For example, if you build a template that contains two macro variables,
        ${NAME} and ${UNIT}, your JSON file should be a list of dictionaries,
        each with keys for NAME and UNIT, like this:

        [{"NAME": "First Device", "UNIT": 1}, {"NAME": "Second Device", "UNIT": 2}]

        Parameters
        -------
        data_source : str
        """
        if data_source != self._data_source:
            self._data_source = data_source
            if self._data_source:
                is_json, data = self._is_json(data_source)
                if is_json:
                    logger.debug("TemplateRepeater dataSource is a valid JSON.")
                    self.data = data
                else:
                    logger.debug("TemplateRepeater dataSource is not a valid JSON. Assuming it is a file path.")
                    try:
                        parent_display = self.find_parent_display()
                        base_path = None
                        if parent_display:
                            base_path = os.path.dirname(parent_display.loaded_file())
                        fname = find_file(
                            self._data_source,
                            base_path=base_path,
                            raise_if_not_found=True,
                            subdir_scan_enabled=self._recursive_data_search,
                        )

                        if not fname:
                            if not is_qt_designer():
                                logger.error(
                                    "Cannot locate data source file {} for PyDMTemplateRepeater.".format(
                                        self._data_source
                                    )
                                )
                            self.data = []
                        else:
                            with open(fname) as f:
                                try:
                                    self.data = json.load(f)
                                except ValueError:
                                    logger.error(
                                        "Failed to parse data source file {} for PyDMTemplateRepeater.".format(fname)
                                    )
                                    self.data = []
                    except IOError:
                        self.data = []
            else:
                self.clear()

    dataSource = Property(str, readDataSource, setDataSource)

    def readRecursiveDataSearch(self) -> bool:
        """
        Whether or not to search for a provided data file recursively
        in subfolders relative to the location of this widget.

        Returns
        -------
        bool
            If recursive search is enabled.
        """
        return self._recursive_data_search

    def setRecursiveDataSearch(self, new_value) -> None:
        """
        Set whether or not to search for a provided data file recursively
        in subfolders relative to the location of this widget.

        Parameters
        ----------
        new_value
            If recursive search should be enabled.
        """
        self._recursive_data_search = new_value

    recursiveDataSearch = Property(bool, readRecursiveDataSearch, setRecursiveDataSearch)

    def open_template_file(self, variables=None):
        """
        Opens the widget specified in the templateFilename property.

        Parameters
        ----------
        variables : dict
            A dictionary of macro variables to apply when loading, in addition
            to all the macros specified on the template repeater widget.
        Returns
        -------
        display : QWidget
        """
        if not variables:
            variables = {}

        parent_display = self.find_parent_display()
        base_path = None
        if parent_display:
            base_path = os.path.dirname(parent_display.loaded_file())
        fname = find_file(
            self.templateFilename,
            base_path=base_path,
            raise_if_not_found=True,
            subdir_scan_enabled=self._recursive_template_search,
        )

        if self._parent_macros is None:
            self._parent_macros = {}
            if parent_display:
                self._parent_macros = parent_display.macros()

        parent_macros = copy.copy(self._parent_macros)
        parent_macros.update(variables)
        try:
            w = load_file(fname, macros=parent_macros, target=None)
        except Exception as ex:
            w = QLabel("Error: could not load template: " + str(ex))
        return w

    def rebuild(self):
        """Clear out all existing widgets, and populate the list using the
        template file and data source."""
        self.clear()
        if (not self.templateFilename) or (not self.data):
            return
        self.setUpdatesEnabled(False)

        layout_class = layout_class_for_type[self.layoutType]
        if type(self.layout()) != layout_class:
            if self.layout() is not None:
                # Trick to remove the existing layout by re-parenting it in an empty widget.
                QWidget().setLayout(self.layout())
            currLayoutClass = layout_class(self)
            self.setLayout(currLayoutClass)
            self.layout().setSpacing(self._temp_layout_spacing)
        try:
            with pydm.data_plugins.connection_queue(defer_connections=True):
                for i, variables in enumerate(self.data):
                    if is_qt_designer() and i > self.countShownInDesigner - 1:
                        break
                    w = self.open_template_file(variables)
                    if w is None:
                        w = QLabel()
                        w.setText("No Template Loaded.  Data: {}".format(variables))
                    w.setParent(self)
                    self.layout().addWidget(w)
        except Exception:
            logger.exception("Template repeater failed to rebuild.")
        finally:
            # If issues happen during the rebuild we should still enable
            # updates and establish connection for the widgets added.
            # Moreover, if we dont call establish_queued_connections
            # the queue will never be emptied and new connections will be
            # staled.
            self.setUpdatesEnabled(True)
            pydm.data_plugins.establish_queued_connections()

    def clear(self):
        """Clear out any existing instances of the template inside
        the widget."""
        if not self.layout():
            return
        while self.layout().count() > 0:
            item = self.layout().takeAt(0)
            item.widget().deleteLater()
            del item

    def count(self):
        if not self.layout():
            return 0
        return self.layout().count()

    @property
    def data(self):
        """
        The dictionary used by the widget to fill in each instance of the template.
        This property will be overwritten if the user changes the dataSource
        property.
        """
        return self._data

    @data.setter
    def data(self, new_data):
        """
        Sets the dictionary used by the widget to fill in each instance of
        the template.  This property will be overwritten if the user changes
        the dataSource property.  After setting this property, `rebuild`
        is automatically called to refresh the widget.
        """
        self._data = new_data
        self.rebuild()
