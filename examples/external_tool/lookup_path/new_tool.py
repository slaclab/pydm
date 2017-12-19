from pydm.tools import ExternalTool
from pydm.utilities.iconfont import IconFont

class DummyTool2(ExternalTool):
    def __init__(self):
        icon = IconFont().icon("code")
        name = "Dummy Tool 2"
        group = "Example"
        use_with_widgets = False
        ExternalTool.__init__(self, icon=icon, name=name, group=group, use_with_widgets=use_with_widgets)

    def call(self, channels, sender):
        print("Called Dummy Tool 2 from: {} with:".format(sender))
        print("Channels: ", channels)

    def to_json(self):
        return ""

    def from_json(self, content):
        print("Received from_json: ", content)
