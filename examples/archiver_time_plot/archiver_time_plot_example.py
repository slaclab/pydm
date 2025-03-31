from pydm import Display

from qtpy import QtCore
from qtpy.QtWidgets import QHBoxLayout, QApplication, QCheckBox
from pydm.widgets import PyDMArchiverTimePlot


class archiver_time_plot_example(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super().__init__(parent=parent, args=args, macros=macros)
        self.app = QApplication.instance()
        self.setup_ui()

    def minimumSizeHint(self):
        return QtCore.QSize(100, 100)

    def ui_filepath(self):
        return None

    def setup_ui(self):
        self.main_layout = QHBoxLayout()
        self.setLayout(self.main_layout)
        self.plot_live = PyDMArchiverTimePlot(background=[255, 255, 255, 255])
        self.plot_archived = PyDMArchiverTimePlot(background=[255, 255, 255, 255])
        self.plot_live.enableCrosshair(True)
        self.plot_archived.enableCrosshair(True)
        self.chkbx_live = QCheckBox()
        self.chkbx_live.setChecked(True)
        self.chkbx_archived = QCheckBox()
        self.chkbx_archived.setChecked(True)
        self.main_layout.addWidget(self.chkbx_live)
        self.main_layout.addWidget(self.plot_live)
        self.main_layout.addWidget(self.plot_archived)
        self.main_layout.addWidget(self.chkbx_archived)

        curve_live = self.plot_live.addYChannel(
            y_channel="ca://XCOR:LI29:302:IACT",
            name="name",
            color="red",
            yAxisName="Axis",
            useArchiveData=True,
            liveData=True,
        )

        curve_archived = self.plot_archived.addYChannel(
            y_channel="ca://XCOR:LI28:302:IACT",
            name="name",
            color="blue",
            yAxisName="Axis",
            useArchiveData=True,
            liveData=False,
        )

        self.chkbx_live.stateChanged.connect(lambda x: self.set_live(curve_live, x))
        self.chkbx_archived.stateChanged.connect(lambda x: self.set_live(curve_archived, x))

    @staticmethod
    def set_live(curve, live):
        curve.liveData = live
