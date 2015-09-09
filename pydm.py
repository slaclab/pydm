import sys
from pydm import PyDMApplication
from PyQt4.QtGui import QMainWindow
from PyQt4 import uic
import epics

if __name__ == "__main__":
  app = PyDMApplication(sys.argv)
  app.main_window.show()
  app.start_connections()
  sys.exit(app.exec_())