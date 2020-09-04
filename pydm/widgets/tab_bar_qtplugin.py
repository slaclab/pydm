from .qtplugin_base import PyDMDesignerPlugin, WidgetCategory
from .tab_bar import PyDMTabWidget


class TabWidgetPlugin(PyDMDesignerPlugin):
    """TabWidgetPlugin needs a custom plugin so that it can
    populate itself with an initial tab."""
    TabClass = PyDMTabWidget

    def __init__(self, extensions=None):
        super(TabWidgetPlugin, self).__init__(self.TabClass,
                                              group=WidgetCategory.CONTAINER,
                                              extensions=extensions)

    def domXml(self):
        """
        XML Description of the widget's properties.
        """
        return ("<widget class=\"{0}\" name=\"{0}\">\n"
                " <property name=\"toolTip\" >\n"
                "  <string>{1}</string>\n"
                " </property>\n"
                " <property name=\"whatsThis\" >\n"
                "  <string>{2}</string>\n"
                " </property>\n"
                "<property name=\"alarmChannels\">\n"
                "<stringlist>\n"
                "  <string></string>\n"
                "</stringlist>\n"
                "</property>\n"
                "<widget class=\"QWidget\" name=\"tab\">\n"
                " <attribute name=\"title\">\n"
                "  <string>Page 1</string>\n"
                " </attribute>\n"
                "</widget>\n"
                "</widget>"
        ).format(self.name(), self.toolTip(), self.whatsThis())
