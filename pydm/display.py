import functools
import imp
import six
import inspect
import logging
import os
import sys
import uuid
import warnings
from os import path
from string import Template

from qtpy import uic
from qtpy.QtWidgets import QWidget, QApplication

from .utilities import macro, is_pydm_app
from .utilities.stylesheet import merge_widget_stylesheet


class ScreenTarget:
    NEW_PROCESS = 0
    DIALOG = 1


logger = logging.getLogger(__file__)


def load_file(file, macros=None, args=None, target=ScreenTarget.NEW_PROCESS):
    """
    Load .ui or .py file, perform macro substitution, then return the resulting
    QWidget.
    If target is specified, it will properly display the display file.

    Parameters
    ----------
    file : str
        The path to a .ui file to load
    macros : dict, optional
        A dictionary of macro variables to supply to the
        loaded display subclass.
    args : list, optional
        A list of command-line arguments to pass to the
        loaded display subclass.
    target : int
        One of the ScreenTarget targets. PROCESS is only available when used
        with PyDM Application for now.

    Returns
    -------
    pydm.Display
    """
    if not is_pydm_app() and target == ScreenTarget.NEW_PROCESS:
        logger.warning('New Process is only valid with PyDM Application. ' +
                       'Falling back to ScreenTarget.DIALOG.')
        target = ScreenTarget.DIALOG

    if target == ScreenTarget.NEW_PROCESS:
        # Invoke PyDM to open a new process here.
        app = QApplication.instance()
        app.new_pydm_process(file, macros=macros, command_line_args=args)
        return None

    _, extension = os.path.splitext(file)
    loader = _extension_to_loader.get(extension, load_py_file)
    logger.debug("Loading %s file by way of %s...", file, loader.__name__)
    w = loader(file, args=args, macros=macros)
    if target == ScreenTarget.DIALOG:
        w.show()
    return w


def _load_ui_into_display(uifile, display):
    klass, _ = uic.loadUiType(uifile)

    # Python 2.7 compatibility. More info at the following links:
    # https://github.com/universe-proton/universe-topology/issues/3
    # https://stackoverflow.com/questions/3296993/python-how-to-call-unbound-method-with-other-type-parameter
    retranslateUi = six.get_unbound_function(klass.retranslateUi)
    setupUi = six.get_unbound_function(klass.setupUi)

    # Add retranslateUi to Display class
    display.retranslateUi = functools.partial(retranslateUi, display)
    setupUi(display, display)

    display.ui = display


def load_ui_file(uifile, macros=None, args=None):
    """
    Load a .ui file, perform macro substitution, then return the resulting QWidget.

    This is an internal method, users will usually want to use `open_file` instead.

    Parameters
    ----------
    uifile : str
        The path to a .ui file to load.
    macros : dict, optional
        A dictionary of macro variables to supply to the file
        to be opened.
    args : list, optional
        This is ignored for UI files.

    Returns
    -------
    QWidget
    """

    d = Display(macros=macros)
    merge_widget_stylesheet(d)

    if macros:
        f = macro.substitute_in_file(uifile, macros)
    else:
        f = uifile

    d._loaded_file = uifile
    _load_ui_into_display(f, d)

    return d


def load_adl_file(filename, macros=None, args=None):
    """
    Load an MEDM ADL display with adl2pydm.

    Parameters
    ----------
    filename : str
        The ADL file path.

    macros : dict, optional
        A dictionary of macro variables to supply to the loaded display
        subclass.

    args : any, optional
        Ignored for load_adl_file.
    """
    try:
        import adl2pydm
        from adl2pydm import adl_parser
        from adl2pydm import output_handler
    except ImportError:
        raise RuntimeError("Sorry, adl2pydm is not installed.")

    screen = adl_parser.MedmMainWidget(filename)
    buf = screen.getAdlLines(filename)
    screen.parseAdlBuffer(buf)

    writer = output_handler.Widget2Pydm()
    writer.write_ui(screen, None)
    ui_contents = writer.writer.generate_ui_contents()

    d = Display(macros=macros)
    merge_widget_stylesheet(d)
    d._loaded_file = filename

    fp = macro.replace_macros_in_template(Template(ui_contents), macros or {})
    _load_ui_into_display(fp, d)
    fp.close()
    return d


