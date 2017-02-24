#!/usr/bin/env python
import sys
import argparse
from pydm import PyDMApplication

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Python Display Manager")
  parser.add_argument('displayfile', help='A PyDM file to display.  Can be either a Qt .ui file, or a Python file.', nargs='?', default=None)
  parser.add_argument('display_args', help='Arguments to be passed to the PyDM client application (which is a QApplication subclass).', nargs=argparse.REMAINDER)
  pydm_args = parser.parse_args()
  app = PyDMApplication(ui_file=pydm_args.displayfile, command_line_args=pydm_args.display_args)
  sys.exit(app.exec_())