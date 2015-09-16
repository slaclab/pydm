import sys
from pydm import PyDMApplication

if __name__ == "__main__":
  app = PyDMApplication(sys.argv)
  sys.exit(app.exec_())