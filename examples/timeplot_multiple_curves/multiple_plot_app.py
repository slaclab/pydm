#!/usr/bin/env python3.4
import sys
from os import path
from pydm import PyDMApplication
#from pydm.PyQt import uic
#from pydm.PyQt.QtGui import QWidget
from pydm import Display

# Display Class -----------------------------------------------------------------
class PlotControl(Display):
  def __init__(self, parent=None, args=None):
    super(PlotControl, self).__init__(parent=parent, args=None)
    self.multiplePlot.addYChannel('ca://EX:FUNC2', '#9304FE')	# Add a new curve with defined color

  def ui_filename(self):
    return 'plot.ui'
    
  def ui_filepath(self):
    return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())

intelclass = PlotControl

# Main --------------------------------------------------------------------------
def main():
  app = PyDMApplication(ui_file="multiple_plot_app.py")
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()