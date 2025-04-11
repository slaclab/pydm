import platform
from qtpy.QtWidgets import (
    QWidget,
    QTableView,
    QAbstractItemView,
    QHBoxLayout,
    QVBoxLayout,
    QAbstractScrollArea,
    QPushButton,
    QApplication,
    QFileDialog,
    QMessageBox,
    QLabel,
)
from qtpy.QtCore import Qt, Slot, QTimer
from .connection_table_model import ConnectionTableModel
from pydm import data_plugins


class ConnectionInspector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        connections = self.fetch_data()
        self.table_view = ConnectionTableView(connections, self)
        self.setLayout(QVBoxLayout(self))
        self.layout().addWidget(self.table_view)
        button_layout = QHBoxLayout()
        self.layout().addItem(button_layout)
        self.save_status_label = QLabel(self)
        button_layout.addWidget(self.save_status_label)
        button_layout.setSpacing(10)
        self.save_button = QPushButton(self)
        self.save_button.setText("Save list to file...")
        self.save_button.clicked.connect(self.save_list_to_file)
        self.copy_button = QPushButton(self)
        self.copy_button.setText("Copy PVs to clipboard")
        self.copy_button.clicked.connect(self.copy_pv_list_to_clipboard)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.copy_button)
        self.update_timer = QTimer(parent=self)
        self.update_timer.setInterval(1500)
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start()

    def update_data(self):
        self.table_view.model().connections = self.fetch_data()
        self.table_view.sortByColumn(
            self.table_view.horizontalHeader().sortIndicatorSection(),
            self.table_view.horizontalHeader().sortIndicatorOrder(),
        )

    def fetch_data(self):
        plugins = data_plugins.plugin_modules
        return [
            connection
            for p in plugins.values()
            for connection in p.connections.values()
            # DISP field is connected to separately for writable channels, including it on this list is redundant
            # Local plugins have a ParseResult address, not a string, so they may not have a 'endswith' attribute
            if (not connection.address.endswith(".DISP") if hasattr(connection.address, "endswith") else True)
        ]

    @Slot()
    def save_list_to_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save connection list", "", "Text Files (*.txt)")
        try:
            if len(filename) == 0:
                # User hit Cancel
                return
            with open(filename, "w") as f:
                for conn in self.table_view.model().connections:
                    f.write("{p}://{a}\n".format(p=conn.protocol, a=conn.address))
            self.save_status_label.setText("File saved to {}".format(filename))
        except Exception as e:
            msgBox = QMessageBox()
            msgBox.setText("Couldn't save connection list to file.")
            msgBox.setInformativeText("Error: {}".format(str(e)))
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec_()

    @Slot()
    def copy_pv_list_to_clipboard(self):
        """Copy the list of PVs from the table to the clipboard"""
        pv_list = [connection.address for connection in self.table_view.model().connections]
        if len(pv_list) == 0:
            return

        pvs_to_copy = " ".join(pv_list)
        clipboard = QApplication.clipboard()
        if platform.system() == "Linux":
            # Mode Selection is only valid for X11.
            clipboard.setText(pvs_to_copy, clipboard.Selection)
        clipboard.setText(pvs_to_copy, clipboard.Clipboard)


class ConnectionTableView(QTableView):
    def __init__(self, connections=[], parent=None):
        super().__init__(parent)
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(True)
        self.setModel(ConnectionTableModel(connections, self))
        self.resizeColumnsToContents()
