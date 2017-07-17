#!/usr/bin/env python3
import sys
from pydm import Display, PyDMApplication

app = PyDMApplication(ui_file='byte.ui')
sys.exit(app.exec_())