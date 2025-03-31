from pydm import Display

from qtpy import QtCore
from qtpy.QtWidgets import QHBoxLayout, QApplication, QCheckBox, QLineEdit, QPushButton
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
        self.plot = PyDMArchiverTimePlot(background=[255, 255, 255, 255])
        self.chkbx_live = QCheckBox()
        self.chkbx_live.setChecked(True)
        self.formula_box = QLineEdit(self)
        self.formula_box.setText("f://{A}")
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.set_formula)
        self.main_layout.addWidget(self.formula_box)
        self.main_layout.addWidget(self.ok_button)
        self.main_layout.addWidget(self.chkbx_live)
        self.main_layout.addWidget(self.plot)
        self.curve = self.plot.addYChannel(
            y_channel="ca://MTEST:Float",
            name="name",
            color="red",
            yAxisName="Axis",
            useArchiveData=True,
            liveData=True,
        )

        pvdict = dict()
        pvdict["A"] = self.curve
        self.formula_curve = self.plot.addFormulaChannel(
            formula=r"f://2*{A}",
            pvs=pvdict,
            yAxisName="Axis",
            color="green",
            useArchiveData=True,
            liveData=True,
        )
        self.chkbx_live.stateChanged.connect(lambda x: self.set_live(self.curve, self.formula_curve, x))

    @staticmethod
    def set_live(curve, formula_curve, live):
        curve.liveData = live
        formula_curve.liveData = live

    def set_formula(self):
        print("assuming formula is valid, attempting to use formula")
        self.formula_curve.formula = self.formula_box.text()
        self.formula_curve.redrawCurve()