def load_py_file(pyfile, args=None, macros=None):
    """
    Load a .py file, performs some sanity checks to try and determine
    if the file actually contains a valid PyDM Display subclass, and if
    the checks pass, create and return an instance.

    This is an internal method, users will usually want to use `open_file` instead.

    Parameters
    ----------
    pyfile : str
        The path to a .ui file to load.
    args : list, optional
        A list of command-line arguments to pass to the
        loaded display subclass.
    macros : dict, optional
        A dictionary of macro variables to supply to the
        loaded display subclass.

    Returns
    -------
    pydm.Display
    """
    # Add the intelligence module directory to the python path, so that
    # submodules can be loaded.
    # Eventually, this should go away, and intelligence modules should behave
    # as real python modules.
    module_dir = os.path.dirname(os.path.abspath(pyfile))
    if module_dir not in sys.path:
        sys.path.append(module_dir)
    temp_name = str(uuid.uuid4())

    # Now load the intelligence module.
    module = imp.load_source(temp_name, pyfile)
    if hasattr(module, 'intelclass'):
        cls = module.intelclass
        if not issubclass(cls, Display):
            raise ValueError(
                "Invalid class definition at file {}. {} does not inherit from Display. Nothing to open at this time.".format(
                    pyfile, cls.__name__))
    else:
        classes = [obj for name, obj in inspect.getmembers(module) if
                   inspect.isclass(obj) and issubclass(obj,
                                                       Display) and obj != Display]
        if len(classes) == 0:
            raise ValueError(
                "Invalid File Format. {} has no class inheriting from Display. Nothing to open at this time.".format(
                    pyfile))
        if len(classes) > 1:
            warnings.warn(
                "More than one Display class in file {}. The first occurence (in alphabetical order) will be opened: {}".format(
                    pyfile, classes[0].__name__), RuntimeWarning, stacklevel=2)
        cls = classes[0]

    try:
        # This only works in python 3 and up.
        module_params = inspect.signature(cls).parameters
    except AttributeError:
        # Works in python 2, deprecated in 3.0 and up.
        module_params = inspect.getargspec(cls.__init__).args

    # Because older versions of Display may not have the args parameter or the macros parameter, we check
    # to see if it does before trying to use them.
    kwargs = {}
    if 'args' in module_params:
        kwargs['args'] = args
    if 'macros' in module_params:
        kwargs['macros'] = macros
    instance = cls(**kwargs)
    instance._loaded_file = pyfile
    merge_widget_stylesheet(instance)
    return instance


_extension_to_loader = {
    ".ui": load_ui_file,
    ".py": load_py_file,
    ".adl": load_adl_file,
}


class Display(QWidget):
    def __init__(self, parent=None, args=None, macros=None, ui_filename=None):
        super(Display, self).__init__(parent=parent)
        self.ui = None
        self._ui_filename = ui_filename
        self._loaded_file = None
        self._args = args
        self._macros = macros
        self._previous_display = None
        self._next_display = None
        if ui_filename or self.ui_filename():
            self.load_ui(macros=macros)

    def loaded_file(self):
        return self._loaded_file

    @property
    def previous_display(self):
        return self._previous_display

    @previous_display.setter
    def previous_display(self, display):
        self._previous_display = display

    @property
    def next_display(self):
        return self._next_display

    @next_display.setter
    def next_display(self, display):
        self._next_display = display

    def navigate_back(self):
        pass

    def navigate_forward(self):
        pass

    def macros(self):
        if self._macros is None:
            return {}
        return self._macros

    def args(self):
        return self._args

    def ui_filepath(self):
        """ Returns the path to the ui file relative to the file of the class
        calling this function."""
        if not self.ui_filename():
            return None
        path_to_class = sys.modules[self.__module__].__file__
        return path.join(path.dirname(path.realpath(path_to_class)),
                         self.ui_filename())

    def ui_filename(self):
        """ Returns the name of the ui file.  In modern PyDM, it is preferable
        specify this via the ui_filename argument in Display's constructor,
        rather than reimplementing this in Display subclasses."""
        if self._ui_filename is None:
            return None
        else:
            return self._ui_filename

    def load_ui(self, macros=None):
        """ Load and parse the ui file, and make the file's widgets available
        in self.ui.  Called by the initializer."""
        if self.ui:
            return self.ui
        if self.ui_filepath() is not None and self.ui_filepath() != "":
            self._loaded_file = self.ui_filepath()
            if macros is not None:
                f = macro.substitute_in_file(self.ui_filepath(), macros)
            else:
                f = self.ui_filepath()

            _load_ui_into_display(f, self)
            merge_widget_stylesheet(self.ui)
