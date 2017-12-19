from pydm.tools import ExternalTool
from pydm.utilities.iconfont import IconFont

class DummyTool(ExternalTool):
    def __init__(self):
        icon = IconFont().icon("cogs")
        name = "Dummy Tool"
        group = "Example"
        use_with_widgets = False
        ExternalTool.__init__(self, icon=icon, name=name, group=group, use_with_widgets=use_with_widgets)

    def call(self, channels, sender):
        print("Called Dummy Tool from: {} with:".format(sender))
        print("Channels: ", channels)

    def to_json(self):
        return ""

    def from_json(self, content):
        print("Received from_json: ", content)
