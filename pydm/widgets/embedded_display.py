from ..PyQt.QtGui import QStackedWidget, QApplication
from ..PyQt.QtCore import Qt
from ..PyQt.QtCore import pyqtSignal, pyqtSlot, pyqtProperty

class PyDMEmbeddedDisplay(QStackedWidget):
    """
    Widget to display other pydm guis inside of the current window.
    Requires a list of filenames, either absolute paths or relative to the the
    gui this widget is in.
    """
    def __init__(self, parent=None, filenames=None, initial_display=0):
        super(PyDMEmbeddedDisplay, self).__init__(parent)
        self.app = QApplication.instance()
        self.widget_files = []
        #if filenames is not None:
        #    self.display_filenames = filenames
        #self.setCurrentIndex(initial_display)

    def update_widgets(self):
        """
        Remove defunct widgets and load new widgets.
        """
        # Block updating in designer, where only a normal QApplication exists
        if not hasattr(self.app, "open_file"):
            return
        i=0
        for i, filename in enumerate(self.display_filenames):
            user_file = str(filename)
            try:
                widget_file = self.widget_files[i]
            except IndexError:
                widget_file = None
                self.widget_files.append(None)
            if user_file != widget_file:
                new_widget = self.open_file(user_file)
                old_widget = self.widget(i)
                if old_widget is not None:
                    self.app.close_widget_connections(old_widget)
                    self.removeWidget(old_widget)
                self.app.establish_widget_connections(new_widget)
                self.insertWidget(i, new_widget)
                self.widget_files[i] = user_file
        n_widgets = i+1
        while self.count() > n_widgets:
            widget = self.widget(n_widgets)
            self.app.close_widget_connections(widget)
            self.removeWidget(widget)
        self.widget_files = self.widget_files[:i]

    def open_file(self, filename):
        """
        Opens the widget specified in filename, relative to the file that this
        widget is instantiated in, or absolute path.

        :param filename: relative or absolute filepath
        :type filename:  string
        :rtyp: QWidget
        """
        if filename[0] == "/":
            return self.app.open_file(filename)
        else:
            return self.app.open_relative(filename, self)

    def update_display_at_index(self, index, new_filename):
        """
        Change the filename of the display at index.

        :param index: index of the filename to update
        :type index:  int
        :param new_filename: path of the new file to use
        :type new_filename:  str
        """
        filenames = self.display_filenames
        filenames[index] = new_filename
        self.display_filenames = filenames

    @pyqtSlot(str)
    def add_display(self, new_filename):
        """
        Append a new filename to the list of available filenames.

        :param new_filename: path of the file to append
        :type new_filename:  str
        """
        filenames = self.display_filenames
        filenames.append(new_filename)
        self.display_filenames = filenames

    @pyqtSlot(str)
    def edit_filename(self, name):
        """
        Unload the current file and load a new file.

        :param name: path to the file to replace the current file
        :type name:  str
        """
        self.active_display_filename = name

    @pyqtProperty("QStringList", doc=
    """
    List of filenames accessible through the embedded display.
    """
    )
    def display_filenames(self):
        try:
            return self._display_filenames
        except AttributeError:
            return []

    @display_filenames.setter
    def display_filenames(self, filename_list):
        self._display_filenames = []
        for file in filename_list:
            self._display_filenames.append(file)
        self.update_widgets()

    @pyqtProperty(str, doc=
    """
    Filename of the current active display.
    """
    )
    def active_display_filename(self):
        filenames = self.display_filenames
        index = self.currentIndex()
        if 0 <= index < len(filenames):
            return filenames[index]
        return ""

    @active_display_filename.setter
    def active_display_filename(self, filename):
        if filename is not None and len(filename) > 0:
            index = self.currentIndex()
            self.update_display_at_index(index, filename)

