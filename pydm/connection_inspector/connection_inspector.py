from qtpy.QtWidgets import (QWidget, QTableView, QAbstractItemView, QHBoxLayout,
                            QVBoxLayout, QAbstractScrollArea, QPushButton,
                            QFileDialog, QMessageBox, QLabel)
from qtpy.QtCore import Qt, QSize, Slot, QTimer
from .connection_table_model import ConnectionTableModel
from .. import data_plugins


class ConnectionInspector(QWidget):
    def __init__(self, parent=None):
        super(ConnectionInspector, self).__init__(parent, Qt.Window)
        connections = self.fetch_data()
        self.table_view = ConnectionTableView(connections, self)
        self.setLayout(QVBoxLayout(self))
        self.layout().addWidget(self.table_view)
        button_layout = QHBoxLayout()
        self.layout().addItem(button_layout)
        self.save_status_label = QLabel(self)
        button_layout.addWidget(self.save_status_label)
        button_layout.addStretch()
        self.save_button = QPushButton(self)
        self.save_button.setText("Save list to file...")
        self.save_button.clicked.connect(self.save_list_to_file)
        button_layout.addWidget(self.save_button)
        self.update_timer = QTimer(parent=self)
        self.update_timer.setInterval(1500)
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start()

    def update_data(self):
        self.table_view.model().connections = self.fetch_data()

    def fetch_data(self):
        plugins = data_plugins.plugin_modules
        return [connection
                for p in plugins.values()
                for connection in p.connections.values()
                ]

    @Slot()
    def save_list_to_file(self):
        filename, filters = QFileDialog.getSaveFileName(self,
                                                        "Save connection list",
                                                        "",
                                                        "Text Files (*.txt)")
        try:
            with open(filename, "w") as f:
                for conn in self.table_view.model().connections:
                    f.write(
                        "{p}://{a}\n".format(p=conn.protocol, a=conn.address))
            self.save_status_label.setText("File saved to {}".format(filename))
        except Exception as e:
            msgBox = QMessageBox()
            msgBox.setText("Couldn't save connection list to file.")
            msgBox.setInformativeText("Error: {}".format(str(e)))
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec_()


class ConnectionTableView(QTableView):
    def __init__(self, connections=[], parent=None):
        super(ConnectionTableView, self).__init__(parent)
        self.setSizeAdjustPolicy(
            QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(True)
        self.setModel(ConnectionTableModel(connections, self))
        self.resizeColumnsToContents()
