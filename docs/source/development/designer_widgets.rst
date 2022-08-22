Designer Widgets
================

Widgets in PyDM itself
----------------------

If you are developing a new widget for PyDM, please make it compatible with
Qt designer by editing ``pydm/widgets/qtplugins.py``.

For example, if you create a widget called ``MyWidget`` and have it in
``pydm.widgets.my_widget``, you should add the following lines in
``qtplugins.py``.

.. code:: python

    from .my_widget import MyWidget

    # And further down in the file where the "NOTE" is:

    MyWidgetPlugin = qtplugin_factory(
        MyWidget,
        group=WidgetCategory.MISC,
        extensions=BASE_EXTENSIONS,
        icon=ifont.icon("calendar-alt"),
    )


The ``group`` parameter may be one of the following attributes from
``WidgetCategory``.

.. autoclass:: pydm.widgets.qtplugin_base.WidgetCategory
   :members:

For most widgets, ``extensions`` should remain as the suggested
``BASE_EXTENSIONS``.  Advanced users who wish to further customize the Qt
Designer experience will need to poke around in the PyDM internals to figure it
out.

The ``icon`` can be customized using the PyDM-vendored fontawesome library.
The available options can be found in ``fontawesome-charmap.json``, and a quick
Google search should help you find an icon that will fit your scenario.

.. autofunction:: pydm.widgets.qtplugin_base.qtplugin_factory


Widgets in external packages
----------------------------

If you develop a package which has Qt Designer-compatible widgets, you can use
PyDM's built-in support for adding widgets to the designer via entrypoints.

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

    class MyWidgetClass(QtWidgets.QWidget):
        """This is your custom widget."""
        # Add this to customize where/how the widget shows up in the designer:
        _qt_designer_ = {
            "group": "My Widget Category",
            "is_container": False,
            "extensions": [],
            "icon": None,  # QtGui.QIcon(...)
        }


The ``_qt_designer_`` dictionary is passed directly to ``qtplugin_factory``.
