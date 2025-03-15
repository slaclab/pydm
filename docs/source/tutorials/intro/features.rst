Features
========


Adding Menu Actions
-------------------

You can add actions to the default menu bar in 2 ways:

* Add any custom action to the "Actions" drop down
* Add a "save", "save as", and/or "load" function to the "File" drop down

To add to the menu bar, overload the ``menu_items()`` and ``file_menu_items()``
functions in your ``Display`` subclass. These functions should return dictionaries,
where the keys are the action names, and the values one of the following:

* A callable
* A two element tuple, where the first item is a callable and the second is a keyboard shortcut
* A dictionary corresponding to a sub menu, with the same key-value format so far described. This is only available for the "Actions" menu, not for the "File" menu

.. note::
    The only accepted keys for the "File" menu are: "save", "save_as", and "load"


An example:

.. code:: python

    from pydm import Display
    class MyDisplay(Display):

        def __init__(self, parent=None, args=None, macros=None):
            super().__init__(parent=parent, args=args, macros=macros)

        def file_menu_items(self):
            return {"save": self.save_function, "load": (self.load_function, "Ctrl+L")}

        def menu_items(self):
            return {"Action1": self.action1_function, "submenu": {"Action2": self.action2_function, "Action3": self.action3_function}}

        def save_function(self):
            # do something to save your data

        def load_function(self):
            # do something to load your data

        def action1_function(self):
            # do action 1

        def action2_function(self):
            # do action 2

        def action3_function(self):
            # do action 3