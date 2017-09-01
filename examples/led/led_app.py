#!/usr/bin/env python3
import sys
from pydm import PyDMApplication

app = PyDMApplication(ui_file='led.ui')
sys.exit(app.exec_())