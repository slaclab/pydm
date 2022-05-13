Designer Widgets
================

If you develop a package which has Qt Designer-compatible widgets, you can use
PyDM's built-in support for adding widgets to the designer via entrypoints.

Configuration
-------------

Here is an example ``setup.py`` that could be used to locate a designable
widget in your own Python package:

.. code:: python

    from setuptools import setup, find_packages

    setup(
        name="my_package",
        # ... other settings will go here
        entry_points={
            "gui_scripts": ["my_package_gui=my_package.main:main"],
            "pydm.widget": [
                "MyWidgetDesigner=my_package.tool_name:MyWidgetClass",
            ],
        },
        install_requires=[],
    )


This would assume that you have the following:

1. A package named "my_package" with ``my_package/__init__.py`` and
   ``my_package/widget.py``.
2. In ``my_package/widget.py``, a ``MyWidgetClass`` that inherits from
   :class:`~QtWidgets.QWidget`.

After running ``pip install`` on the package, it should be readily available
in the Qt Designer.

The class may specify additional settings by way of this mechanism:

.. code:: python

    class MyWidgetDesigner(QtWidgets.QWidget):
        """This is your custom widget."""
        # Add this to customize where/how the widget shows up in the designer:
        _qt_designer_ = {
            "group": "My Widget Category",
            "is_container": False,
            "extensions": [],
            "icon": None,  # QtGui.QIcon(...)
        }
