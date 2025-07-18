from pydm import Display
from qtpy import QtCore
from qtpy.QtWidgets import QVBoxLayout, QHBoxLayout, QCheckBox, QApplication
from pydm.widgets import PyDMArchiverTimePlot


class SimpleFormulaExample(Display):
    """
    Simple example showing:
    1. Two base PV curves (Sin and Cos)
    2. One formula that adds them together (Sum = Sin + Cos)

    This demonstrates the basic concept without the complexity.
    """

    def __init__(self, parent=None, args=None, macros=None):
        super().__init__(parent=parent, args=args, macros=macros)
        self.app = QApplication.instance()
        self.setup_ui()

    def minimumSizeHint(self):
        return QtCore.QSize(800, 600)

    def ui_filepath(self):
        return None

    def setup_ui(self):
        # Main layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Create the plot
        self.plot = PyDMArchiverTimePlot(background=[255, 255, 255, 255])

        # Simple controls
        self.control_layout = QHBoxLayout()
        self.chkbx_sin = QCheckBox("Sin (red)")
        self.chkbx_sin.setChecked(True)
        self.chkbx_cos = QCheckBox("Cos (blue)")
        self.chkbx_cos.setChecked(True)
        self.chkbx_sum = QCheckBox("Sum = Sin + Cos (green)")
        self.chkbx_sum.setChecked(True)

        self.control_layout.addWidget(self.chkbx_sin)
        self.control_layout.addWidget(self.chkbx_cos)
        self.control_layout.addWidget(self.chkbx_sum)
        self.control_layout.addStretch()

        # Add to main layout
        self.main_layout.addLayout(self.control_layout)
        self.main_layout.addWidget(self.plot)

        # Create base PV curves
        self.sin_curve = self.plot.addYChannel(
            y_channel="ca://MTEST:SinVal",
            name="Sin",
            color="red",
            yAxisName="Amplitude",
            useArchiveData=True,
            liveData=True,
        )

        self.cos_curve = self.plot.addYChannel(
            y_channel="ca://MTEST:CosVal",
            name="Cos",
            color="blue",
            yAxisName="Amplitude",
            useArchiveData=True,
            liveData=True,
        )

        # Create a formula that adds the two PVs
        base_pvs = {"Sin": self.sin_curve, "Cos": self.cos_curve}

        self.sum_formula = self.plot.addFormulaChannel(
            yAxisName="Amplitude",
            formula="f://{Sin} + {Cos}",
            pvs=base_pvs,
            use_archive_data=True,
            liveData=True,
            color="green",
            plot_style="Line",
        )

        # Connect checkboxes to show/hide curves
        self.chkbx_sin.stateChanged.connect(lambda state: self.sin_curve.setVisible(state == 2))
        self.chkbx_cos.stateChanged.connect(lambda state: self.cos_curve.setVisible(state == 2))
        self.chkbx_sum.stateChanged.connect(lambda state: self.sum_formula.setVisible(state == 2))
