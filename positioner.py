import sys, time
from pydm import PyDMApplication
from positioner_ui import Ui_MainWindow
from PyQt4.QtGui import QMainWindow
from PyQt4.QtCore import pyqtSlot, pyqtSignal, QString
import epics
import cams

class PositionerWindow(QMainWindow):
	def __init__(self, parent=None):
		super(PositionerWindow, self).__init__(parent)
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)
		self.moving = False
		self.ui.pushButton.clicked.connect(self.move_motors)
		self.motor1pv = epics.PV("MOTOR:1:VAL")
		self.motor2pv = epics.PV("MOTOR:2:VAL")
		self.motor3pv = epics.PV("MOTOR:3:VAL")
		self.motor_pvs = (self.motor1pv, self.motor2pv, self.motor3pv)
		self.ui.xPosTextEntry.textChanged.connect(self.desired_position_changed)
		self.ui.yPosTextEntry.textChanged.connect(self.desired_position_changed)
		self.ui.zPosTextEntry.textChanged.connect(self.desired_position_changed)
	
	@pyqtSlot()
	def move_motors(self):
		if self.moving:
			return
		
		self.moving = True
		self.ui.pushButton.setEnabled(False)
		self.statusBar().showMessage("Moving motors...")
		self.motor1pv.put(self.m1des)
		self.motor2pv.put(self.m2des)
		self.motor3pv.put(self.m3des)
		
		waiting = True
		while waiting:
			time.sleep(0.001)
			waiting = not all([pv.put_complete for pv in self.motor_pvs])
		self.statusBar().showMessage("Motor move complete.", 2000)
		self.ui.pushButton.setEnabled(True)
		self.moving = False
		
		
	@pyqtSlot(QString)
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
			self.statusBar().showMessage("Cannot calculate new position, desired position is invalid.")
			return
			
		self.statusBar().showMessage("Calculating new position...", 1000)
		(self.m1des, self.m2des, self.m3des, valid) = cams.real2cams((x,y,theta))
		self.ui.motor1DesLabel.setText('%.3f' % self.m1des)
		self.ui.motor2DesLabel.setText('%.3f' % self.m2des)
		self.ui.motor3DesLabel.setText('%.3f' % self.m3des)
		self.ui.pushButton.setEnabled(valid)
		
class PositionerApplication(PyDMApplication):
	def __init__(self, args):
		super(PositionerApplication, self).__init__(args)
	
	

if __name__ == "__main__":
	app = PositionerApplication(sys.argv)
	window = PositionerWindow()
	window.show()
	app.start_connections()
	sys.exit(app.exec_())
