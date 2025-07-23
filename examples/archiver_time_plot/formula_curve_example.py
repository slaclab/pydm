from pydm import Display
from qtpy import QtCore
from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QApplication, QCheckBox, QGroupBox
from pydm.widgets import PyDMArchiverTimePlot


class FormulaCurveExample(Display):
    """
    This example demonstrates:

    1. Base PV curves: Sin and Cos from the IOC
    2. Level 1 formulas: Mathematical operations on the base PVs AND constants
       - Sum = Sin + Cos
       - Product = Sin * Cos
       - Difference = Sin - Cos
       - Constant = 1 (uses pvs={} for constants!)
    3. Level 2 formulas: Operations on the Level 1 formulas!
       - Combo1 = Sum + Product = (Sin + Cos) + (Sin * Cos)
       - Combo2 = Sum * Difference = (Sin + Cos) * (Sin - Cos)
       - Combo3 = Sum^2 - Product + Constant = (Sin + Cos)^2 - (Sin * Cos) + 1

    Key points:
     - Constants use pvs={} (empty dictionary)
     - PV-based formulas use pvs=base_pvs
     - Higher-level formulas can reference any lower-level formula OR constant
     - This creates a dependency tree where changes propagate automatically

    This shows how you can build complex hierarchical calculations
    where formulas depend on other formulas, creating a dependency tree.
    """

    def __init__(self, parent=None, args=None, macros=None):
        super().__init__(parent=parent, args=args, macros=macros)
        self.app = QApplication.instance()
        self.setup_ui()

    def minimumSizeHint(self):
        return QtCore.QSize(1400, 700)

    def ui_filepath(self):
        return None

    def setup_ui(self):
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.plot = PyDMArchiverTimePlot(background=[255, 255, 255, 255])
        self.plot.enableCrosshair(True)

        self.control_layout = QHBoxLayout()

        self.base_group = QGroupBox("Base PV Curves")
        self.base_layout = QVBoxLayout()
        self.chkbx_sin = QCheckBox("Sin")
        self.chkbx_sin.setChecked(True)
        self.chkbx_cos = QCheckBox("Cos")
        self.chkbx_cos.setChecked(True)
        self.base_layout.addWidget(self.chkbx_sin)
        self.base_layout.addWidget(self.chkbx_cos)
        self.base_group.setLayout(self.base_layout)

        self.level1_group = QGroupBox("Level 1 Formulas")
        self.level1_layout = QVBoxLayout()
        self.chkbx_sum = QCheckBox("Sum (Sin+Cos)")
        self.chkbx_sum.setChecked(True)
        self.chkbx_product = QCheckBox("Product (Sin*Cos)")
        self.chkbx_product.setChecked(True)
        self.chkbx_difference = QCheckBox("Diff (Sin-Cos)")
        self.chkbx_difference.setChecked(True)
        self.chkbx_constant = QCheckBox("Constant (1)")
        self.chkbx_constant.setChecked(True)
        self.level1_layout.addWidget(self.chkbx_sum)
        self.level1_layout.addWidget(self.chkbx_product)
        self.level1_layout.addWidget(self.chkbx_difference)
        self.level1_layout.addWidget(self.chkbx_constant)
        self.level1_group.setLayout(self.level1_layout)

        self.level2_group = QGroupBox("Level 2 Formulas (Formula of Formulas)")
        self.level2_layout = QVBoxLayout()
        self.chkbx_combo1 = QCheckBox("Sum + Product")
        self.chkbx_combo1.setChecked(True)
        self.chkbx_combo2 = QCheckBox("Sum * Difference")
        self.chkbx_combo2.setChecked(True)
        self.chkbx_combo3 = QCheckBox("Sum^2 - Product + 1")
        self.chkbx_combo3.setChecked(True)
        self.level2_layout.addWidget(self.chkbx_combo1)
        self.level2_layout.addWidget(self.chkbx_combo2)
        self.level2_layout.addWidget(self.chkbx_combo3)
        self.level2_group.setLayout(self.level2_layout)

        self.control_layout.addWidget(self.base_group)
        self.control_layout.addWidget(self.level1_group)
        self.control_layout.addWidget(self.level2_group)
        self.control_layout.addStretch()

        self.main_layout.addLayout(self.control_layout)
        self.main_layout.addWidget(self.plot)

        # ======== STEP 1: Create base PV curves ========
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

        # ======== STEP 2: Create Level 1 formulas (based on PVs) ========
        base_pvs = {"Sin": self.sin_curve, "Cos": self.cos_curve}

        # Level 1 Formula 1: Sum
        self.sum_formula = self.plot.addFormulaChannel(
            yAxisName="Amplitude",
            formula="f://{Sin} + {Cos}",
            pvs=base_pvs,
            use_archive_data=True,
            liveData=True,
            color="green",
            plot_style="Line",
        )

        # Level 1 Formula 2: Product
        self.product_formula = self.plot.addFormulaChannel(
            yAxisName="Amplitude",
            formula="f://{Sin} * {Cos}",
            pvs=base_pvs,
            use_archive_data=True,
            liveData=True,
            color="purple",
            plot_style="Line",
        )

        # Level 1 Formula 3: Difference
        self.difference_formula = self.plot.addFormulaChannel(
            yAxisName="Amplitude",
            formula="f://{Sin} - {Cos}",
            pvs=base_pvs,
            use_archive_data=True,
            liveData=True,
            color="orange",
            plot_style="Line",
        )

        # Level 1 Formula 4: Constant (note: empty pvs for constants!)
        self.constant_formula = self.plot.addFormulaChannel(
            yAxisName="Amplitude",
            formula="f://1",
            pvs={},  # Empty dict for constants!
            use_archive_data=True,
            liveData=True,
            color="black",
            plot_style="Line",
        )

        # ======== STEP 3: Create Level 2 formulas (formulas of formulas!) ========
        level2_pvs = {
            "Sum": self.sum_formula,
            "Product": self.product_formula,
            "Difference": self.difference_formula,
            "Constant": self.constant_formula,
        }

        # Level 2 Formula 1: Combination of Sum and Product
        self.combo1_formula = self.plot.addFormulaChannel(
            yAxisName="Amplitude",
            formula="f://{Sum} + {Product}",
            pvs=level2_pvs,
            use_archive_data=True,
            liveData=True,
            color="cyan",
            plot_style="Line",
        )

        # Level 2 Formula 2: Multiply Sum by Difference
        self.combo2_formula = self.plot.addFormulaChannel(
            yAxisName="Amplitude",
            formula="f://{Sum} * {Difference}",
            pvs=level2_pvs,
            use_archive_data=True,
            liveData=True,
            color="magenta",
            plot_style="Line",
        )

        # Level 2 Formula 3: More complex expression using the constant
        self.combo3_formula = self.plot.addFormulaChannel(
            yAxisName="Amplitude",
            formula="f://{Sum}^2 - {Product} + {Constant}",
            pvs=level2_pvs,
            use_archive_data=True,
            liveData=True,
            color="yellow",
            plot_style="Line",
        )

        self.chkbx_sin.stateChanged.connect(lambda state: self.sin_curve.setVisible(state == 2))
        self.chkbx_cos.stateChanged.connect(lambda state: self.cos_curve.setVisible(state == 2))
        self.chkbx_sum.stateChanged.connect(lambda state: self.sum_formula.setVisible(state == 2))
        self.chkbx_product.stateChanged.connect(lambda state: self.product_formula.setVisible(state == 2))
        self.chkbx_difference.stateChanged.connect(lambda state: self.difference_formula.setVisible(state == 2))
        self.chkbx_constant.stateChanged.connect(lambda state: self.constant_formula.setVisible(state == 2))
        self.chkbx_combo1.stateChanged.connect(lambda state: self.combo1_formula.setVisible(state == 2))
        self.chkbx_combo2.stateChanged.connect(lambda state: self.combo2_formula.setVisible(state == 2))
        self.chkbx_combo3.stateChanged.connect(lambda state: self.combo3_formula.setVisible(state == 2))
