import sys
import functools
from qtpy import QtWidgets
from pydm import exception


class Screen(QtWidgets.QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_ui()

    def setup_ui(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.btn_install = QtWidgets.QPushButton(self)
        self.btn_install.setText("Install Handler")
        self.btn_install.clicked.connect(functools.partial(self.setup_handler, True))

        self.btn_uninstall = QtWidgets.QPushButton(self)
        self.btn_uninstall.setText("Uninstall Handler")
        self.btn_uninstall.clicked.connect(functools.partial(self.setup_handler, False))

        self.btn_raise = QtWidgets.QPushButton(self)
        self.btn_raise.setText("Raise Exception")
        self.btn_raise.clicked.connect(self.raise_exception)

        self.layout().addWidget(self.btn_install)
        self.layout().addWidget(self.btn_uninstall)
        self.layout().addWidget(self.btn_raise)

    def setup_handler(self, install=True):
        if install:
            exception.install(use_default_handler=True)
        else:
            exception.uninstall()

    def raise_exception(self):
        raise Exception("This is an exception being raised...")


def main():
    app = QtWidgets.QApplication(sys.argv)
    screen = Screen()
    screen.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
