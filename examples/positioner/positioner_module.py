import epics
import cams
import time
from qtpy.QtCore import Slot
from os import path
from pydm import Display


class Positioner(Display):
    def __init__(self, parent=None, args=None):
        super().__init__(parent=parent, args=args)
        self.moving = False
        self.ui.pushButton.clicked.connect(self.move_motors)
        self.motor1pv = epics.PV("MOTOR:1:VAL")
        self.motor2pv = epics.PV("MOTOR:2:VAL")
        self.motor3pv = epics.PV("MOTOR:3:VAL")
        self.motor_pvs = (self.motor1pv, self.motor2pv, self.motor3pv)
        self.ui.xPosTextEntry.textChanged.connect(self.desired_position_changed)
        self.ui.yPosTextEntry.textChanged.connect(self.desired_position_changed)
        self.ui.zPosTextEntry.textChanged.connect(self.desired_position_changed)

    @property
    def display_manager_window(self):
        return self.window()

    @Slot()
    def move_motors(self):
        if self.moving:
            return

        self.moving = True
        self.ui.pushButton.setEnabled(False)
        self.display_manager_window.statusBar().showMessage("Moving motors...")
        self.motor1pv.put(self.m1des)
        self.motor2pv.put(self.m2des)
        self.motor3pv.put(self.m3des)

        waiting = True
        while waiting:
            time.sleep(0.001)
            waiting = not all([pv.put_complete for pv in self.motor_pvs])
        self.display_manager_window.statusBar().showMessage("Motor move complete.", 2000)
        self.ui.pushButton.setEnabled(True)
        self.moving = False

    @Slot(str)
    def desired_position_changed(self):
        x = self.ui.xPosTextEntry.text()
        y = self.ui.yPosTextEntry.text()
        theta = self.ui.zPosTextEntry.text()
        try:
            x = float(x)
            y = float(y)
            theta = float(theta)
        except ValueError:
            self.ui.pushButton.setEnabled(False)
            self.display_manager_window.statusBar().showMessage(
                "Cannot calculate new position, desired position is invalid."
            )
            return

        self.display_manager_window.statusBar().showMessage("Calculating new position...", 1000)
        (self.m1des, self.m2des, self.m3des, valid) = cams.real2cams((x, y, theta))
        self.ui.motor1DesLabel.setText("%.3f" % self.m1des)
        self.ui.motor2DesLabel.setText("%.3f" % self.m2des)
        self.ui.motor3DesLabel.setText("%.3f" % self.m3des)
        self.ui.pushButton.setEnabled(valid)

    def ui_filename(self):
        return "positioner-widget.ui"

    def ui_filepath(self):
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())


intelclass = Positioner
