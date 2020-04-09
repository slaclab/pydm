import warnings

warnings.warn('pydm.utilities.display_loading was deprecated in favor of pydm.display',
              DeprecationWarning)


def load_py_file(*args, **kwargs):
    from pydm.display import load_py_file
    return load_py_file(*args, **kwargs)
