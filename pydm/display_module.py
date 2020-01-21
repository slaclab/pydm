import warnings
warnings.warn("The display_module was renamed to display."
              "Please modify your code to reflect this change.",
              DeprecationWarning, stacklevel=2)

__all__ = ['Display', 'ScreenTarget',
           'load_file', 'load_py_file', 'load_ui_file']

from pydm.display import (Display, ScreenTarget,
                          load_file, load_py_file, load_ui_file)
