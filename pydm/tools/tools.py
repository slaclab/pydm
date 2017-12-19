

class ExternalTool():
    """
    PyDM base class for External Tools hook-up.
    This class offers a boilerplate for tools to be added to PyDM.
    Code available at PyDMApplication will automatically install
    the tool if available somewhere under PYDM_TOOLS_PATH or if
    explicitly installed.

    Parameters
    ----------
    icon : QIcon
        The icon to be used when rendering the menu. Use None for no Icon.
    name : str
        The tool name. This must be unique across the combination group+name.
    group : str
        The group in which this action must be inserted. This becomes a
        QMenu with the tool as an action inside.
    author : str, optional
        This information is used to list the author name at the About screen.
    use_with_widgets : bool
        Whether or not this action should be rendered at a Custom Context Menu
        for the PyDMWidgets. If `False` the tool will be available at the Main Window
        menu only and will receive as a parameter `channels` as `None` and `sender` as
        the `main_window` object.

    """

    def __init__(self, icon, name, group, author="", use_with_widgets=True):
        self.icon = icon
        self.name = name
        self.group = group
        self.author = author
        self.use_with_widgets = use_with_widgets

    def call(self, channels, sender):
        """
        This method is invoked when the tool is selected at the menu.

        Parameters
        ----------
        channels : list
            The list of channels in use at the widget.
        sender : PyDMWidget
            The PyDMWidget or Main Window that triggered the action.

        """
        raise NotImplementedError

    def to_json(self):
        """
        Serialize the information at this tool in order to make it possible
        to be added to another PyDM Application without user interference.

        Returns
        -------
        str
        """
        raise NotImplementedError

    def from_json(self, content):
        """
        Recreate the tool based on the serialized information sent as parameter.

        Parameters
        ----------
        content : str
        """
        raise NotImplementedError

    def get_info(self):
        """
        Retrieve basic information about the External Tool in a format
        that is parsed and used at the About screen.

        Returns
        -------
        dict
            Dictionary containing at least `author`, `file`, `group` and
            `name` of the External Tool.
        """

        return {
            'author': self.author,
            'file': "",
            'group': self.group,
            'name': self.name
            }
