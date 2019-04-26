import os
import json
import logging
from qtpy.QtWidgets import (QFrame, QApplication, QLabel, QVBoxLayout,
                           QHBoxLayout, QWidget, QStyle, QSizePolicy,
                           QLayout, QListWidget, QListWidgetItem)
from qtpy.QtCore import Qt, QSize, QRect, Slot, Property, QPoint, QUrl, Q_ENUMS
from qtpy import uic
from .base import PyDMPrimitiveWidget, PyDMWidget
from .embedded_display import PyDMEmbeddedDisplay
from pydm.utilities import is_qt_designer, is_pydm_app
import pydm.data_plugins
from ..utilities import macro
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
        return self.do_layout(QRect(0,0, width, 0), True)
    
    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.do_layout(rect, False)
    
    def sizeHint(self):
        return self.minimumSize()
    
    def minimumSize(self):
        size = QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        #size += QSize(2*self.margin(), 2*self.margin())
        size += QSize(2*8, 2*8)
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

layout_class_for_type = (QVBoxLayout, QHBoxLayout, FlowLayout)

class PyDMTemplateRepeater(QFrame, PyDMPrimitiveWidget, LayoutType):
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
    Q_ENUMS(LayoutType)
    LayoutType = LayoutType
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        PyDMPrimitiveWidget.__init__(self)
        self._template_filename = ""
        self._count_shown_in_designer = 1
        self._data_source = ""
        self._data = []
        self._cached_template = None
        self._layout_type = LayoutType.Vertical
        self.app = QApplication.instance()
        self.rebuild()
    
    @Property(LayoutType)
    def layoutType(self):
        """
        The layout type to use.

        Returns
        -------
        LayoutType
        """
        return self._layout_type

    @layoutType.setter
    def layoutType(self, new_type):
        """
        The layout type to use.
        Options are:
        - **Vertical**: Instances of the template are laid out vertically, in rows.
        - **Horizontal**: Instances of the template are laid out horizontally, in columns.
        - **Flow**: Instances of the template are laid out horizontally until they reach the edge of the template, at which point they "wrap" into a new row.

        Parameters
        ----------
        new_type : LayoutType
        """
        if new_type != self._layout_type:
            self._layout_type = new_type
            self.rebuild()
    
    @Property(int)
    def countShownInDesigner(self):
        """
        The number of instances to show in Qt Designer.  This property has no
        effect outside of Designer.
        
        Returns
        -------
        int
        """
        return self._count_shown_in_designer
    
    @countShownInDesigner.setter
    def countShownInDesigner(self, new_count):
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
    
    @Property(str)
    def templateFilename(self):
        """
        The path to the .ui file to use as a template.
        
        Returns
        -------
        str
        """
        return self._template_filename
    
    @templateFilename.setter
    def templateFilename(self, new_filename):
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
    
    @Property(str)
    def dataSource(self):
        """
        The path to the JSON file to fill in each instance of the template.
        
        Returns
        -------
        str
        """
        return self._data_source
    
    @dataSource.setter
    def dataSource(self, data_source):
        """
        Sets the path to the JSON file to fill in each instance of the template.
        
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
                try:
                    # Expand user (~ or ~user) and environment variables.
                    fname = os.path.expanduser(os.path.expandvars(self._data_source))
                    if is_pydm_app():
                        # If we're running this inside the PyDM app, we can
                        # make sure the path is relative to the currently loaded
                        # display (.ui or .py file).
                        fname = self.app.get_path(fname)
                    with open(fname) as f:
                        self.data = json.load(f)
                except IOError as e:
                    self.data = []
            else:
                self.clear()
        
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
        # Expand user (~ or ~user) and environment variables.
        fname = os.path.expanduser(os.path.expandvars(self.templateFilename))
        if is_pydm_app():
            if not self._cached_template:
                self._cached_template = self.app.open_template(fname)
            return self.app.widget_from_template(self._cached_template, variables)
        else:
            try:
                f = macro.substitute_in_file(fname, variables)
                return uic.loadUi(f)
            except Exception as e:
                logger.exception("Exception while opening template file.")
                return None
       
    def rebuild(self):
        """ Clear out all existing widgets, and populate the list using the
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
            l = layout_class(self)
            self.setLayout(l)
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
        self.setUpdatesEnabled(True)
        pydm.data_plugins.establish_queued_connections()
    
    def clear(self):
        """ Clear out any existing instances of the template inside
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

    