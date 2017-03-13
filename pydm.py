#!/usr/bin/env python
import sys
import argparse
from pydm import PyDMApplication
import json

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Python Display Manager")
  parser.add_argument('displayfile', help='A PyDM file to display.  Can be either a Qt .ui file, or a Python file.', nargs='?', default=None)
  parser.add_argument('--perfmon', action='store_true', help='Enable performance monitoring, and print CPU usage to the terminal.')
  parser.add_argument('-m', '--macro', help='Specify macro replacements to use, in JSON object format.  Reminder: JSON requires double quotes for strings, so you should wrap this whole argument in single quotes.  Example: -m \'{"sector": "LI25", "facility": "LCLS"}')
  parser.add_argument('display_args', help='Arguments to be passed to the PyDM client application (which is a QApplication subclass).', nargs=argparse.REMAINDER)
  pydm_args = parser.parse_args()
  macros = None
  if pydm_args.macro is not None:
    try:
      macros = json.loads(pydm_args.macro)
    except ValueError:
      raise ValueError("Could not parse macro argument as JSON.")
  app = PyDMApplication(ui_file=pydm_args.displayfile, command_line_args=pydm_args.display_args, perfmon=pydm_args.perfmon, macros=macros)
  sys.exit(app.exec_())