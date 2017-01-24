#!/usr/bin/env python
import sys
import argparse
from pydm.client.application import PyDMApplication
from pydm.data_server import PyDMDataServer

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Python Display Manager", epilog="All other arguments are forwarded to a QApplication instance.")
  parser.add_argument('-c', '--client', dest='servername', help='Launch a display which is a client of the pydm server with name servername')
  parser.add_argument('displayfile', help='A PyDM file to display.  Can be either a Qt .ui file, or a Python file.', nargs='?', default=None)
  pydm_args = parser.parse_args()
  if pydm_args.servername:
    app = PyDMApplication(pydm_args.servername, ui_file=pydm_args.displayfile)
  else:
    app = PyDMDataServer(ui_file=pydm_args.displayfile)
  sys.exit(app.exec_())