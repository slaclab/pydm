import warnings

warnings.warn('pydm.utilities.display_loading was deprecated in favor of pydm.display_module',
              DeprecationWarning)


def load_py_file(*args, **kwargs):
    from pydm.display_module import load_py_file
    return load_py_file(*args, **kwargs)
