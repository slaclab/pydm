from qtpy import uic
from qtpy.QtWidgets import QWidget, QApplication, QTableWidgetItem
from qtpy.QtCore import Qt, PYQT_VERSION_STR, qVersion
from .about_ui import Ui_Form
from numpy import __version__ as numpyver
from pyqtgraph import __version__ as pyqtgraphver
import pydm
import sys
from os import path
import inspect


class AboutWindow(QWidget):
    def __init__(self, parent=None):
        super(AboutWindow, self).__init__(parent, Qt.Window)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.pydmVersionLabel.setText(str(self.ui.pydmVersionLabel.text()).format(version=pydm.__version__))
        pyver = ".".join([str(v) for v in sys.version_info[0:3]])
        self.ui.modulesVersionLabel.setText(str(self.ui.modulesVersionLabel.text()).format(pyver=pyver,
                                                                                           numpyver=numpyver,
                                                                                           pyqtgraphver=pyqtgraphver,
                                                                                           pyqtver=PYQT_VERSION_STR,
                                                                                           qtver=qVersion()))
        self.populate_external_tools_list()
        self.populate_plugin_list()
        self.populate_contributor_list()

    def populate_external_tools_list(self):
        col_labels = ["Name", "Group", "Author", "File"]
        self.ui.externalToolsTableWidget.setColumnCount(len(col_labels))
        self.ui.externalToolsTableWidget.setHorizontalHeaderLabels(col_labels)
        self.ui.externalToolsTableWidget.horizontalHeader().setStretchLastSection(True)
        self.ui.externalToolsTableWidget.verticalHeader().setVisible(False)
        self.add_tools_to_list(pydm.tools.ext_tools)

    def add_tools_to_list(self, tools):
        for (name, tool) in tools.items():
            if isinstance(tool, dict):
                self.add_tools_to_list(tool)
            else:
                tool_info = tool.get_info()
                name_item = QTableWidgetItem(tool_info.get("name","None"))
                group_item = QTableWidgetItem(tool_info.get("group","None"))
                author_item = QTableWidgetItem(tool_info.get("author","None"))
                file_item = QTableWidgetItem(tool_info.get("file","None"))
                new_row = self.ui.externalToolsTableWidget.rowCount()
                self.ui.externalToolsTableWidget.insertRow(new_row)
                self.ui.externalToolsTableWidget.setItem(new_row, 0, name_item)
                self.ui.externalToolsTableWidget.setItem(new_row, 1, group_item)
                self.ui.externalToolsTableWidget.setItem(new_row, 2, author_item)
                self.ui.externalToolsTableWidget.setItem(new_row, 3, file_item)

    def populate_plugin_list(self):
        col_labels = ["Protocol", "File"]
        self.ui.dataPluginsTableWidget.setColumnCount(len(col_labels))
        self.ui.dataPluginsTableWidget.setHorizontalHeaderLabels(col_labels)
        self.ui.dataPluginsTableWidget.horizontalHeader().setStretchLastSection(True)
        self.ui.dataPluginsTableWidget.verticalHeader().setVisible(False)
        for (protocol, plugin) in pydm.data_plugins.plugin_modules.items():
            protocol_item = QTableWidgetItem(protocol)
            file_item = QTableWidgetItem(inspect.getfile(plugin.__class__))
            new_row = self.ui.dataPluginsTableWidget.rowCount()
            self.ui.dataPluginsTableWidget.insertRow(new_row)
            self.ui.dataPluginsTableWidget.setItem(new_row, 0, protocol_item)
            self.ui.dataPluginsTableWidget.setItem(new_row, 1, file_item)

    def populate_contributor_list(self):
        contrib_file = path.join(path.dirname(path.realpath(__file__)), "contributors.txt")
        with open(contrib_file) as f:
            for line in f:
                self.ui.contributorsListWidget.addItem(str(line).strip())
