import os
import json
import logging
from qtpy.QtWidgets import (QFrame, QApplication, QLabel, QVBoxLayout,
                           QHBoxLayout, QWidget, QStyle, QSizePolicy,
                           QLayout, QListWidget, QListWidgetItem)
from qtpy.QtCore import Qt, QSize, QRect, Property, QPoint, QUrl, Q_ENUMS
from qtpy import uic
from .base import PyDMPrimitiveWidget, PyDMWidget
from .embedded_display import PyDMEmbeddedDisplay
from pydm.utilities import is_qt_designer, is_pydm_app
from ..utilities import macro
logger = logging.getLogger(__name__)

def combine_macros(list_of_macros):
    macros = {}
    for l in reversed(list_of_macros):
        macros.update(l)
    return macros

class LayoutType(object):
    Vertical = 0
    Horizontal = 1
    Flow = 2

class PyDMTemplateRepeater(QListWidget, PyDMPrimitiveWidget, LayoutType):
    Q_ENUMS(LayoutType)
    WidgetType = LayoutType
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        PyDMPrimitiveWidget.__init__(self)
        self._template_filename = ""
        self._count_shown_in_designer = 1
        self._macros = ""
        self._data_source = ""
        self._data = []
        self._cached_template = None
        self.app = QApplication.instance()
        self.rebuild()
    
    @Property(int)
    def countShownInDesigner(self):
        return self._count_shown_in_designer
    
    @countShownInDesigner.setter
    def countShownInDesigner(self, new_count):
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
        return self._template_filename
    
    @templateFilename.setter
    def templateFilename(self, new_filename):
        if new_filename != self._template_filename:
            self._template_filename = new_filename
            self._cached_template = None
            if self._template_filename:
                self.rebuild()
            else:
                self.clear()
    
    @Property(str)
    def dataSource(self):
        return self._data_source
    
    @dataSource.setter
    def dataSource(self, new_filename):
        if new_filename != self._data_source:
            self._data_source = new_filename
            if self._data_source:
                self.rebuild()
            else:
                self.clear()
    
    @Property(str)
    def macros(self):
        """
        String containing macro variables to use in the template file.
        Can use either JSON or key1=val1;key2=val2 format.

        Returns
        -------
        str
        """
        if self._macros is None:
            return ""
        return self._macros

    @macros.setter
    def macros(self, new_macros):
        """
        String containing macro variables to use in the template file.
        Can use either JSON or key1=val1;key2=val2 format.

        Parameters
        ----------
        new_macros : str
        """
        self._macros = str(new_macros)
    
    def parsed_macros(self):
        """
        Dictionary containing the key value pair for each macro specified.

        Returns
        --------
        dict
        """
        return macro.parse_macro_string(self.macros)
    
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
        #Note, the order is important here, variables must be last.
        macros = [self.parsed_macros(), variables]
        # Expand user (~ or ~user) and environment variables.
        fname = os.path.expanduser(os.path.expandvars(self.templateFilename))
        if is_pydm_app():
            combined_macros = combine_macros(macros)
            if not self._cached_template:
                self._cached_template = self.app.open_template(fname)
            return self.app.widget_from_template(self._cached_template, combined_macros)
        else:
            # Build up our macros by traversing up the widget tree.
            p = self.parent()
            while p is not None:
                if isinstance(p, (PyDMEmbeddedDisplay, PyDMTemplateRepeater)):
                    macros.append(p.parsed_macros())
                p = p.parent()
            # Now that we've collected them all, we apply them in reverse order,
            # so that child variables override those defined on parents.
            combined_macros = combine_macros(macros)
            try:
                f = macro.substitute_in_file(fname, combined_macros)
                return uic.loadUi(f)
            except Exception as e:
                logger.exception("Exception while opening template file.")
                return None
       
    def rebuild(self):
        """ Clear out all existing widgets, and populate the list using the
        template file and data source."""
        self.clear()
        if not self.templateFilename:
            return
        for i, variables in enumerate(self.data()):
            if is_qt_designer() and i > self.countShownInDesigner - 1:
                break
            w = self.open_template_file(variables)
            if w is None:
                w = QLabel()
                w.setText("No Template Loaded.  Data: {}".format(variables))
            #w.setParent(self)
            item = QListWidgetItem(self)
            self.addItem(item)
            item.setSizeHint(w.minimumSizeHint())
            self.setItemWidget(item, w)
        #for i in range(self.count()):
        #    w = self.itemWidget(self.item(i))
        #    child_widgets = [w]
        #    child_widgets.extend(w.findChildren(QWidget))
        #    for child_widget in child_widgets:
        #        try:
        #            for chan in child_widget.channels():
        #                chan.connect()
        #        except AttributeError:
        #            pass

    
    def data(self):
        if not self._data:
            try:
                with open(self._data_source) as f:
                    self._data = json.load(f)
            except IOError as e:
                self._data = []
        return self._data

        

    