import os
import sys
import imp
import uuid
import inspect
import warnings
from ..display_module import Display
from qtpy import uic
from . import macro

def load_ui_file(uifile, macros=None):
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

    Returns
    -------
    QWidget
    """
    if macros is not None and len(macros) > 0:
        f = macro.substitute_in_file(uifile, macros)
    else:
        f = uifile
    return uic.loadUi(f)

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
    # Add the intelligence module directory to the python path, so that submodules can be loaded.    Eventually, this should go away, and intelligence modules should behave as real python modules.
    module_dir = os.path.dirname(os.path.abspath(pyfile))
    sys.path.append(module_dir)
    temp_name = str(uuid.uuid4())

    # Now load the intelligence module.
    module = imp.load_source(temp_name, pyfile)
    if hasattr(module, 'intelclass'):
        cls = module.intelclass
        if not issubclass(cls, Display):
            raise ValueError("Invalid class definition at file {}. {} does not inherit from Display. Nothing to open at this time.".format(pyfile, cls.__name__))
    else:
        classes = [obj for name, obj in inspect.getmembers(module) if inspect.isclass(obj) and issubclass(obj, Display) and obj != Display]
        if len(classes) == 0:
            raise ValueError("Invalid File Format. {} has no class inheriting from Display. Nothing to open at this time.".format(pyfile))
        if len(classes) > 1:
            warnings.warn("More than one Display class in file {}. The first occurence (in alphabetical order) will be opened: {}".format(pyfile, classes[0].__name__), RuntimeWarning, stacklevel=2)
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
    return cls(**kwargs)